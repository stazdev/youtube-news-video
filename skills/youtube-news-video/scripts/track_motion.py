#!/usr/bin/env python3
"""Track one element through a frame folder, frame by frame, by its colours (idea from
rossark0/rossark-motion-skill's track_edges, MIT; own code).

Small motion (a 2% squash, a 5 px float, a slow sway) doesn't show on a contact sheet but is often what
makes a reference feel alive. This measures it.

  .venv/bin/python -I <skill>/scripts/track_motion.py anim/ref/<name>/frames --name drop \
        --colors 3FB0A2,A8E3D9 [--tol 45] [--region x,y,w,h] [--min-run 3] [--sample X,Y --at 1.2]
        [--not-bg 0C0A0E]           # instead of colours: everything that is NOT the background colour
        [--out track_drop.json]

Per frame it records: presence (share of the region covered), cx, cy (centroid), x0, y0, x1, y1 (bounding box),
w, h, aspect (w/h), top/bottom/left/right edges, and mean colour of the element. Lone sparkles and anti-aliased
edges are ignored (a pixel only counts inside a horizontal run of --min-run matching pixels).
--sample X,Y --at T prints the colour at that pixel/time (to pick --colors from the reference instead of guessing).
Output: JSON {fps, start, frame_size, name, series: {prop: [values per frame]}} next to the frames (or --out).
"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image


def hexrgb(h):
    h = h.strip().lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def runs_mask(m, k):
    if k <= 1:
        return m
    c = np.cumsum(np.pad(m.astype(np.int32), ((0, 0), (1, 0))), axis=1)
    full = (c[:, k:] - c[:, :-k]) == k                    # windows of k all-true
    out = np.zeros_like(m)
    for s in range(k):                                    # mark every pixel covered by a full window
        out[:, s:s + full.shape[1]] |= full
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frames"); ap.add_argument("--name", default="el")
    ap.add_argument("--colors"); ap.add_argument("--not-bg"); ap.add_argument("--tol", type=float, default=45)
    ap.add_argument("--region"); ap.add_argument("--min-run", type=int, default=3)
    ap.add_argument("--sample"); ap.add_argument("--at", type=float, default=0.0)
    ap.add_argument("--out")
    a = ap.parse_args()
    fdir = Path(a.frames); meta = json.loads((fdir.parent / "frames.json").read_text()) if (fdir.parent / "frames.json").exists() else {"fps": 30, "start": 0}
    fps, start = meta["fps"], meta.get("start", 0)
    files = sorted(fdir.glob("*.png"))
    if a.sample:
        x, y = map(int, a.sample.split(",")); i = min(len(files) - 1, max(0, round((a.at - start) * fps)))
        px = np.asarray(Image.open(files[i]).convert("RGB"))[y, x]
        print(f"colour at ({x},{y}) t={a.at:.3f}s (frame {i}): #{px[0]:02X}{px[1]:02X}{px[2]:02X}"); return
    if not (a.colors or a.not_bg):
        ap.error("give --colors or --not-bg (or --sample to read a colour first)")
    cols = [hexrgb(c) for c in a.colors.split(",")] if a.colors else None
    bg = hexrgb(a.not_bg) if a.not_bg else None
    keys = ["presence", "cx", "cy", "x0", "y0", "x1", "y1", "w", "h", "aspect", "r", "g", "b"]
    S = {k: [] for k in keys}
    for f in files:
        im = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
        ox = oy = 0
        if a.region:
            x, y, w, h = map(int, a.region.split(",")); im = im[y:y + h, x:x + w]; ox, oy = x, y
        if cols is not None:
            dist = np.min(np.stack([np.linalg.norm(im - c, axis=2) for c in cols]), axis=0); m = dist <= a.tol
        else:
            m = np.linalg.norm(im - bg, axis=2) > a.tol
        m = runs_mask(m, a.min_run)
        n = int(m.sum())
        S["presence"].append(round(n / m.size, 5))
        if n == 0:
            for k in keys[1:]:
                S[k].append(None)
            continue
        ys, xs = np.nonzero(m)
        x0, x1, y0, y1 = int(xs.min()) + ox, int(xs.max()) + ox, int(ys.min()) + oy, int(ys.max()) + oy
        mean = im[m].mean(axis=0)
        for k, v in zip(keys[1:], [float(xs.mean()) + ox, float(ys.mean()) + oy, x0, y0, x1, y1, x1 - x0 + 1, y1 - y0 + 1,
                                    (x1 - x0 + 1) / (y1 - y0 + 1), float(mean[0]), float(mean[1]), float(mean[2])]):
            S[k].append(round(v, 2) if isinstance(v, float) else v)
    out = Path(a.out) if a.out else fdir.parent / f"track_{a.name}.json"
    out.write_text(json.dumps({"fps": fps, "start": start, "frame_size": meta.get("frame_size"), "name": a.name,
                               "colors": a.colors, "not_bg": a.not_bg, "series": S}))
    vis = [i for i, p in enumerate(S["presence"]) if p > 0]
    if vis:
        i0, i1 = vis[0], vis[-1]
        hs = [v for v in S["h"] if v]; ws = [v for v in S["w"] if v]
        print(f"{a.name}: visible frames {i0}-{i1} ({start + i0 / fps:.3f}-{start + i1 / fps:.3f} s); "
              f"size w {min(ws)}-{max(ws)} px, h {min(hs)}-{max(hs)} px; centre from ({S['cx'][i0]:.0f},{S['cy'][i0]:.0f}) "
              f"to ({S['cx'][i1]:.0f},{S['cy'][i1]:.0f}) -> {out}")
    else:
        print(f"{a.name}: never found (loosen --tol or check --colors with --sample)")


if __name__ == "__main__":
    main()
