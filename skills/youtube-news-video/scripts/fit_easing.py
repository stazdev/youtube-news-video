#!/usr/bin/env python3
"""Fit the timing and easing of one move in a tracked series (idea from NiazMorshed2007/reanimate's
easing.ts, MIT; own code). Turns "it moves nicely" into numbers you can type into Remotion.

  .venv/bin/python -I <skill>/scripts/fit_easing.py anim/ref/<name>/track_drop.json --prop cy
        [--from 0.5 --to 2.0]              # seconds: only this window (one move at a time)
        [--vs anim/ours/<name>/track_drop.json]   # also fit ours and print the difference (pass ±0.08 s)

Props: cx, cy (position), w, h, aspect (squash/stretch), x0..y1 (edges), presence (fade/grow), r, g, b (colour).
Prints: start, end, duration (s and frames), travel, best easing family with its error, overshoot %, settle time,
and the best-fitting cubic-bezier as `Easing.bezier(x1, y1, x2, y2)` + `interpolate(frame, [a, b], [from, to])`.
Error is RMSE as a share of the travel (≤ 0.03 is a close fit; > 0.08 means the move isn't one simple ease:
split the window, or it is a chain of poses: use flow()).
"""
import argparse, json, math, sys
from pathlib import Path
import numpy as np


def bezier_fn(x1, y1, x2, y2):
    s = np.linspace(0, 1, 401)
    bx = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s ** 2 * x2 + s ** 3
    by = 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s ** 2 * y2 + s ** 3
    return lambda u: np.interp(u, bx, by)


def fam():
    F = {"linear": lambda u: u}
    pw = {"quad": 2, "cubic": 3, "quart": 4, "quint": 5}
    for n, k in pw.items():
        F[f"easeIn{n.title()}"] = lambda u, k=k: u ** k
        F[f"easeOut{n.title()}"] = lambda u, k=k: 1 - (1 - u) ** k
        F[f"easeInOut{n.title()}"] = lambda u, k=k: np.where(u < .5, 2 ** (k - 1) * u ** k, 1 - (-2 * u + 2) ** k / 2)
    F["easeInSine"] = lambda u: 1 - np.cos(u * np.pi / 2)
    F["easeOutSine"] = lambda u: np.sin(u * np.pi / 2)
    F["easeInOutSine"] = lambda u: -(np.cos(np.pi * u) - 1) / 2
    F["easeOutExpo"] = lambda u: np.where(u >= 1, 1, 1 - 2 ** (-10 * u))
    F["easeInExpo"] = lambda u: np.where(u <= 0, 0, 2 ** (10 * u - 10))
    F["easeOutCirc"] = lambda u: np.sqrt(1 - (u - 1) ** 2)
    for c in (1.0, 1.70158, 2.5):
        F[f"easeOutBack({c:g})"] = lambda u, c=c: 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2
    for z in (0.35, 0.5, 0.7, 0.9):
        def spring(u, z=z):
            w = 2 * np.pi * 1.6 / max(1e-6, 1)  # ~1.6 cycles over the window, settles by u=1 for these dampings
            wd = w * math.sqrt(1 - z * z)
            y = 1 - np.exp(-z * w * u) * (np.cos(wd * u) + z / math.sqrt(1 - z * z) * np.sin(wd * u))
            return np.where(u >= 1, 1 - np.exp(-z * w) * (np.cos(wd) + z / math.sqrt(1 - z * z) * np.sin(wd)), y)
        F[f"spring(damping {z})"] = spring
    return F


def load(path, prop, t0=None, t1=None):
    j = json.loads(Path(path).read_text()); fps = j["fps"]; st = j.get("start", 0)
    v = np.array([np.nan if x is None else x for x in j["series"][prop]], float)
    t = st + np.arange(len(v)) / fps
    m = np.ones(len(v), bool)
    if t0 is not None: m &= t >= t0 - 1e-9
    if t1 is not None: m &= t <= t1 + 1e-9
    t, v = t[m], v[m]
    ok = ~np.isnan(v)
    if ok.sum() < 4: sys.exit(f"{path}: '{prop}' has fewer than 4 frames with the element visible in that window")
    v = np.interp(t, t[ok], v[ok])
    return t, v, fps


