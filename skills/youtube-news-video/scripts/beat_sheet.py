#!/usr/bin/env python3
"""Beat contact sheets: one labelled still shortly after every beat in timeline.json
(review method adapted from stazdev/cutaway, MIT).

You can't watch a video, only frames. This pulls the exact frames where something is supposed
to happen, so every beat gets checked instead of a random sample.

Usage (project venv, from the project root):
  .venv/bin/python -I <skill>/scripts/beat_sheet.py VIDEO anim/src/data/timeline.json --out anim/out/beats
       [--after 0.3] [--cols 4] [--width 480] [--every 0.2 --from 41.0 --to 43.0] [--scenes S04,S07]

Writes anim/out/beats/beats_01.png (and with --keep, full-size tiles in <out>/tiles/)
  , beats_02.png ... (max 16 tiles per sheet) and beats.json
(tile -> scene, beat, time). With --every/--from/--to it samples a range instead (transitions).
timeline.json: {"fps": 30, "scenes": [{"id": "S01", "startFrame": 0, "durationInFrames": 300,
                "beats": {"title": 45, "...": 120}}]}  (beat frames are local to the scene).
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def video_info(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def grab(video, t, dst, width):
    # one seek per timestamp: exact frames, no duplicated fills (fps/select filters repeat frames across gaps)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                    "-vf", f"scale={width}:-2", str(dst)], check=True)


def font(size):
    for f in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def sheets(tiles, out, cols, width):
    out.mkdir(parents=True, exist_ok=True)
    f = font(max(12, width // 28))
    per = cols * 4
    paths = []
    for n in range(0, len(tiles), per):
        group = tiles[n:n + per]
        ims = [Image.open(t["png"]).convert("RGB") for t in group]
        h = ims[0].height; bar = f.size + 10
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * width, rows * (h + bar)), (12, 10, 14))
        d = ImageDraw.Draw(sheet)
        for i, (im, t) in enumerate(zip(ims, group)):
            x, y = (i % cols) * width, (i // cols) * (h + bar)
            sheet.paste(im, (x, y + bar))
            d.text((x + 6, y + 4), t["label"], font=f, fill=(246, 241, 234))
        p = out / f"beats_{n // per + 1:02d}.png"; sheet.save(p); paths.append(p)
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("timeline"); ap.add_argument("--out", required=True)
    ap.add_argument("--after", type=float, default=0.3, help="seconds after each beat (default 0.3)")
    ap.add_argument("--cols", type=int, default=4); ap.add_argument("--width", type=int, default=480)
    ap.add_argument("--scenes", help="only these scene ids, comma-separated")
    ap.add_argument("--keep", action="store_true", help="also keep each full-size tile as <out>/tiles/NNNN_<scene>_<beat>.png (for check_frames.py)")
    ap.add_argument("--every", type=float); ap.add_argument("--from", dest="t0", type=float); ap.add_argument("--to", dest="t1", type=float)
    a = ap.parse_args()
    tl = json.loads(Path(a.timeline).read_text()); fps = tl["fps"]
    dur = video_info(a.video)
    want = set(a.scenes.split(",")) if a.scenes else None
    points = []
    if a.every:
        t = a.t0 or 0.0
        while t <= (a.t1 if a.t1 is not None else dur) + 1e-6:
            points.append({"t": t, "label": f"t={t:.2f}s", "scene": "", "beat": ""}); t += a.every
    else:
        for s in tl["scenes"]:
            if want and s["id"] not in want:
                continue
            start = s["startFrame"] / fps
            points.append({"t": start + a.after, "label": f"{s['id']} start  t={start + a.after:.2f}s", "scene": s["id"], "beat": "start"})
            for name, fr in sorted(s.get("beats", {}).items(), key=lambda kv: kv[1]):
                t = start + fr / fps + a.after
                points.append({"t": t, "label": f"{s['id']} {name}  t={t:.2f}s", "scene": s["id"], "beat": name})
    points = [p for p in points if p["t"] < dur - 0.02]
    if not points:
        sys.exit("No beat times inside the video.")
    out = Path(a.out)
    with tempfile.TemporaryDirectory() as tmp:
        for i, p in enumerate(points):
            p["png"] = str(Path(tmp) / f"{i:04d}.png"); grab(a.video, p["t"], p["png"], a.width)
            if a.keep:
                (out / "tiles").mkdir(parents=True, exist_ok=True)
                name = f"{i:04d}_{p['scene'] or 't'}_{(p['beat'] or ('%.2f' % p['t'])).replace(' ', '_')}.png"
                grab(a.video, p["t"], out / "tiles" / name, 1920)
        paths = sheets(points, out, a.cols, a.width)
    (out / "beats.json").write_text(json.dumps([{k: v for k, v in p.items() if k != "png"} for p in points], indent=1))
    print(f"{len(points)} tiles -> " + ", ".join(str(p) for p in paths))


if __name__ == "__main__":
    main()
