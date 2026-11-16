#!/usr/bin/env python3
"""Render scan: check EVERY frame of a render for the glitches stills miss (checks inspired by
win4r/video-director's QA, MIT; this is an independent implementation).

Beat sheets sample a few frames; this reads all of them (downscaled, so it is fast and costs no tokens):
  - frame 0 / thumbnail: blank or flat opening frame
  - flashes: one frame that differs while the frames either side match (a stray frame, a blink of a layer)
  - pops: a sudden jump in change, > 3x both neighbours, that isn't a planned cut
  - empty frames: mid-film frames with nothing readable on them (no subject brighter than the ground),
    e.g. a crossfade that passes through an empty or dark frame
  - frozen stretches: nothing moves for longer than --freeze s (a designed hold, or dead air?)
  - audio: integrated loudness and true peak, silences (>= 0.4 s, 15 dB under the film's loud level and
    below -30 dBFS), the loudest 100 ms, and whether a silence comes before it
  - phone sheet: 1 frame per second at 360 px wide (can a phone viewer read it?)

Usage (project venv, from the project root):
  .venv/bin/python -I <skill>/scripts/render_scan.py VIDEO --out anim/out/scan
      [--timeline anim/src/data/timeline.json]  # planned cuts = scene starts; holds named "hold*" are allowed
      [--holds 6.8-8.6,12-14]                   # extra designed holds (seconds)
      [--freeze 1.0] [--fades 0-0.6,last-0.6]   # windows where empty frames are deliberate (fade in/out)
Writes report.md / report.json and phone_sheet.png. Exit code 1 if anything FAILs.
Every number is MEASURED from the file.
"""
import argparse, json, math, subprocess, sys
from pathlib import Path
import numpy as np

W, H = 192, 108


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out); st = j["streams"][0]; a, b = st["r_frame_rate"].split("/")
    return {"w": st["width"], "h": st["height"], "fps": float(a) / float(b), "dur": float(j["format"]["duration"])}


def frames(path, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={w}:{h}:flags=area,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32) / 255.0


def lightness(g):  # gray (0-1, sRGB-ish) -> perceptual lightness ~ cube root of linear luminance
    lin = np.where(g <= 0.04045, g / 12.92, ((g + 0.055) / 1.055) ** 2.4)
    return np.cbrt(lin)


def parse_fades(arg, dur):
    out = []
    for part in (arg or "").split(","):
        part = part.strip()
        if not part:
            continue
        if part.startswith("last-"):
            out.append((dur - float(part[5:]), dur))
        else:
            a, b = part.split("-"); out.append((float(a), float(b)))
    return out


def inside(t, rs, pad=0.0):
    return any(a - pad <= t <= b + pad for a, b in rs)


def runs(mask):
    out, start = [], None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        if not m and start is not None:
            out.append((start, i - 1)); start = None
    if start is not None:
        out.append((start, len(mask) - 1))
    return out


