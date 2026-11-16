#!/usr/bin/env python3
"""Voice-to-picture sync check: transcribe the finished video and compare when each word is heard
with when timeline.json says it is spoken (the frames the cuts, ticks and captions are built on).

  .venv/bin/python -I <skill>/scripts/sync_check.py <final.mp4> anim/src/data/timeline.json [--tol 0.15]

Timeline format: {"fps", "segments": [{"id", "start" (or "startFrame"), "words": [{"w", "f"}]}]}, where a word's
frame f is relative to its segment's start. Words of 4+ letters are matched to the nearest heard word within
6 s. Prints the median offset per segment (heard minus timeline; negative = the voice runs ahead) and
exits 1 if any segment is off by more than --tol seconds. Catches a mix that drops a clip's delay, a clip
copied in the wrong place, or a timeline built from different clips than the ones mixed.
"""
import argparse, json, re, sys


def key(w):
    return re.sub(r"[^a-z]", "", w.lower())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("timeline"); ap.add_argument("--tol", type=float, default=0.15)
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    tl = json.load(open(a.timeline)); fps = tl["fps"]
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(a.video, language="en", word_timestamps=True, beam_size=5)
    heard = [(key(w.word), w.start) for s in segs for w in s.words]
    bad = 0
    for s in tl.get("segments", []):
        s0 = s.get("start", s.get("startFrame", 0))
        offs = []
        for w in s.get("words", []):
            k = key(w["w"])
            if len(k) < 4:
                continue
            exp = (s0 + w["f"]) / fps
            near = [t - exp for h, t in heard if h == k and abs(t - exp) < 6]
            if near:
                offs.append(min(near, key=abs))
        if not offs:
            print(f"  {s['id']:10} FAIL  no words matched: the voice may be missing or far off here (check by ear)")
            bad += 1
            continue
        offs.sort()
        med = offs[len(offs) // 2]
        ok = abs(med) <= a.tol
        bad += not ok
        print(f"  {s['id']:10} {'PASS' if ok else 'FAIL'}  voice {med:+.2f} s vs timeline ({len(offs)} words)"
              + ("" if ok else "  <- negative: voice runs ahead of the picture" if med < 0 else "  <- voice lags the picture"))
    print("sync PASS" if not bad else f"sync FAIL in {bad} segment(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
