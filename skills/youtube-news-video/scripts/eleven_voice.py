#!/usr/bin/env python3
"""ElevenLabs narration for a news episode: one clip per .txt script, using the user's own API key.

Reads every <name>.txt in the episode's scripts folder (00_intro, 01_story ... 99_outro, short_A, short_B),
generates <name>.mp3 with the channel voice, then checks each take with Whisper (does it say the script?)
and librosa (is it as loud as the others?).

Run from the project root with its venv:  .venv/bin/python -I <skill>/scripts/eleven_voice.py <command> ...

  voices                                    list the voices in the user's ElevenLabs library (free)
  plan     SCRIPTS_DIR                      list clips, character counts and the total (free)
  generate SCRIPTS_DIR --out AUDIO_DIR [--only 01_story,short_A] [--force] [--yes] [--voice ID_OR_NAME]
                                            generate missing clips (costs credits), then check them
  check    SCRIPTS_DIR --out AUDIO_DIR      re-run the checks on existing clips (e.g. ones the user recorded)

Voice settings: settings.json -> "voice" in the project root (voice_id, model_id, stability, similarity_boost,
style, use_speaker_boost, output_format, optional speed and seed). --voice overrides the voice for this run.
The API key is ELEVENLABS_API_KEY (environment or keys.env, found by walking up from the current folder).
It is never printed. Results: AUDIO_DIR/voice_report.json.
"""
import argparse, difflib, json, os, re, subprocess, sys, unicodedata, urllib.error, urllib.request
from pathlib import Path

API = "https://api.elevenlabs.io/v1"
DEFAULT_VOICE = {"voice_id": "", "model_id": "eleven_v4", "stability": 0.5, "similarity_boost": 0.75,
                 "style": 0.0, "use_speaker_boost": True, "output_format": "mp3_44100_128"}
MAX_RETAKES = 2
MIN_MATCH = 0.85
LETTER_WORDS = ("ai", "uae", "ula")  # Whisper writes "AI"; the script says "A I"


def find_up(name):
    p = Path.cwd().resolve()
    for d in [p, *p.parents]:
        if (d / name).exists():
            return d / name
    return None


