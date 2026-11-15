#!/usr/bin/env python3
"""Colour checker for the composition decider (no neon, controlled chroma, readable contrast).

Usage:
  python3 check_palette.py anim/direction/look.json      # checks every chapter/scene palette in look.json
  python3 check_palette.py --hex "#0E3B5C,#1F7FB0,#7FC8E8,#F5F7FA,#F2C14E"
  python3 check_palette.py --library                     # checks the mood library in references/composition_decider.md
Palette order: dominant, secondary, tertiary, light, accent (the 5th colour is the accent). Exit code 1 on any failure.
Standard library only.
"""
import json, math, re, sys
from pathlib import Path

def srgb_to_lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_rgb(h):
    h = h.strip().lstrip('#')
    if len(h) == 3: h = ''.join(ch * 2 for ch in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def oklch(h):
    r, g, b = (srgb_to_lin(v) for v in hex_rgb(h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(a, bb), (math.degrees(math.atan2(bb, a)) + 360) % 360

def hsv(h):
    r, g, b = (v / 255 for v in hex_rgb(h))
    mx, mn = max(r, g, b), min(r, g, b)
    return (0 if mx == 0 else (mx - mn) / mx), mx

def lum(h):
    r, g, b = (srgb_to_lin(v) for v in hex_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def is_neon(h):
    L, C, _ = oklch(h); S, V = hsv(h)
    return (C >= 0.20 and L >= 0.62) or (S >= 0.90 and V >= 0.95)

def check(name, pal, neon_ok=False):
    errs = []
    if not 2 <= len(pal) <= 6: errs.append(f'{len(pal)} colours (use 5: dominant, secondary, tertiary, light, accent)')
    for i, h in enumerate(pal):
        L, C, _ = oklch(h)
        if is_neon(h) and not neon_ok: errs.append(f'{h} is neon (L={L:.2f}, C={C:.3f}); neon only where the script asks for it')
        accent = i == len(pal) - 1
        lim = 0.19 if accent else 0.16
        if C > lim and not neon_ok: errs.append(f'{h} chroma {C:.3f} > {lim} ({"accent" if accent else "large-area"} limit)')
    darkest = min(pal, key=lum); lightest = max(pal, key=lum)
    cr = contrast(darkest, lightest)
    if cr < 4.5: errs.append(f'darkest/lightest contrast {cr:.1f}:1 < 4.5:1 (text needs a readable pair)')
    print(('FAIL ' if errs else 'ok   ') + name + '  ' + ' '.join(pal) + (f'  (contrast {cr:.1f}:1)' if not errs else ''))
    for e in errs: print('      - ' + e)
    return not errs

def main():
    a = sys.argv[1:]
    ok = True
    if not a:
        print(__doc__); sys.exit(2)
    if a[0] == '--hex':
        ok = check('palette', [x for x in re.split(r'[\s,]+', a[1]) if x])
    elif a[0] == '--library':
        md = (Path(__file__).resolve().parent.parent / 'references' / 'composition_decider.md').read_text()
        for m in re.finditer(r'^\| ([a-z-]+) \| ((?:#[0-9A-Fa-f]{6} ?){5}) \|', md, re.M):
            ok &= check(m.group(1), m.group(2).split())
    else:
        look = json.loads(Path(a[0]).read_text())
        neon = set(look.get('neon_allowed_scenes', []))
        for ch in look.get('chapters', []):
            ok &= check(f"chapter {ch.get('n')} ({ch.get('mood', '')})", ch['palette'])
        for sc in look.get('scenes', []):
            if 'palette' in sc: ok &= check(f"scene {sc['id']}", sc['palette'], sc['id'] in neon)
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
