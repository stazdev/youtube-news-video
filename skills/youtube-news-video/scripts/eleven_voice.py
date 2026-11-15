#!/usr/bin/env python3
"""ElevenLabs narration from the channel's production script.

Reads the "Voice script for Eleven v4" section of a production script (PDF, .txt or .md),
splits it into the named chunks (voice_01_ch0.mp3 ...), generates each chunk with the
channel voice, checks every take with Whisper and joins them with chapter gaps.

Run with the project's venv:  .venv/bin/python -I <skill>/scripts/eleven_voice.py <command> ...

  plan     <script>                         parse only, list chunks + character count (free)
  generate <script> --out DIR [--only ch0,ch3] [--force] [--yes] [--no-check]
                                            generate missing chunks (costs credits)
  check    <script> --out DIR               Whisper/loudness checks on existing chunks
  join     <script> --out DIR [--gap 1.3]   trimmed chunks + gaps -> DIR/voice.mp3 + voice_chunks.json

Voice settings come from settings.json -> "voice" (project root). A line in the script's
production notes overrides them for that video:
  VOICE: <voice id or name> [· stability 50 · similarity 75 · style 0 · model eleven_v4]
The API key is read from ELEVENLABS_API_KEY (environment or keys.env). It is never printed.
"""
import argparse, difflib, json, os, re, subprocess, sys, unicodedata, urllib.request, urllib.error
from pathlib import Path

API = "https://api.elevenlabs.io/v1"
DEFAULT_VOICE = {"voice_id": "", "model_id": "eleven_v4", "stability": 0.5, "similarity_boost": 0.75,
                 "style": 0.0, "use_speaker_boost": True, "output_format": "mp3_44100_128",
                 "chapter_gap_s": 1.3, "part_gap_s": 0.5, "max_retries": 2}
CHUNK_RE = re.compile(r"^\s*(voice_[A-Za-z0-9_]+\.mp3)\s*[:\-–—]\s*(.*)$")
END_RE = re.compile(r"^\s*(Checks after generating|Fact check|Upload pack|\d+\.\s+Fact check)", re.I)
FOOTER_RE = re.compile(r"^\s*(.*\(Production Script\)\s*|Page \d+ of \d+\s*)$")
TAG_RE = re.compile(r"\[([^\]]+)\]")


# ---------- project files ----------
def find_up(name, start=None):
    p = Path(start or os.getcwd()).resolve()
    for d in [p, *p.parents]:
        if (d / name).exists():
            return d / name
    return None


def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        kf = find_up("keys.env")
        if kf:
            for line in kf.read_text().splitlines():
                if line.strip().startswith("ELEVENLABS_API_KEY="):
                    k = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not k:
        sys.exit("ELEVENLABS_API_KEY not found: add it to keys.env in the project root.")
    return k


def read_text(path):
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8")


# ---------- parsing ----------
def unwrap(lines):
    """Undo PDF hard wraps: a line ending in a space (or a hyphen before a lowercase word) continues."""
    out = []
    for raw in lines:
        if FOOTER_RE.match(raw) or not raw.strip():
            if not raw.strip():
                out.append("")
            continue
        prev = out[-1] if out else ""
        if prev and (prev.endswith(" ") or prev.rstrip()[-1:] not in '.?!…:;"\')]’”' or prev.endswith("-")):
            out[-1] = (out[-1] if out[-1].endswith("-") else out[-1].rstrip() + " ") + raw.strip()
        else:
            out.append(raw.rstrip(" ") + (" " if raw.endswith(" ") else ""))
    return [l.strip() for l in out if l.strip()]