def audio(path):
    try:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None
    y = np.frombuffer(raw, np.float32)
    if y.size < 1600:
        return None
    hop = 1600  # 100 ms
    n = y.size // hop
    rms = np.sqrt(np.mean(y[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    loud = float(np.percentile(db, 90))
    quiet = (db < loud - 15) & (db < -30)
    sil = [(a * 0.1, (b + 1) * 0.1) for a, b in runs(quiet) if (b - a + 1) >= 4]
    peak_i = int(np.argmax(db))
    eb = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    lufs = tp = None
    for line in eb.splitlines()[::-1]:
        s = line.strip()
        if s.startswith("I:") and lufs is None:
            lufs = float(s.split()[1])
        if s.startswith("Peak:") and tp is None:
            tp = float(s.split()[1])
    return {"lufs": lufs, "true_peak": tp, "loudest_t": round(peak_i * 0.1, 2), "loudest_db": round(float(db[peak_i]), 1),
            "silences": [(round(a, 2), round(b, 2)) for a, b in sil],
            "silence_before_loudest": any(b <= peak_i * 0.1 + 0.05 and peak_i * 0.1 - b <= 4.0 for a, b in sil)}


def phone_sheet(path, dur, dest):
    times = [t + 0.5 for t in range(int(dur))] or [0]
    tiles = []
    import tempfile
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(times):
            p = Path(tmp) / f"{i:04d}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{min(t, dur - 0.05):.2f}", "-i", str(path), "-frames:v", "1",
                            "-vf", "scale=360:-2", str(p)], check=True)
            tiles.append(Image.open(p).convert("RGB"))
        cols = 6; tw, th = tiles[0].size; rows = math.ceil(len(tiles) / cols)
        sheet = Image.new("RGB", (cols * tw, rows * th), (12, 10, 14))
        for i, im in enumerate(tiles):
            sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
        sheet.save(dest)


def subject_contrast(f):
    """How far the subject stands out from the background, in either direction: light text on a dark
    frame (99.7th percentile above the median) or dark ink on a light page (0.3rd percentile below it)."""
    p03, p50, p997 = np.percentile(f, (0.3, 50, 99.7))
    return max(p997 - p50, p50 - p03)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("--out", required=True)
    ap.add_argument("--timeline"); ap.add_argument("--holds", default=""); ap.add_argument("--fades", default="0-0.5,last-0.6")
    ap.add_argument("--freeze", type=float, default=1.0)
    ap.add_argument("--no-sheet", action="store_true")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    info = probe(a.video); fps = info["fps"]; dur = info["dur"]
    g = frames(a.video, W, H); n = len(g)
    L = lightness(g)
    holds = parse_fades(a.holds.replace(" ", ""), dur) if a.holds else []
    fades = parse_fades(a.fades, dur)
    cuts = []
    if a.timeline:
        tl = json.loads(Path(a.timeline).read_text()); tfps = tl.get("fps", fps)
        if "sting" in tl:
            cuts.append(tl["sting"]["dur"] / tfps)
        # "scenes" with startFrame/beats, or the news "segments" with start, shots and plane flights
        for s in tl.get("scenes", []) + tl.get("segments", []):
            s0 = s.get("startFrame", s.get("start", 0))
            cuts.append(s0 / tfps)
            cuts += [(s0 + sh["start"]) / tfps for sh in s.get("shots", [])[1:]]
            if s.get("flight"):
                cuts += [s["flight"]["start"] / tfps, (s["flight"]["start"] + s["flight"]["dur"]) / tfps]
            for k, v in (s.get("beats") or {}).items():
                if k.lower().startswith("hold"):
                    holds.append(((s0 + v) / tfps, (s0 + v) / tfps + a.freeze * 2))
    res = {"file": str(a.video), "fps": round(fps, 3), "duration": round(dur, 2), "frames": n, "checks": []}

    def add(name, level, msg, t=None):
        res["checks"].append({"check": name, "level": level, "t": t, "msg": msg})

    # frame 0 / thumbnail
    sc0 = subject_contrast(L[0])
    if sc0 < 0.25:
        add("frame0", "WARN" if inside(0, fades) else "FAIL",
            f"opening frame is nearly empty (subject contrast {sc0:.2f}); fine only if the video opens with a deliberate fade", 0.0)
    # frame differences
    d = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2))  # d[i] = change from frame i to i+1
    for i in range(1, len(d) - 1):
        t = round((i + 1) / fps, 3)
        # flash: frame i+1 differs from both neighbours while i and i+2 match
        if i + 2 < n:
            around = float(np.abs(g[i] - g[i + 2]).mean())
            if d[i] > 0.02 and d[i + 1] > 0.02 and around < 0.25 * min(d[i], d[i + 1]):
                add("flash", "FAIL", f"single-frame flash (frame {i + 1}): the frames either side match", t)
        if d[i] > 0.012 and d[i] > 3 * d[i - 1] and d[i] > 3 * d[i + 1]:
            if any(abs(t - c) <= 1.5 / fps for c in cuts):
                continue
            add("pop", "WARN", f"sudden jump in change ({d[i]:.3f} vs {d[i-1]:.3f}/{d[i+1]:.3f}); a cut is fine if planned", t)
    # empty frames mid-film
    sc = np.array([subject_contrast(f) for f in L])
    empty = sc < 0.25
    for s, e in runs(empty):
        t0, t1 = s / fps, (e + 1) / fps
        if s == 0 and inside(t1, fades, 0.05):
            continue
        if inside(t0, fades, 0.05) and inside(t1, fades, 0.05):
            continue
        if (e - s + 1) >= 2:
            add("empty", "FAIL", f"{t1 - t0:.2f} s with nothing readable on screen (subject contrast ≤ {sc[s:e + 1].max():.2f})", round(t0, 2))
    # frozen stretches
    still = np.concatenate([[False], d < 0.0006])
    for s, e in runs(still):
        t0, t1 = (s - 1) / fps, e / fps
        if t1 - t0 >= a.freeze:
            designed = any(a0 - 0.3 <= t0 and t1 <= b0 + 0.3 for a0, b0 in holds) or any(a0 <= t0 + 0.3 and t1 <= b0 + 1.0 for a0, b0 in fades[-1:])
            add("frozen", "INFO" if designed else "WARN",
                f"{t1 - t0:.2f} s with no motion ({'designed hold' if designed else 'designed hold or dead air? Add a living element or mark it as a hold'})", round(t0, 2))
    # audio
    au = audio(a.video)
    if au:
        res["audio"] = au
        if au["lufs"] is not None and not (-15.5 <= au["lufs"] <= -12.5):
            add("loudness", "WARN", f"integrated {au['lufs']} LUFS (target -14 ±1.5)")
        if au["true_peak"] is not None and au["true_peak"] > -1.0:
            add("true_peak", "FAIL", f"true peak {au['true_peak']} dBFS (max -1)")
    else:
        add("audio", "INFO", "no audio stream")
    if not a.no_sheet:
        phone_sheet(a.video, dur, out / "phone_sheet.png")
    fails = sum(c["level"] == "FAIL" for c in res["checks"]); warns = sum(c["level"] == "WARN" for c in res["checks"])
    res["summary"] = {"fail": fails, "warn": warns}
    (out / "report.json").write_text(json.dumps(res, indent=1))
    lines = [f"# Render scan: {Path(a.video).name}", f"{n} frames at {fps:.2f} fps, {dur:.2f} s. All numbers measured.", ""]
    for c in res["checks"]:
        lines.append(f"- **{c['level']}** {c['check']}" + (f" @ {c['t']:.2f}s" if c["t"] is not None else "") + f": {c['msg']}")
    if au:
        lines += ["", f"Audio: {au['lufs']} LUFS, true peak {au['true_peak']} dBFS, loudest 100 ms at {au['loudest_t']} s "
                  f"({au['loudest_db']} dBFS), silences {au['silences'] or 'none'}, silence before the loudest moment: "
                  f"{'yes' if au['silence_before_loudest'] else 'no'}"]
    lines += ["", f"**{fails} FAIL, {warns} WARN**" + ("" if a.no_sheet else f" · phone sheet: {out / 'phone_sheet.png'}")]
    (out / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
