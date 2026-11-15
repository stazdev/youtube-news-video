#!/usr/bin/env python3
"""ElevenLabs sound effects: the channel's main SFX source.

Input: a JSON list of sounds (written from the storyboard), e.g. anim/direction/sfx_plan.json:
  [{"id": "S04_vent_hiss", "prompt": "deep underwater hydrothermal vent hissing, low rumble, muffled",
    "duration": 4.0, "loop": false, "influence": 0.4, "scene": "S04", "beat": "vent"}]
  id         file name -> <out>/el_<id>.mp3 (letters, digits, _ and - only)
  prompt     what it should sound like: source, action, space, distance, mood (no music, no voices unless wanted)
  duration   seconds, 0.5-30 (omit to let ElevenLabs choose)
  loop       true for ambience beds that must repeat seamlessly
  influence  prompt_influence 0-1 (higher = follows the prompt more literally); default from settings

Run with the project venv from the project root:
  .venv/bin/python -I <skill>/scripts/eleven_sfx.py plan     anim/direction/sfx_plan.json
  .venv/bin/python -I <skill>/scripts/eleven_sfx.py generate anim/direction/sfx_plan.json --out anim/public/sfx [--only id1,id2] [--force] [--takes 2] [--yes]

Settings: settings.json -> "sfx" (model_id, prompt_influence, output_format, sources_csv).
Key: ELEVENLABS_API_KEY in keys.env (never printed). Each file is logged in sources/sources.csv.
"""
import argparse, csv, json, os, re, subprocess, sys, urllib.request, urllib.error
from datetime import date
from pathlib import Path

API = "https://api.elevenlabs.io/v1/sound-generation"
DEFAULTS = {"model_id": "eleven_text_to_sound_v2", "prompt_influence": 0.4, "output_format": "mp3_44100_128",
            "sources_csv": "sources/sources.csv"}


def find_up(name):
    p = Path.cwd().resolve()
    for d in [p, *p.parents]:
        if (d / name).exists():
            return d / name
    return None


def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    kf = find_up("keys.env")
    if not k and kf:
        for line in kf.read_text().splitlines():
            if line.strip().startswith("ELEVENLABS_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not k:
        sys.exit("ELEVENLABS_API_KEY not found: add it to keys.env in the project root.")
    return k


def settings():
    s = dict(DEFAULTS)
    sf = find_up("settings.json")
    if sf:
        s.update(json.loads(sf.read_text()).get("sfx", {}))
    return s


def load_plan(path):
    items = json.loads(Path(path).read_text())
    if isinstance(items, dict):
        items = items.get("sfx", [])
    seen = set()
    for it in items:
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", it.get("id", "")):
            sys.exit(f"Bad id {it.get('id')!r}: use letters, digits, _ and - only.")
        if it["id"] in seen:
            sys.exit(f"Duplicate id {it['id']}")
        seen.add(it["id"])
        if not it.get("prompt"):
            sys.exit(f"{it['id']}: missing prompt")
        d = it.get("duration")
        if d is not None and not 0.5 <= float(d) <= 30:
            sys.exit(f"{it['id']}: duration must be 0.5-30 s")
    return items


def cmd_plan(a):
    s, items = settings(), load_plan(a.plan)
    total = 0.0
    print(f"Model {s['model_id']} · prompt influence {s['prompt_influence']} · {s['output_format']}")
    for it in items:
        d = it.get("duration")
        total += float(d) if d else 5.0
        print(f"  el_{it['id']:<28} {('%.1f s' % d) if d else 'auto':>7} {'loop ' if it.get('loop') else '     '}{it['prompt'][:80]}")
    print(f"Total: {len(items)} sounds, about {total:.0f} s of audio (credits are charged per sound by length; "
          f"check the cost of the first one in your ElevenLabs history).")


def generate(it, s, dst):
    body = {"text": it["prompt"], "model_id": s["model_id"],
            "prompt_influence": float(it.get("influence", s["prompt_influence"]))}
    if it.get("duration"):
        body["duration_seconds"] = float(it["duration"])
    if it.get("loop"):
        body["loop"] = True
    req = urllib.request.Request(f"{API}?output_format={s['output_format']}", method="POST",
                                 data=json.dumps(body).encode(),
                                 headers={"xi-api-key": api_key(), "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            Path(dst).write_bytes(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs error {e.code} for {it['id']}: {e.read().decode(errors='replace')[:400]}")


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    vol = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    mx = re.search(r"max_volume: (-?[\d.]+) dB", vol)
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", vol)
    return {"dur_s": round(float(out or 0), 2), "max_db": float(mx.group(1)) if mx else None,
            "mean_db": float(mean.group(1)) if mean else None}


def log_source(csv_path, fname, it, s):
    p = Path(csv_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    new = not p.exists()
    rows = [] if new else list(csv.reader(p.open()))
    if any(r and r[0] == fname for r in rows):
        return
    with p.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["file", "type", "source", "author", "license", "url", "used_for"])
        w.writerow([fname, "sfx", f"ElevenLabs sound effects ({s['model_id']}), generated {date.today()}",
                    "generated for the channel", "ElevenLabs terms (commercial use on a paid plan)",
                    "prompt: " + it["prompt"], it.get("scene", "") + (" " + it["beat"] if it.get("beat") else "")])


def cmd_generate(a):
    s, items = settings(), load_plan(a.plan)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if a.only:
        keep = {x.strip() for x in a.only.split(",")}
        items = [it for it in items if it["id"] in keep]
    todo = [it for it in items if a.force or not (out / f"el_{it['id']}.mp3").exists()]
    if not todo:
        print("Nothing to generate (all sounds exist; use --force to redo)."); return
    if (len(todo) > 1 or a.takes > 1) and not a.yes:
        sys.exit(f"{len(todo)} sounds x {a.takes} take(s). Re-run with --yes after the user approves.")
    report_p = out / "sfx_report.json"
    report = json.loads(report_p.read_text()) if report_p.exists() else {}
    for it in todo:
        for t in range(1, a.takes + 1):
            name = f"el_{it['id']}.mp3" if a.takes == 1 else f"el_{it['id']}_take{t}.mp3"
            print(f"Generating {name} ...", flush=True)
            generate(it, s, out / name)
            r = probe(out / name)
            flags = []
            # ElevenLabs output is normalised to ~0 dBFS peak; that is expected (the mix sets the level).
            if r["mean_db"] is not None and r["mean_db"] < -45:
                flags.append("very quiet / near silent")
            r.update(prompt=it["prompt"], flags=flags)
            report[name] = r
            log_source(s["sources_csv"], f"sfx/{name}", it, s)
            print(f"   {r['dur_s']} s · mean {r['mean_db']} dB · peak {r['max_db']} dB" + (f" · {', '.join(flags)}" if flags else ""))
    report_p.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    if a.takes > 1:
        print("Pick the best take per sound, rename it to el_<id>.mp3 and delete the others.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("plan")
    g = sub.add_parser("generate"); g.add_argument("plan"); g.add_argument("--out", required=True)
    g.add_argument("--only"); g.add_argument("--force", action="store_true"); g.add_argument("--yes", action="store_true")
    g.add_argument("--takes", type=int, default=1)
    a = ap.parse_args()
    {"plan": cmd_plan, "generate": cmd_generate}[a.cmd](a)


if __name__ == "__main__":
    main()
