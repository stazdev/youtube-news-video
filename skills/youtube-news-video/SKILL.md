---
name: "youtube-news-video"
description: "Use when the user wants a YouTube news episode: research the latest stories, write ElevenLabs voice scripts, then build the cinematic animated long-form video and 2 Shorts from their audio."
---

# YouTube News Video

This skill produces one news episode in two phases:

- **Phase 1:** research the stories, write the scripts and YouTube metadata, then stop and wait for the user's audio.
- **Phase 2:** the user uploads their ElevenLabs clips. Build the long-form video, 2 Shorts and a thumbnail in the cinematic motion style described below.

Always say which phase you are in. If the user uploads audio clips named like the ones below, go straight to Phase 2.

## Engine and house rules (bundled; this skill is standalone)

This skill needs no other skill. Everything it uses ships inside it (`<skill>` is this skill's folder); **don't use a separately installed documentary-animation, video-making, frontend-design or dataviz skill**, even if one is available.

- **Engine manual:** `<skill>/references/engine.md`, a frozen copy of the documentary-animation build pipeline (v16). Read it before Phase 2 and follow these sections unless this file says otherwise: One-time setup (Remotion, Three.js via `@remotion/three`, Drei, postprocessing, GSAP, motion blur), Determinism, Timing (1, 1b: Whisper word timings, `timeline.json`, librosa), Camera library (5a-2), Smoothness toolkit (5), Three.js rules (6), Preview → review → final (7), Sound, grade and assembly (8), Shorts (8a), Captions (8b) and Quality checks. Ignore its house style (5a) and its Midnight Rose brand: the **Cinematic Desk** look and the brand below win.
- **Scripts** (`<skill>/scripts/`, run with the project's `.venv/bin/python -I`): `render_scan.py` (blank, black or frozen frames), `beat_sheet.py`, `check_shotlist.py`, `check_palette.py`, `check_frames.py`, `cam_track.mjs`, `eleven_sfx.py` (ElevenLabs sound effects, only with the user's OK on credits), `eleven_voice.py` (only if the user asks Claude to generate the narration), `ref_frames.py`, `track_motion.py`, `fit_easing.py`, `motion_compare.py`.
- **References** (`<skill>/references/`): `director.md` + `camera_bible.md` (shot choice and the director self-check), `composition_decider.md`, `hero_checklist.md`, `living_motion.md`, `reference_matching.md`, `subframe_accumulation.md` (depth of field when postprocessing `DepthOfField` renders blank).

**Rendering and encoding (house rules).**
- Long form 1920×1080 at 30 fps; Shorts 1080×1920; H.264 (`-c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow`), AAC 320 kbps at 48 kHz, `-movflags +faststart`. Render with Remotion, mix and mux with FFmpeg; never re-encode a finished video twice.
- Render a draft at `--scale=0.5` first, check it, then the final. Measure render time on a short test range before quoting a total.
- Every frame comes from `useCurrentFrame()`; no CSS animations, timers or unseeded randomness.

**Typography and layout (house rules).**
- One display serif with an italic for headlines and hero words, Inter for everything else; loaded from local font files, never from a CDN at render time.
- Keep text inside the title-safe area (5 % margin on long form; Shorts: away from the top 15 % and bottom 20 %). Headlines at least 64 px on 1080p, labels at least 28 px, captions 44-56 px; strong contrast (ink on paper, paper on charcoal), never mid-grey text.
- One clear focal point per shot; align to a simple grid; generous spacing; no decorative elements that don't carry information.

**Charts, numbers and colour (house rules).**
- Pick the simplest honest chart: bars for comparisons (axis from zero), lines for change over time, one big number for a single figure. Label values directly instead of using a legend where possible; always show the unit and the source.
- Use the category accent for the series that matters and neutral greys for the rest; never more than 4 colours in one chart. Check contrast and colour-blind safety with `scripts/check_palette.py --hex "<colours>"`.
- Numbers on screen match the narration exactly (rounding included) and the source list.

---

## Brand (fill in once decided)

Until the user sets these, use the defaults below and keep them the same in every episode.

- **Channel name:** `[CHANNEL NAME]`. Use "Today's Briefing" as a placeholder.
- **Base palette:** paper `#F4EFE6`, ink `#141414`, desk charcoal `#26262B`, warm key light `#FFC98B`, cool fill light `#9DB8FF`.
- **Category accents** for tags, trails and color pops: WORLD `#2F6BFF`, TECH `#8B5CF6`, BUSINESS `#10B981`, SPORTS `#FF7A1A`, BREAKING/alert `#E63946`.
- **Type:** an expressive display serif with an italic (e.g. Instrument Serif or Fraunces, OFL) for headlines and hero words, plus Inter (already installed) for labels, body and captions. Load fonts from local files.
- **Intro:** a 5–8 s title sting with the date. **Outro:** 8–10 s with a subscribe prompt and a next-episode card.
- **Sign-on:** "Here's what's happening around the world today." **Sign-off:** "That's your briefing. Stay informed, and we'll see you next time."
- Once decided, record the brand in `theme.ts` and `channel_bible.md` (see the engine's Channel bible section) and never change it between episodes.

---

## Phase 1: Research

**Topics.** Cover world, tech, business and sports. Add others if there's major news, such as science, health, Africa/Nigeria or entertainment. Each episode has **at least 5 stories**, and at least 3 categories must be represented.

**Recency.** Use stories from the last 24–48 hours. Check today's date first and search using it.

**Sources.** Use reputable outlets from around the world, and prefer original reporting over aggregators.

- Wires: Reuters, AP, AFP
- General and world: BBC, Al Jazeera, The Guardian, NYT, Washington Post, DW, France 24, NHK World, Nikkei Asia, ABC (Australia), CBC
- Africa: Channels TV, Premium Times, The Punch, Nation (Kenya), News24, Daily Maverick
- Business: Bloomberg, Financial Times, WSJ, CNBC, The Economist
- Tech: The Verge, Ars Technica, TechCrunch, Wired
- Sports: BBC Sport, ESPN, The Athletic, Sky Sports, and official league or federation sites

**Verification rules.**

- Confirm every story with **at least 2 independent reputable sources**, or with 1 wire service plus the official primary source (a government statement, company filing or league site).
- Skip rumors, single-source scoops and stories that can't be confirmed. Label developing stories as "developing" and attribute contested claims ("according to…").
- Keep a source list with the outlet, headline, URL and publish date for every story.
- Stay politically neutral. Report what happened and what each side says, with no editorializing.
- Write everything in your own words. Never copy sentences from articles.

**Story selection.** Rank stories by importance and interest, and lead with the biggest one. Pick the **2 strongest, most visual stories as Short candidates**.

---

## Phase 1: Scripts

The user records **one ElevenLabs clip per segment**. Give each clip's spoken text in its own labeled block, with nothing but spoken words in it, and save each one as a .txt file with the exact name below.

| File | Content | Target length |
|---|---|---|
| `00_intro.txt` | Sign-on and a one-line teaser for the top 3 stories | 15–20 s (~40–50 words) |
| `01_story.txt` … `NN_story.txt` | One story each | 60–90 s (~150–220 words) |
| `99_outro.txt` | Quick recap and the sign-off | 15–20 s |
| `short_A.txt`, `short_B.txt` | Standalone condensed versions of the 2 Short stories, with a hook in the first 2 seconds | 40–55 s (~100–135 words) |

Aim for a long-form total of about 7–12 minutes.

**Writing for voice (ElevenLabs).**

- Use short sentences in a conversational anchor tone. Open with the headline fact, then the context, then why it matters.
- Write numbers the way they're spoken ("two point five billion dollars"). Spell out uncommon acronyms or write them phonetically. Avoid symbols, URLs and parentheses.
- Put phonetic hints for hard names in the scene plan, not in the clip text.
- Use commas and full stops for pacing, and "..." only for a deliberate pause.

**Scene plan.** For each story, list the shots with the spoken line each one matches, the camera move (`CAMERA:`), the hero word(s) that get kinetic type, the keyword ticks, and the sound cues. Use the Cinematic Desk shot vocabulary below.

---

## Phase 1: YouTube metadata

- **Title:** under 70 characters, factual, no clickbait. Give 3 options.
- **Description:** a 2–3 line summary, chapters (fill in exact times in Phase 2), a full **Sources** list with links, and a note that the visuals are animated graphics.
- **Tags:** 15–25 tags.
- **Shorts:** a title and description for each, plus 3–5 hashtags including #Shorts.

Deliver Phase 1 as one doc, then ask for the clips using the exact file names (`00_intro.mp3`, `01_story.mp3`, …, `99_outro.mp3`, `short_A.mp3`, `short_B.mp3`).

---

## Motion style: "Cinematic Desk"

The target is a physically lit 3D world rendered in code that feels filmed, not templated. The user's reference was a three.js/WebGL piece with these qualities: a paper sheet on a textured surface, window-light shadows sweeping across it, kinetic serif type with rainbow motion trails, checkboxes ticking on beat, a slow camera dolly, the paper folding into a paper plane, and a flight through giant 3D letters in a bright sky.

Take the ideas only. Never copy the reference's frames or text.

**World.** Each story is a printed news brief lying on a dark desk. The brief shows the category tag, date, a big headline in the display serif with one italic hero word, a short keyword checklist, and a small "Source: …" line.

**Light and depth.** These are what make it look premium.

- Use a soft warm key light through a **window-blind gobo** (a projected shadow pattern) that drifts slowly across the scene, plus a cool fill light. Turn on shadows, use PBR materials (paper roughness ~0.9), and add an HDRI or `Environment` light for realism.
- Ease the color temperature from cool to warm across a story to mark its arc.
- Postprocessing: `DepthOfField` with focus on the hero word, `Bloom` kept light, `Vignette`, very light `Noise` grain, and a touch of `ChromaticAberration` only on fast moves.

**Camera.** Every shot moves.

- Slow push-ins and dolly-tilts across the brief take 3–6 s with `Easing.inOut(Easing.cubic)`.
- Use a rack focus from the headline to the keywords.
- Use a fast whip or fly-through only for transitions, with motion blur.
- Nothing stays static for more than ~4 s.

**Kinetic type.**

- The headline types or slides in word by word, synced to the voice through the transcript or word timestamps.
- The hero word smears in with **colored motion trails** in the category accent plus 2 neighboring hues, then settles to ink.
- Keyword checkboxes tick on the exact spoken word, each with a soft click.
- Big numbers count up with a snap zoom.

**Signature transitions between stories.**

1. The brief **folds into a paper plane** (animated fold rig or morph) and flies off-frame.
2. The plane flies through the next category's world: giant extruded 3D letters of the category name (WORLD / TECH / BUSINESS / SPORTS) in a stylized setting with a color pop. Use clouds and sky for WORLD, a dark grid with glowing lines for TECH, rising extruded bars for BUSINESS, and stadium-line geometry with floodlight bloom for SPORTS.
3. The plane lands and unfolds into the next brief.

Keep each transition to 2–3 s. Vary the flight path every time, and vary the plane's entry angle per episode so it doesn't feel repetitive.

**Inside a story**, cut away from the brief to supporting 3D or 2.5D shots as the script needs: a lit globe with the location pin, an extruded chart, a timeline ribbon, or a quote card (quotes under 15 words, attributed). Then return to the brief.

**Intro sting:** shadows sweep across a blank sheet, the channel name inks on with trails, the date ticks in, and the camera pulls back. **Outro:** the brief folds into a plane that flies toward a subscribe card.

**Shorts (9:16):** use the same world with a tighter vertical framing and more camera energy. Put a hook headline in the first second, and keep word-synced captions in Inter Bold inside the safe zone (away from the top 15% and bottom 20%). End with the plane flying toward "Full briefing on the channel".

---

## Sound design

- **Voice first.** The voice is never time-stretched, and every segment lasts exactly as long as its clip (measure with ffprobe).
- **Sound kit**, built once and reused for a consistent channel sound (procedural via Tone.js/FFmpeg, or CC0/CC BY sounds with logged licenses):
  - paper rustle and fold for brief entrances and folds
  - a soft airy whoosh for camera moves and plane flights
  - a crisp pencil-tick for checkboxes
  - a typewriter-light click for type-ons
  - a short riser into story transitions
  - a low room-tone and ambience bed
  - a 3-note sonic logo for the intro and outro
- **Music:** a subtle news-style bed, either generated with a fixed seed and tempo or supplied by the user. Place transitions on beats with librosa, but the spoken word wins if they disagree.
- **Mix:** keep music 18–24 dB under the voice with sidechain ducking and sound effects sparse and soft. Normalize to about -14 LUFS (`loudnorm=I=-14:TP=-1.5:LRA=11`).

---

## Phase 2: Build

1. Read the engine sections listed at the top. Set up or reuse the Remotion project and build the reusable components once: `NewsBrief`, `GoboLight`, `KineticHeadline`, `TrailWord`, `CheckTick`, `PaperPlaneFold`, `CategoryWorld`, `GlobePin`, `BigNumber`, `QuoteCard`, `TitleSting`, `Outro`.
2. Measure the clips, transcribe them for word timings (faster-whisper), and build `timeline.json`.
3. Write the storyboard from the Phase 1 scene plan.
4. Render test stills at the busiest moments at full size and look at them. Check the light, focus, readability and that frames aren't blank.
5. Render:
   - the long-form video at 1920×1080, 30 fps (60 fps for the transition flights if render time allows), H.264 + AAC
   - 2 Shorts at 1080×1920
   - a 1280×720 thumbnail rendered as a still from the 3D world: the brief under dramatic light with a 3–5 word headline
6. Do the sound pass and mix (see Sound design), then assemble with FFmpeg and finalize the chapter timestamps.

**If npm packages can't be installed** (no network), fall back to the preinstalled tools: Chrome plus Playwright rendering HTML, Canvas and CSS 3D transforms frame by frame, then FFmpeg. Fake the light with layered gradient and gobo-shadow overlays, blur for depth of field, and grain. Tell the user the full 3D look needs package installs enabled.

**Visual rules.** These are always required.

- Use only original graphics generated in code.
- **Never** use news-outlet footage, photos, logos or screenshots. Never use photos or likenesses of real people, and never use team, league or brand logos. Show names as text.
- Credit sources as on-screen text and in the description.

---

## Final checks (before delivering)

- Re-check every fact, number, name and date against the source list.
- Watch sampled frames from every segment and transition:
  - text is sharp and readable, and nothing is cut off
  - focus lands on the hero word
  - there's no flicker and no blank WebGL frames
  - captions are in sync and clear of the Shorts UI zones
- Run the director self-check (`references/director.md`): every scene changes on a spoken beat, there's one clear focus per shot, and nothing is static for more than ~4 s.
- Confirm that the durations match the audio, every clip was used, and the loudness is about -14 LUFS.
- Deliver the long-form MP4, 2 Short MP4s, the thumbnail PNG and the final metadata.