def fit(t, v, fps):
    k = max(2, len(v) // 10)
    a, b = float(np.median(v[:k])), float(np.median(v[-k:]))
    travel = b - a
    if abs(travel) < 1e-6 or abs(travel) < 0.5 and np.ptp(v) < 1:
        return {"moves": False, "range": float(np.ptp(v))}
    p = (v - a) / travel
    mv = np.nonzero(np.abs(p) > 0.03)[0]; i0 = max(0, mv[0] - 1) if len(mv) else 0
    st = np.nonzero(np.abs(p - 1) > 0.03)[0]; i1 = min(len(v) - 1, st[-1] + 1) if len(st) else len(v) - 1
    over = float(max(0.0, (p.max() - 1))) * 100
    F = fam(); best = []
    starts = t[max(0, i0 - 2):i0 + 3]; dur0 = max(t[i1] - t[i0], 1 / fps)
    durs = dur0 * np.linspace(0.75, 1.35, 13)
    for name, f in F.items():
        e_best = (9e9, None, None)
        for s0 in starts:
            for d in durs:
                u = np.clip((t - s0) / d, 0, 1)
                e = math.sqrt(np.mean((f(u) - p) ** 2))
                if e < e_best[0]: e_best = (e, s0, d)
        best.append((e_best[0], name, e_best[1], e_best[2]))
    best.sort()
    e, name, s0, d = best[0]
    # cubic-bezier fit on the chosen window
    u = np.clip((t - s0) / d, 0, 1)
    grid = np.round(np.linspace(0, 1, 11), 2); ygrid = np.round(np.linspace(-0.4, 1.6, 21), 2)
    bb = (9e9, None)
    for x1 in grid:
        for x2 in grid:
            for y1 in ygrid:
                for y2 in ygrid[::2]:
                    ee = math.sqrt(np.mean((bezier_fn(x1, y1, x2, y2)(u) - p) ** 2))
                    if ee < bb[0]: bb = (ee, (x1, y1, x2, y2))
    x1, y1, x2, y2 = bb[1]
    for step in (0.05, 0.02):                              # local refine
        for _ in range(3):
            for idx in range(4):
                for dlt in (-step, step):
                    c = [x1, y1, x2, y2]; c[idx] = c[idx] + dlt
                    if not (0 <= c[0] <= 1 and 0 <= c[2] <= 1): continue
                    ee = math.sqrt(np.mean((bezier_fn(*c)(u) - p) ** 2))
                    if ee < bb[0]: bb = (ee, tuple(c)); x1, y1, x2, y2 = c
    settle = None
    after = np.nonzero(np.abs(p - 1) > 0.02)[0]
    if len(after): settle = float(t[min(len(t) - 1, after[-1] + 1)])
    return {"moves": True, "from": a, "to": b, "travel": travel, "start": float(s0), "end": float(s0 + d), "dur": float(d),
            "frames": round(d * fps, 1), "family": name, "err": e, "runner_up": [(n, round(x, 3)) for x, n, _, _ in best[1:4]],
            "overshoot_pct": over, "settle": settle, "bezier": [round(x, 2) for x in bb[1]], "bezier_err": bb[0]}


def show(label, r, fps, prop):
    if not r["moves"]:
        print(f"{label}: '{prop}' doesn't move in this window (range {r['range']:.2f})"); return
    print(f"{label}: {prop} {r['from']:.1f} -> {r['to']:.1f} (travel {r['travel']:+.1f})")
    print(f"   start {r['start']:.3f} s, end {r['end']:.3f} s, duration {r['dur']:.3f} s ({r['frames']} frames at {fps:g} fps)")
    print(f"   best easing: {r['family']} (error {r['err']:.3f}); next: " + ", ".join(f"{n} {e}" for n, e in r["runner_up"]))
    print(f"   overshoot {r['overshoot_pct']:.1f}%" + (f", settles at {r['settle']:.3f} s" if r["settle"] else ""))
    b = r["bezier"]
    print(f"   cubic-bezier: Easing.bezier({b[0]}, {b[1]}, {b[2]}, {b[3]}) (error {r['bezier_err']:.3f})")
    print(f"   Remotion: interpolate(frame, [{round(r['start'] * fps)}, {round(r['end'] * fps)}], [{r['from']:.1f}, {r['to']:.1f}], "
          f"{{easing: Easing.bezier({b[0]}, {b[1]}, {b[2]}, {b[3]}), extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}})")
    if r["err"] > 0.08 and r["bezier_err"] > 0.08:
        print("   note: no single ease fits well: split the window into separate moves, or use flow() through key poses")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track"); ap.add_argument("--prop", required=True)
    ap.add_argument("--from", dest="t0", type=float); ap.add_argument("--to", dest="t1", type=float)
    ap.add_argument("--vs"); ap.add_argument("--tol", type=float, default=0.08)
    a = ap.parse_args()
    t, v, fps = load(a.track, a.prop, a.t0, a.t1); r = fit(t, v, fps); show("reference" if a.vs else Path(a.track).stem, r, fps, a.prop)
    if a.vs:
        t2, v2, fps2 = load(a.vs, a.prop, a.t0, a.t1); r2 = fit(t2, v2, fps2); show("ours", r2, fps2, a.prop)
        if r["moves"] and r2["moves"]:
            ds, de, dd = r2["start"] - r["start"], r2["end"] - r["end"], r2["dur"] - r["dur"]
            rel = (r2["travel"] / r["travel"] - 1) * 100 if r["travel"] else 0
            ok = abs(ds) <= a.tol and abs(de) <= a.tol and abs(dd) <= a.tol
            fam_ok = r["family"].split("(")[0].replace("In", "").replace("Out", "")[:4] == r2["family"].split("(")[0].replace("In", "").replace("Out", "")[:4]
            print(f"difference: start {ds:+.3f} s, end {de:+.3f} s, duration {dd:+.3f} s, travel {rel:+.0f}% of the reference, "
                  f"overshoot {r2['overshoot_pct'] - r['overshoot_pct']:+.1f} pts -> timing {'PASS' if ok else 'FAIL'} (±{a.tol} s)"
                  + ("" if (r['family'] == r2['family']) else f"; easing differs ({r['family']} vs {r2['family']})"))
            sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