def parse_script(text):
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if re.search(r"voice script", l, re.I) and not CHUNK_RE.match(l)
                  and any(CHUNK_RE.match(x) for x in lines[i:i + 40])), None)
    if start is None:
        start = next((i for i, l in enumerate(lines) if CHUNK_RE.match(l)), None)
    if start is None:
        sys.exit("No voice chunks found (expected lines like 'voice_01_ch0.mp3 : cold open').")
    chunks, cur = [], None
    for l in lines[start:]:
        if END_RE.match(l):
            break
        m = CHUNK_RE.match(l)
        if m:
            cur = {"file": m.group(1), "label": m.group(2).strip(), "raw": []}
            chunks.append(cur)
        elif cur is not None:
            cur["raw"].append(l)
    for c in chunks:
        c["text"] = "\n".join(unwrap(c.pop("raw")))
        c["chars"] = len(c["text"])
        c["chapter"] = chapter_key(c["file"])

    # production notes: VOICE override, IPA fixes, listen-check words
    notes = "\n".join(lines[:start])
    full = re.sub(r"\s+", " ", text)
    ipa = {}
    for w, p in re.findall(r"([A-Za-z][\wáéíóúñü\-]+)\s*/\s*([^/,]{2,40}?)\s*/", full):
        p = p.replace(" ", "")
        if re.search(r"[ˈˌəɑɒɪʊʒʃθðŋɡːæɛɔ]", p):
            ipa[w] = p
    listen = []
    m = re.search(r"listen for (.+?);", full)
    if m:
        listen = re.findall(r"[\"“]([^\"”]+)[\"”]", m.group(1))
    override = {}
    vm = re.search(r"^\s*VOICE\s*:\s*(.+)$", notes, re.M)
    if vm:
        parts = [p.strip() for p in re.split(r"[·|,;]", vm.group(1)) if p.strip()]
        override["voice"] = parts[0]
        for p in parts[1:]:
            kv = re.match(r"(stability|similarity|style|model|speed)\s*[:=]?\s*(\S+)", p, re.I)
            if kv:
                k, v = kv.group(1).lower(), kv.group(2)
                if k == "model":
                    override["model_id"] = v
                else:
                    f = float(v)
                    override[{"similarity": "similarity_boost"}.get(k, k)] = f / 100 if f > 1 and k != "speed" else f
    return {"chunks": chunks, "ipa": ipa, "listen": listen, "override": override}


def chapter_key(fname):
    m = re.search(r"_ch(\d+)", fname)
    return m.group(1) if m else fname


# ---------- settings ----------
def voice_settings(plan):
    s = dict(DEFAULT_VOICE)
    sf = find_up("settings.json")
    if sf:
        s.update(json.loads(sf.read_text()).get("voice", {}))
    ov = dict(plan["override"])
    if "voice" in ov:
        v = ov.pop("voice")
        if re.fullmatch(r"[A-Za-z0-9]{20}", v):
            s["voice_id"], s["voice_name"] = v, ""
        else:
            s["voice_id"], s["voice_name"] = resolve_voice_name(v), v
    s.update(ov)
    if not s.get("voice_id"):
        sys.exit("No voice set: add \"voice\": {\"voice_id\": ...} to settings.json or a VOICE: line to the script.")
    return s


def http(method, url, body=None, accept="application/json"):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": api_key(), "Content-Type": "application/json", "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:400]
        sys.exit(f"ElevenLabs error {e.code}: {msg}")


def resolve_voice_name(name):
    data = json.loads(http("GET", f"{API}/voices?show_legacy=true"))
    hits = [v for v in data.get("voices", []) if v["name"].lower().startswith(name.lower())]
    if len(hits) == 1:
        return hits[0]["voice_id"]
    if not hits:
        sys.exit(f"No voice named '{name}' in this ElevenLabs account. Use the voice ID instead.")
    sys.exit("Several voices match '%s': %s. Use the voice ID." % (name, ", ".join(f"{v['name']} ({v['voice_id']})" for v in hits)))


def tts(text, s, out_path):
    url = f"{API}/text-to-speech/{s['voice_id']}?output_format={s['output_format']}"
    body = {"text": text, "model_id": s["model_id"],
            "voice_settings": {k: s[k] for k in ("stability", "similarity_boost", "style", "use_speaker_boost") if k in s}}
    if s.get("speed"):
        body["voice_settings"]["speed"] = s["speed"]
    if s.get("seed") is not None:
        body["seed"] = s["seed"]
    audio = http("POST", url, body, accept="audio/mpeg")
    Path(out_path).write_bytes(audio)


# ---------- checks ----------
_model = None


def load_audio(path, sr=16000):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def transcribe(path):
    global _model
    from faster_whisper import WhisperModel
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = _model.transcribe(load_audio(path), language="en", beam_size=5)
    return " ".join(s.text for s in segs).strip()


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.findall(r"[a-z0-9']+", s)


def word_present(word, heard_words):
    w = "".join(norm(word))
    for n in (1, 2):
        for i in range(len(heard_words) - n + 1):
            if difflib.SequenceMatcher(None, w, "".join(heard_words[i:i + n])).ratio() >= 0.75:
                return True
    return False