def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    kf = None if k else find_up("keys.env")
    if kf:
        for line in kf.read_text().splitlines():
            if line.strip().startswith("ELEVENLABS_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not k:
        sys.exit("ELEVENLABS_API_KEY not found: add it to keys.env in the project root.")
    return k


def http(method, url, body=None, accept="application/json"):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": api_key(), "Content-Type": "application/json", "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs error {e.code}: {e.read().decode(errors='replace')[:400]}")


def settings(voice=None):
    s = dict(DEFAULT_VOICE)
    sf = find_up("settings.json")
    if sf:
        s.update(json.loads(sf.read_text()).get("voice", {}))
    if voice:
        s["voice_id"] = voice if re.fullmatch(r"[A-Za-z0-9]{20}", voice) else voice_by_name(voice)
    if not s.get("voice_id"):
        sys.exit("No voice set: add settings.json -> voice.voice_id in the project root, or pass --voice.")
    return s


def voice_by_name(name):
    vs = json.loads(http("GET", f"{API}/voices")).get("voices", [])
    hits = [v for v in vs if v["name"].lower().startswith(name.lower())]
    if len(hits) != 1:
        sys.exit(f"{len(hits)} voices match '{name}': " + ", ".join(f"{v['name']} ({v['voice_id']})" for v in hits))
    return hits[0]["voice_id"]


def clips(scripts_dir, only=None):
    files = sorted(Path(scripts_dir).glob("*.txt"))
    if only:
        want = {x.strip() for x in only.split(",")}
        files = [f for f in files if f.stem in want]
    if not files:
        sys.exit(f"No matching .txt scripts in {scripts_dir}")
    return [(f.stem, " ".join(f.read_text().split())) for f in files]


def tts(text, s, out):
    vs = {k: s[k] for k in ("stability", "similarity_boost", "style", "use_speaker_boost") if k in s}
    if s.get("speed"):
        vs["speed"] = s["speed"]
    body = {"text": text, "model_id": s["model_id"], "voice_settings": vs}
    if s.get("seed") is not None:
        body["seed"] = s["seed"]
    out.write_bytes(http("POST", f"{API}/text-to-speech/{s['voice_id']}?output_format={s['output_format']}", body, "audio/mpeg"))


# ---------- checks ----------
_model = None
ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
        "sixteen seventeen eighteen nineteen").split()
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def spell(n):
    if n < 20:
        return [ONES[n]]
    if n < 100:
        return [TENS[n // 10]] + ([ONES[n % 10]] if n % 10 else [])
    if 1100 <= n <= 1999 and n % 100:
        return spell(n // 100) + spell(n % 100)
    w = []
    if n >= 1000:
        w += spell(n // 1000) + ["thousand"]; n %= 1000
    if n >= 100:
        w += [ONES[n // 100], "hundred"]; n %= 100
    return w + (spell(n) if n else [])


def words(s):
    """Lower-case word tokens. Whisper's digits become spoken words and 'AI' / 'U.S.' become letters,
    so they match a script written for the voice ('forty', 'A I', 'U S')."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().replace("-", " ")
    s = re.sub(r"\b([a-z])\.", r"\1 ", s)
    out = []
    for t in re.findall(r"[a-z0-9']+", s):
        if t.isdigit() and len(t) <= 4:
            out += spell(int(t))
        elif t in LETTER_WORDS:
            out += list(t)
        else:
            out.append(t)
    return out


def load(path, sr):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def similarity(a, b):
    # "us" is ambiguous (the word vs the letters U S), so also compare with both readings removed
    plain = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    drop = lambda ws: [w for w in ws if w not in ("u", "s", "us")]
    return max(plain, difflib.SequenceMatcher(None, drop(a), drop(b), autojunk=False).ratio())


def check(path, text):
    global _model
    import numpy as np, librosa
    from faster_whisper import WhisperModel
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = _model.transcribe(load(path, 16000), language="en", beam_size=5)
    heard = " ".join(x.text for x in segs).strip()
    y = load(path, 22050)
    parts = librosa.effects.split(y, top_db=35)
    sp = np.concatenate([y[i:j] for i, j in parts]) if len(parts) else y
    return {"heard": heard, "match": round(similarity(words(text), words(heard)), 3), "dur_s": round(len(y) / 22050, 2),
            "speech_dbfs": round(float(20 * np.log10(np.sqrt(np.mean(sp ** 2)) + 1e-9)), 1),
            "peak": round(float(np.max(np.abs(y))), 3)}


def report(out, results):
    import statistics
    if len(results) > 1:
        med = statistics.median(r["speech_dbfs"] for r in results.values())
        for r in results.values():
            r["loudness_off_db"] = round(r["speech_dbfs"] - med, 1)
    flags = []
    for name, r in results.items():
        if r["match"] < MIN_MATCH:
            flags.append(f"{name}: transcript match {r['match']} < {MIN_MATCH} (heard: \"{r['heard']}\")")
        if abs(r.get("loudness_off_db", 0)) > 3:
            flags.append(f"{name}: {r['loudness_off_db']:+} dB from the other clips")
        if r["peak"] >= 0.99:
            flags.append(f"{name}: clipping (peak {r['peak']})")
    (out / "voice_report.json").write_text(json.dumps({"clips": results, "flags": flags}, indent=2))
    for name, r in results.items():
        print(f"  {name:10} {r['dur_s']:6.2f} s  match {r['match']:.2f}  {r['speech_dbfs']:6.1f} dBFS")
    print("flags:" if flags else "no flags", *flags, sep="\n  ")
    return flags


# ---------- commands ----------
def cmd_voices(a):
    for v in json.loads(http("GET", f"{API}/voices")).get("voices", []):
        labels = v.get("labels") or {}
        print(f"{v['voice_id']}  {v['name']}  [{v.get('category')}]  " + ", ".join(str(x) for x in labels.values() if x))


def cmd_plan(a):
    s = settings(a.voice)
    cs = clips(a.scripts)
    print(f"voice {s.get('voice_name', '')} {s['voice_id']} · model {s['model_id']} · stability {s['stability']} "
          f"· similarity {s['similarity_boost']} · style {s['style']}")
    for n, t in cs:
        print(f"  {n:10} {len(t):5} chars  {len(t.split()):4} words")
    print(f"total {sum(len(t) for _, t in cs)} characters (≈ credits)")


def cmd_generate(a):
    s = settings(a.voice)
    cs = clips(a.scripts, a.only)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    todo = {n for n, _ in cs if a.force or not (out / f"{n}.mp3").exists()}
    if not todo:
        print("all clips exist (use --force to redo)")
    elif not a.yes:
        chars = sum(len(t) for n, t in cs if n in todo)
        sys.exit(f"{len(todo)} clips, {chars} characters. Re-run with --yes to spend the credits.")
    results = {}
    for n, t in cs:
        p = out / f"{n}.mp3"
        if n in todo:
            for take in range(MAX_RETAKES + 1):
                print(f"generating {n} (take {take + 1}) ...", flush=True)
                tts(t, s, p)
                r = check(p, t)
                if r["match"] >= MIN_MATCH:
                    break
                print(f"  match {r['match']}: retaking", flush=True)
        else:
            r = check(p, t)
        results[n] = r
    report(out, results)


def cmd_check(a):
    out = Path(a.out)
    results = {n: check(out / f"{n}.mp3", t) for n, t in clips(a.scripts) if (out / f"{n}.mp3").exists()}
    report(out, results)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("voices")
    p = sub.add_parser("plan"); p.add_argument("scripts"); p.add_argument("--voice")
    g = sub.add_parser("generate"); g.add_argument("scripts"); g.add_argument("--out", required=True)
    g.add_argument("--only"); g.add_argument("--force", action="store_true"); g.add_argument("--yes", action="store_true")
    g.add_argument("--voice")
    c = sub.add_parser("check"); c.add_argument("scripts"); c.add_argument("--out", required=True)
    a = ap.parse_args()
    {"voices": cmd_voices, "plan": cmd_plan, "generate": cmd_generate, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    main()
