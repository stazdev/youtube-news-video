#!/usr/bin/env python3
"""Rendered-frame colour check + side-by-side sheets (idea borrowed from Leonxlnx/cook, MIT).

Checks real rendered stills (not palette hex values; that is check_palette.py) for:
  - washed-out / grey frames and oversaturated or neon frames,
  - drift from the style reference (anim/public/style_reference.png) when one exists.
With --ref it also writes one side-by-side PNG per frame (reference left, render right).

Usage:
  python3 check_frames.py anim/out/style_S*.png
  python3 check_frames.py --ref anim/public/style_reference.png --sheets anim/out/compare anim/out/style_S*.png
  python3 check_frames.py --neon-ok S07,S12 anim/out/style_S*.png     # scenes where the script asks for neon
Exit code 1 if any frame fails. Needs ffmpeg on PATH; standard library only.
Every number printed is MEASURED (computed from pixels), so it can be quoted as such in reports.
"""
import argparse, math, re, subprocess, sys
from pathlib import Path

W, H = 96, 54  # analysis size; enough for colour statistics, fast

def pixels(path):
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', str(path), '-frames:v', '1',
         '-vf', f'scale={W}:{H}:flags=area', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
        capture_output=True, check=True).stdout
    return [raw[i:i + 3] for i in range(0, len(raw) - 2, 3)]

LUT = [((v / 255) / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4) for v in range(256)]

def oklch(rgb):
    r, g, b = (LUT[v] for v in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(a, bb)

def stats(path):
    px = [oklch(p) for p in pixels(path)]
    Ls = sorted(p[0] for p in px); Cs = sorted(p[1] for p in px); n = len(px)
    neon = sum(1 for L, C in px if C >= 0.20 and L >= 0.62) / n
    return {
        'L': sum(Ls) / n, 'L_p5': Ls[int(n * .05)], 'L_p95': Ls[int(n * .95)],
        'L_p50': Ls[n // 2], 'L_p997': Ls[min(n - 1, int(n * .997))],
        'subj': sum(1 for L in Ls if L > Ls[n // 2] + 0.25) / n,
        'C': sum(Cs) / n, 'C_p95': Cs[int(n * .95)], 'neon': neon,
    }

def side_by_side(ref, frame, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(ref), '-i', str(frame), '-filter_complex',
                    '[0:v]scale=-2:540[a];[1:v]scale=-2:540[b];[a][b]hstack=inputs=2', '-frames:v', '1', str(out)],
                   check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('frames', nargs='+')
    ap.add_argument('--ref', help='style reference image')
    ap.add_argument('--sheets', help='folder for side-by-side PNGs (needs --ref)')
    ap.add_argument('--neon-ok', default='', help='comma-separated scene ids allowed to be neon')
    a = ap.parse_args()
    neon_ok = {s.strip() for s in a.neon_ok.split(',') if s.strip()}
    ref = stats(a.ref) if a.ref else None
    if ref:
        print(f"reference  L={ref['L']:.2f} C={ref['C']:.3f} C95={ref['C_p95']:.3f}")
    failed = 0
    for f in a.frames:
        p = Path(f); s = stats(p); errs = []; warns = []
        scene = (re.search(r'S\d+', p.name) or [None])[0]
        # Near-monochrome can be a deliberate look (newsprint, chalkboard), so without a reference it only warns.
        if s['C_p95'] < 0.03 and not (ref and ref['C_p95'] < 0.03):
            (errs if ref else warns).append('grey frame: almost no colour anywhere (if not intended, check grade, tone mapping, fog, exposure before repainting)')
        if s['L_p95'] - s['L_p5'] < 0.18:
            # A small bright subject on a calm ground (title cards, logos, minimal brand frames) is invisible to the
            # 5-95% spread, so judge it by the subject itself: brightest 0.3% vs the median ground, and its area.
            sc = s['L_p997'] - s['L_p50']
            if sc >= 0.45 and s['subj'] >= 0.005:
                warns.append(f"small subject on flat ground: subject contrast {sc:.2f}, subject area {s['subj']:.1%} (fine for minimal/brand frames; for scenes, add depth or mid-tones)")
            else:
                errs.append(f"flat contrast: L range {s['L_p5']:.2f}-{s['L_p95']:.2f}, subject contrast {sc:.2f}, subject area {s['subj']:.1%}")
        if s['C'] > 0.14: errs.append(f"oversaturated: mean chroma {s['C']:.3f} > 0.14")
        if s['neon'] > 0.02 and scene not in neon_ok: errs.append(f"neon pixels cover {s['neon']:.0%} of the frame")
        if ref:
            if s['C'] < ref['C'] * 0.6: errs.append(f"washed out vs reference: chroma {s['C']:.3f} vs {ref['C']:.3f}")
            if s['C'] > ref['C'] * 1.6 + 0.01: errs.append(f"more saturated than reference: chroma {s['C']:.3f} vs {ref['C']:.3f}")
            if abs(s['L'] - ref['L']) > 0.15: errs.append(f"brightness off reference: L {s['L']:.2f} vs {ref['L']:.2f}")
            if a.sheets: side_by_side(a.ref, p, Path(a.sheets) / f'sbs_{p.stem}.png')
        tag = 'FAIL' if errs else ('warn' if warns else 'ok  ')
        print(f"{tag} {p.name}  L={s['L']:.2f} ({s['L_p5']:.2f}-{s['L_p95']:.2f}) C={s['C']:.3f} C95={s['C_p95']:.3f} neon={s['neon']:.1%}")
        for e in errs: print(f'       - {e}')
        for w in warns: print(f'       ~ {w}')
        failed += bool(errs)
    print(f'{len(a.frames) - failed}/{len(a.frames)} frames pass')
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    main()