def check_chunk(path, chunk, plan):
    heard = transcribe(path)
    hw, spoken = norm(heard), norm(TAG_RE.sub(" ", chunk["text"]))
    issues = []
    # bracketed tag read aloud: tag words heard that the narration itself doesn't contain
    for tag in TAG_RE.findall(chunk["text"]):
        tw = [w for w in norm(tag) if len(w) > 3 and w not in spoken]
        if tw and sum(w in hw for w in tw) >= max(1, len(tw) // 2 + (len(tw) > 2)):
            issues.append(("tag_read", tag))
    for w in set(plan["listen"]) | set(plan["ipa"]):
        if "".join(norm(w)) in "".join(spoken) and not word_present(w, hw):
            issues.append(("word", w))
    ratio = difflib.SequenceMatcher(None, " ".join(spoken), " ".join(hw)).ratio()
    if ratio < 0.85:
        issues.append(("mismatch", f"{ratio:.2f}"))
    return {"heard": heard, "match": round(ratio, 3), "issues": issues, **loudness(path)}


def loudness(path):
    import numpy as np, librosa
    y = load_audio(path, 22050)
    parts = librosa.effects.split(y, top_db=35)
    speech = np.concatenate([y[a:b] for a, b in parts]) if len(parts) else y
    rms = float(np.sqrt(np.mean(speech ** 2)) + 1e-9)
    return {"dur_s": round(len(y) / 22050, 2), "speech_dbfs": round(20 * np.log10(rms), 1),
            "peak": round(float(np.max(np.abs(y))), 3)}


def apply_ipa(text, words, ipa):
    for w in words:
        if w in ipa:
            text = re.sub(rf"\b{re.escape(w)}\b", f"/{ipa[w]}/", text)
    return text


# ---------- commands ----------
def cmd_plan(a):
    plan = parse_script(read_text(a.script))
    s = voice_settings(plan)
    print(f"Voice: {s.get('voice_name') or ''} {s['voice_id']} · model {s['model_id']} · stability {s['stability']}"
          f" · similarity {s['similarity_boost']} · style {s['style']} · {s['output_format']}")
    total = 0
    for c in plan["chunks"]:
        total += c["chars"]
        flag = "  <-- over 2,500" if c["chars"] > 2500 else ""
        print(f"  {c['file']:<22} {c['chars']:>5} chars  {c['label']}{flag}")
    print(f"Total: {len(plan['chunks'])} chunks, {total:,} characters (about {total:,} credits, more for retakes).")
    if plan["ipa"]:
        print("IPA fixes:", ", ".join(f"{k} /{v}/" for k, v in plan["ipa"].items()))
    if plan["listen"]:
        print("Listen-check words:", ", ".join(plan["listen"]))
    if a.json:
        Path(a.json).write_text(json.dumps({"settings": s, **plan}, indent=2, ensure_ascii=False))


def selected(plan, only):
    if not only:
        return plan["chunks"]
    keys = {o.strip() for o in only.split(",")}
    return [c for c in plan["chunks"] if c["file"] in keys or c["file"][:-4].rsplit("_", 1)[-1] in keys]


def cmd_generate(a):
    plan = parse_script(read_text(a.script))
    s = voice_settings(plan)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    todo = [c for c in selected(plan, a.only) if a.force or not (out / c["file"]).exists()]
    chars = sum(c["chars"] for c in todo)
    if not todo:
        print("Nothing to generate (all chunks exist; use --force to redo)."); return
    if len(todo) > 1 and not a.yes:
        sys.exit(f"{len(todo)} chunks, {chars:,} characters. Re-run with --yes after the user approves.")
    rp = out / "voice_report.json"
    report = json.loads(rp.read_text()) if rp.exists() else {}
    for c in todo:
        dst = out / c["file"]
        text, tries, note = c["text"], 0, ""
        while True:
            print(f"Generating {c['file']} ({len(text)} chars){' ' + note if note else ''} ...", flush=True)
            tts(text, s, dst)
            if a.no_check:
                break
            r = check_chunk(dst, c, plan)
            tags = [v for k, v in r["issues"] if k == "tag_read"]
            words = [v for k, v in r["issues"] if k == "word"]
            if not (tags or words) or tries >= s["max_retries"]:
                break
            tries += 1
            if tags:
                note = "retake: a tag was read aloud"
                if tries == s["max_retries"]:  # last try: drop the offending tags
                    for t in tags:
                        text = text.replace(f"[{t}]", "")
            else:
                fix = [w for w in words if w in plan["ipa"]]
                if tries >= 2 and fix:
                    text, note = apply_ipa(text, fix, plan["ipa"]), "retake with IPA for " + ", ".join(fix)
                else:
                    note = "retake: check " + ", ".join(words)
        if not a.no_check:
            r["retakes"], r["text_sent"] = tries, (text if text != c["text"] else None)
            report[c["file"]] = r
            print(f"   match {r['match']:.2f} · {r['dur_s']} s · {r['speech_dbfs']} dBFS · issues: "
                  f"{', '.join(f'{k}:{v}' for k, v in r['issues']) or 'none'}")
    if not a.no_check:
        rp.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        energy_check(report)


def energy_check(report):
    vals = {f: r["speech_dbfs"] for f, r in report.items() if "speech_dbfs" in r}
    if len(vals) < 2:
        return
    import statistics
    med = statistics.median(vals.values())
    odd = [f"{f} ({v - med:+.1f} dB)" for f, v in vals.items() if abs(v - med) > 3]
    print("Energy check:", ("takes differ from the others: " + ", ".join(odd)) if odd else "all takes within 3 dB.")


def cmd_check(a):
    plan = parse_script(read_text(a.script))
    out = Path(a.out); report = {}
    for c in plan["chunks"]:
        p = out / c["file"]
        if not p.exists():
            print(f"  {c['file']}: missing"); continue
        r = report[c["file"]] = check_chunk(p, c, plan)
        print(f"  {c['file']}: match {r['match']:.2f} · {r['dur_s']} s · {r['speech_dbfs']} dBFS · peak {r['peak']} · "
              f"issues: {', '.join(f'{k}:{v}' for k, v in r['issues']) or 'none'}")
    (out / "voice_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    energy_check(report)


def cmd_join(a):
    import numpy as np, librosa, soundfile as sf
    plan = parse_script(read_text(a.script))
    s = voice_settings(plan)
    gap = a.gap if a.gap is not None else s["chapter_gap_s"]
    out, sr = Path(a.out), 44100
    pieces, timeline, t, prev = [], [], 0.0, None
    for c in plan["chunks"]:
        p = out / c["file"]
        if not p.exists():
            sys.exit(f"Missing {p}; generate it first.")
        y = load_audio(p, sr)
        _, (a0, b0) = librosa.effects.trim(y, top_db=40)
        y = y[max(0, a0 - int(0.08 * sr)): min(len(y), b0 + int(0.15 * sr))]
        if prev is not None:
            g = s["part_gap_s"] if c["chapter"] == prev else gap
            pieces.append(np.zeros(int(g * sr), dtype=np.float32)); t += g
        timeline.append({"file": c["file"], "label": c["label"], "start_s": round(t, 3), "end_s": round(t + len(y) / sr, 3)})
        pieces.append(y); t += len(y) / sr; prev = c["chapter"]
    wav = out / "voice.wav"
    sf.write(wav, np.concatenate(pieces), sr)
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", str(wav), "-b:a", "192k", str(out / "voice.mp3")], check=True)
    (out / "voice_chunks.json").write_text(json.dumps(timeline, indent=2, ensure_ascii=False))
    print(f"Joined {len(timeline)} chunks -> {out / 'voice.mp3'} ({t:.1f} s, chapter gap {gap} s, part gap {s['part_gap_s']} s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("script"); p.add_argument("--json")
    g = sub.add_parser("generate"); g.add_argument("script"); g.add_argument("--out", required=True)
    g.add_argument("--only"); g.add_argument("--force", action="store_true"); g.add_argument("--yes", action="store_true")
    g.add_argument("--no-check", action="store_true")
    c = sub.add_parser("check"); c.add_argument("script"); c.add_argument("--out", required=True)
    j = sub.add_parser("join"); j.add_argument("script"); j.add_argument("--out", required=True)
    j.add_argument("--gap", type=float)
    a = ap.parse_args()
    {"plan": cmd_plan, "generate": cmd_generate, "check": cmd_check, "join": cmd_join}[a.cmd](a)


if __name__ == "__main__":
    main()
