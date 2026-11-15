#!/usr/bin/env python3
"""Director checker: enforces the uniqueness rules in references/director.md on anim/direction/shotlist.json.

Usage: python3 check_shotlist.py anim/direction/shotlist.json [direction/camera_history.json]
Exit code 1 if any rule is broken. Standard library only.
"""
import json, re, sys
from collections import Counter
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / 'references' / 'camera_bible.md'
bible = REF.read_text()
FAMILY, NAME = {}, {}
for m in re.finditer(r'^\| ([MX]\d{3}) \| ([^|]+?) \| ([a-z]+) \|', bible, re.M):
    NAME[m.group(1)] = m.group(2); FAMILY[m.group(1)] = m.group(3)
for m in re.finditer(r'^\| ([ASC]\d{3}) \| ([^|]+?) \|', bible, re.M):
    NAME[m.group(1)] = m.group(2)
sig_line = bible.split('## Signature moves', 1)[1]
SIGNATURE = set(re.findall(r'\b([MX]\d{3})\b', sig_line))

def size_class(s):
    n = int(s[1:])
    if n in (82, 83): return 'wide'
    if n in (76, 77, 89): return 'close'
    return 'medium'

def lens_band(mm):
    if mm is None: return 'normal'
    return 'ultra' if mm <= 18 else 'wide' if mm <= 28 else 'normal' if mm <= 50 else 'portrait' if mm <= 100 else 'tele'

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    sl = json.loads(Path(sys.argv[1]).read_text()); shots = sl['shots']
    hist = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 and Path(sys.argv[2]).exists() else {'videos': []}
    errs, warns = [], []
    for s in shots:
        for k in ('movement', 'angle', 'size'):
            if s.get(k) not in NAME: errs.append(f"{s['id']}: unknown {k} code {s.get(k)}")
    if errs: report(errs, warns); return
    for s in shots:
        if not s.get('reason', '').strip(): errs.append(f"rule 8: {s['id']} has no reason")
    # 1 unique triples
    trip = Counter((s['movement'], s['angle'], s['size']) for s in shots)
    for t, n in trip.items():
        if n > 1: errs.append(f'rule 1: combination {t} ({NAME[t[0]]} / {NAME[t[1]]} / {NAME[t[2]]}) used {n}x')
    # 2 consecutive differences, 3 family runs
    for p, s in zip(shots, shots[1:]):
        if p['movement'] == s['movement']: errs.append(f"rule 2: {p['id']} and {s['id']} both use {NAME[s['movement']]}")
        diffs = sum([FAMILY.get(p['movement']) != FAMILY.get(s['movement']), p['angle'] != s['angle'],
                     size_class(p['size']) != size_class(s['size']), lens_band(p.get('lens_mm')) != lens_band(s.get('lens_mm'))])
        if diffs < 2: errs.append(f"rule 2: {p['id']} → {s['id']} differ in only {diffs} of family/angle/size/lens")
    fams = [FAMILY.get(s['movement']) for s in shots]
    for i in range(len(fams) - 2):
        if fams[i] == fams[i + 1] == fams[i + 2]: errs.append(f"rule 3: family '{fams[i]}' three times in a row from {shots[i]['id']}")
    fc = Counter(fams)
    for f, n in fc.items():
        if len(shots) >= 6 and n / len(shots) > 0.30: errs.append(f"rule 3: family '{f}' covers {n}/{len(shots)} shots (> 30%)")
    # 4 signature moves
    sig = [s for s in shots if s['movement'] in SIGNATURE]
    for m, n in Counter(s['movement'] for s in sig).items():
        if n > 1: errs.append(f'rule 4: signature move {NAME[m]} used {n}x')
    for p, s in zip(shots, shots[1:]):
        if p['movement'] in SIGNATURE and s['movement'] in SIGNATURE and p['scene'] != s['scene']:
            errs.append(f"rule 4: signature moves in consecutive scenes {p['id']} and {s['id']}")
    # 5 chapter openers
    op = [s for s in shots if s.get('opener')]
    for f, n in Counter(FAMILY.get(s['movement']) for s in op).items():
        if n > 1: errs.append(f"rule 5: {n} chapter openers use the '{f}' family")
    # 6 size rhythm
    sc = [size_class(s['size']) for s in shots]
    for i in range(len(sc) - 3):
        if len(set(sc[i:i + 4])) == 1: errs.append(f"rule 6: four {sc[i]} shots in a row from {shots[i]['id']}")
    # 7 history (last 3 videos)
    recent = hist.get('videos', [])[-3:]
    used = {(h.get('moment'), h['movement'], h['angle']) for v in recent for h in v.get('shots', []) if h.get('first_of_scene', True)}
    firsts = {}
    for s in shots: firsts.setdefault(s['scene'], s)
    for s in firsts.values():
        if (s.get('moment'), s['movement'], s['angle']) in used:
            errs.append(f"rule 7: {s['id']} reuses ({NAME[s['movement']]}, {NAME[s['angle']]}) for a '{s.get('moment')}' scene from a recent video")
    if recent and shots:
        prev_open = recent[-1].get('shots', [{}])[0]
        if prev_open and (prev_open.get('movement'), prev_open.get('angle')) == (shots[0]['movement'], shots[0]['angle']):
            errs.append('rule 7: cold-open first shot repeats the previous video')
    # 11 coverage
    by_scene = Counter(s['scene'] for s in shots)
    for sid in by_scene:
        span = [s for s in shots if s['scene'] == sid]
        dur = max(s['to'] for s in span) - min(s['from'] for s in span)
        if dur > 7.5 and len(span) < 2: warns.append(f'rule 11: {sid} lasts {dur:.1f} s with one shot (give it 2-3 shots or distinct phases)')
    report(errs, warns, len(shots))

def report(errs, warns, n=0):
    for w in warns: print('WARN  ' + w)
    for e in errs: print('ERROR ' + e)
    print(f"{'FAILED' if errs else 'PASSED'}: {n} shots, {len(errs)} errors, {len(warns)} warnings")
    sys.exit(1 if errs else 0)

if __name__ == '__main__':
    main()
