#!/usr/bin/env python3
"""Reference vs ours, frame by frame (method adapted from NiazMorshed2007/reanimate's compare.ts, MIT; own code).

Both folders must come from ref_frames.py with the same window, crop, fps and width (use --like for ours).

  .venv/bin/python -I <skill>/scripts/motion_compare.py anim/ref/<name> anim/ours/<name> --out anim/ref/<name>/compare-1
        [--max-shift 15] [--tol 0.08] [--every 2] [--no-align]

Measures, independent of colours, fonts and copy:
  - activity curve: how much changes from each frame to the next (the shape shows timing, easing, stagger)
  - offset: the frame shift that best lines ours up with the reference (a late or early start)
  - motion window: first change, last change and the peak, for both; timing errors in seconds
  - per-segment timing: the reference is split into its separate moves (bursts of activity between still
    moments); each one's start/end/peak is matched to ours
  - picture mismatch per frame (share of pixels that clearly differ), useful only for pixel-faithful work
Writes report.md, report.json, activity.png (both curves) and sheets/compare_NN.png (reference | ours | difference).
PASS when every timing error is within --tol seconds (default 0.08 s, under 3 frames at 30 fps).
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SMALL = (192, 108)


def load(d):
    d = Path(d); meta = json.loads((d / "frames.json").read_text()); files = sorted((d / "frames").glob("*.png"))
    big = [Image.open(f).convert("RGB") for f in files]
    w, h = big[0].size; sw = 192 if w >= h else 108; sh = int(round(h * sw / w))
    small = np.stack([np.asarray(im.resize((sw, sh), Image.BILINEAR).convert("L"), np.float32) / 255 for im in big])
    return meta, files, big, small


def activity(s):
    a = np.abs(np.diff(s, axis=0)).mean(axis=(1, 2))
    return np.concatenate([[0.0], a])


def threshold(a):
    # "something is moving" = clearly above the clip's own noise floor (compression shimmer, grain),
    # or 1.5% of its biggest change, whichever is larger; so quiet moves next to a big one still count
    floor = float(np.percentile(a[1:], 20)) if len(a) > 2 else 0.0
    return max(2e-4, 4 * floor, 0.015 * float(a.max()))


def window(a, fps, thr):
    on = np.nonzero(a > thr)[0]
    if not len(on): return None
    return {"start": on[0] / fps, "end": on[-1] / fps, "peak": int(np.argmax(a)) / fps}


def segments(a, fps, thr, gap=0.25):
    on = a > thr; segs = []; s = None; quiet = 0
    for i, v in enumerate(on):
        if v:
            if s is None: s = i
            quiet = 0; e = i
        elif s is not None:
            quiet += 1
            if quiet / fps >= gap: segs.append((s, e)); s = None
    if s is not None: segs.append((s, e))
    out = []
    for s, e in segs:
        if e - s < 1: continue
        pk = s + int(np.argmax(a[s:e + 1]))
        out.append({"start": s / fps, "end": e / fps, "peak": pk / fps})
    return out


def cuts(a, fps, k=5.0, w=6, floor=0.02):
    # a cut / scene change = one frame whose change is >= k x the median of the frames around it (and big)
    out = []
    for i in range(1, len(a)):
        nb = np.concatenate([a[max(1, i - w):i], a[i + 1:i + w + 1]])
        if len(nb) and a[i] >= floor and a[i] >= k * max(float(np.median(nb)), 1e-4) and a[i] >= a[max(1, i - 1):i + 2].max():
            if not out or i - out[-1] > 3: out.append(i)
    return [i / fps for i in out]


def split_at(segs, cut_times, fps):
    # continuous references never go still: split their moves at the cuts, so each section is checked on its own
    out = []
    for sg in segs:
        edges = [sg["start"]] + [c for c in cut_times if sg["start"] + 1.5 / fps < c < sg["end"] - 1.5 / fps] + [sg["end"]]
        for a0, b0 in zip(edges, edges[1:]):
            if b0 - a0 >= 2 / fps:
                out.append({"start": a0, "end": b0, "peak": a0})
    return out


def font(n):
    for f in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        try: return ImageFont.truetype(f, n)
        except OSError: pass
    return ImageFont.load_default()


def plot(ar, ao, off, fps, dest):
    W, H, pad = 1200, 360, 40; im = Image.new("RGB", (W, H), (12, 10, 14)); d = ImageDraw.Draw(im); f = font(16)
    n = max(len(ar), len(ao) - off if off > 0 else len(ao)); top = max(ar.max(), ao.max(), 1e-6)
    def pts(a, shift):
        return [(pad + (i - shift) * (W - 2 * pad) / max(1, n - 1), H - pad - v / top * (H - 2 * pad)) for i, v in enumerate(a) if 0 <= i - shift < n]
    d.line(pts(ar, 0), fill=(168, 227, 217), width=3); d.line(pts(ao, off), fill=(217, 115, 58), width=2)
    for s in range(int(n / fps) + 1):
        x = pad + s * fps * (W - 2 * pad) / max(1, n - 1); d.line([(x, H - pad), (x, H - pad + 6)], fill=(200, 200, 200)); d.text((x - 6, H - pad + 8), f"{s}s", font=f, fill=(200, 200, 200))
    d.text((pad, 8), "activity per frame: reference (teal) vs ours (orange, aligned)", font=f, fill=(246, 241, 234)); im.save(dest)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ref"); ap.add_argument("ours"); ap.add_argument("--out", required=True)
    ap.add_argument("--max-shift", type=int, default=15); ap.add_argument("--tol", type=float, default=0.08)
    ap.add_argument("--every", type=int, default=2); ap.add_argument("--no-align", action="store_true")
    ap.add_argument("--pixel", type=float, default=0.12, help="per-pixel difference that counts as a mismatch (0-1)")
    a = ap.parse_args()
    out = Path(a.out); (out / "sheets").mkdir(parents=True, exist_ok=True)
    mr, fr, br, sr = load(a.ref); mo, fo, bo, so = load(a.ours)
    warn = []
    if abs(mr["fps"] - mo["fps"]) > 1e-3: warn.append(f"fps differ: {mr['fps']} vs {mo['fps']} (re-extract ours with --like)")
    if mr.get("frame_size") != mo.get("frame_size"): warn.append(f"frame sizes differ: {mr.get('frame_size')} vs {mo.get('frame_size')} (ours is resized for the comparison)")
    fps = mr["fps"]
    if sr.shape[1:] != so.shape[1:]:
        so = np.stack([np.asarray(Image.fromarray((x * 255).astype(np.uint8)).resize((sr.shape[2], sr.shape[1])), np.float32) / 255 for x in so])
    ar, ao = activity(sr), activity(so)
    # offset: shift of ours that best matches the reference's activity curve (normalised)
    off = 0
    if not a.no_align:
        best = (9e9, 0)
        nr, no = ar / (ar.max() or 1), ao / (ao.max() or 1)
        for k in range(-a.max_shift, a.max_shift + 1):
            i = np.arange(len(nr)); j = i + k; m = (j >= 0) & (j < len(no))
            if m.sum() < len(nr) * 0.6: continue
            e = np.mean((nr[i[m]] - no[j[m]]) ** 2)
            if e < best[0]: best = (e, k)
        off = best[1]
    thr = threshold(ar)                       # one threshold, from the reference, for both
    wr, wo = window(ar, fps, thr), window(ao, fps, thr)
    res = {"fps": fps, "offset_frames": off, "offset_s": round(off / fps, 3), "warnings": warn, "rows": []}
    ok = True

    def row(name, r, o):
        nonlocal ok
        e = {k: round(o[k] - r[k], 3) for k in ("start", "end", "peak")}; e["duration"] = round((o["end"] - o["start"]) - (r["end"] - r["start"]), 3)
        p = all(abs(v) <= a.tol for k, v in e.items() if k != "peak") and abs(e["peak"]) <= 2 * a.tol
        ok = ok and p
        res["rows"].append({"what": name, "ref": r, "ours": o, "error_s": e, "pass": p})
    if wr and wo:
        row("whole animation (no alignment)", wr, wo)
    cr, co = cuts(ar, fps), cuts(ao, fps)
    for i, c in enumerate(cr):                 # every cut in the reference must land within tol in ours
        near = [x for x in co if abs(x - c) <= max(0.5, 3 * a.tol)]
        if near:
            o = min(near, key=lambda x: abs(x - c)); e = round(o - c, 3); p = abs(e) <= a.tol; ok = ok and p
            res["rows"].append({"what": f"cut {i + 1}", "ref": {"start": c, "end": c, "peak": c}, "ours": {"start": o, "end": o, "peak": o},
                                "error_s": {"start": e, "end": e, "duration": 0.0, "peak": e}, "pass": p})
        else:
            res["rows"].append({"what": f"cut {i + 1}", "ref": {"start": c, "end": c, "peak": c}, "ours": None, "pass": False}); ok = False
    for o in co:
        if not any(abs(o - c) <= max(0.5, 3 * a.tol) for c in cr):
            res["rows"].append({"what": "extra cut in ours", "ref": None, "ours": {"start": o, "end": o, "peak": o}, "pass": False}); ok = False
    res["cuts_ref"], res["cuts_ours"] = [round(c, 3) for c in cr], [round(c, 3) for c in co]
    sgr, sgo = split_at(segments(ar, fps, thr), cr, fps), split_at(segments(ao, fps, thr), co, fps)
    for lst, aa in ((sgr, ar), (sgo, ao)):
        for sg in lst:
            i0, i1 = int(round(sg["start"] * fps)), int(round(sg["end"] * fps))
            sg["peak"] = (i0 + int(np.argmax(aa[i0:i1 + 1]))) / fps if i1 > i0 else sg["start"]
    used = set()
    for i, s in enumerate(sgr):
        cand = [(abs(o["start"] - s["start"]) + abs(o["end"] - s["end"]), j) for j, o in enumerate(sgo) if j not in used]
        if not cand:
            res["rows"].append({"what": f"move {i + 1}", "ref": s, "ours": None, "pass": False}); ok = False; continue
        _, j = min(cand); used.add(j); row(f"move {i + 1}", s, sgo[j])
    for j, o in enumerate(sgo):
        if j not in used:
            res["rows"].append({"what": "extra move in ours", "ref": None, "ours": o, "pass": False}); ok = False
    # pixel mismatch (aligned)
    mism = []
    for i in range(len(sr)):
        j = i + off
        if 0 <= j < len(so): mism.append(float((np.abs(sr[i] - so[j]) > a.pixel).mean()))
    res["mismatch_mean"] = round(float(np.mean(mism)), 4) if mism else None
    res["mismatch_worst"] = round(float(np.max(mism)), 4) if mism else None
    res["pass"] = ok
    plot(ar, ao, off, fps, out / "activity.png")
    # side-by-side sheets: reference | ours | difference
    tw = 300 if br[0].width >= br[0].height else 170; th = int(br[0].height * tw / br[0].width); f = font(14)
    idx = list(range(0, len(br), a.every)); per = 6
    for n in range(0, len(idx), per):
        rows = idx[n:n + per]; sheet = Image.new("RGB", (tw * 3, len(rows) * (th + 20)), (12, 10, 14)); d = ImageDraw.Draw(sheet)
        for r, i in enumerate(rows):
            j = min(max(0, i + off), len(bo) - 1); y = r * (th + 20)
            A = br[i].resize((tw, th)); B = bo[j].resize((tw, th))
            D = Image.fromarray((np.clip(np.abs(np.asarray(A, np.int16) - np.asarray(B, np.int16)).max(axis=2) * 3, 0, 255)).astype(np.uint8)).convert("RGB")
            for c, im in enumerate((A, B, D)): sheet.paste(im, (c * tw, y + 20))
            d.text((4, y + 2), f"ref f{i} {i / fps:.2f}s | ours f{j} | diff", font=f, fill=(246, 241, 234))
        sheet.save(out / "sheets" / f"compare_{n // per + 1:02d}.png")
    (out / "report.json").write_text(json.dumps(res, indent=1))
    L = [f"# Reference vs ours ({fps:g} fps)", "All numbers measured from the frames.", ""]
    L += [f"- warning: {w}" for w in warn]
    L.append(f"- offset: ours is shifted {off:+d} frames ({off / fps:+.3f} s) against the reference" + (" (start earlier/later)" if off else ""))
    L += ["", "| what | ref start-end (peak) | ours start-end (peak) | error start / end / duration / peak (s) | result |", "|---|---|---|---|---|"]
    for r in res["rows"]:
        fmt = lambda w: f"{w['start']:.2f}-{w['end']:.2f} ({w['peak']:.2f})" if w else "missing"
        e = r.get("error_s"); es = f"{e['start']:+.3f} / {e['end']:+.3f} / {e['duration']:+.3f} / {e['peak']:+.3f}" if e else "-"
        L.append(f"| {r['what']} | {fmt(r['ref'])} | {fmt(r['ours'])} | {es} | {'PASS' if r['pass'] else 'FAIL'} |")
    L += ["", f"picture mismatch (aligned): mean {res['mismatch_mean']}, worst {res['mismatch_worst']} (only meaningful for pixel-faithful work)",
          f"**{'PASS' if ok else 'FAIL'}** (timing tolerance ±{a.tol} s) · activity.png · sheets/compare_NN.png"]
    (out / "report.md").write_text("\n".join(L) + "\n"); print("\n".join(L))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
