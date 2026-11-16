---
name: "youtube-news-video"
description: "Use when the user wants a YouTube news episode: research the latest stories, write the scripts, voice them (ElevenLabs with the user's key, their own ElevenLabs recordings, or a free local voice), then build the cinematic animated long-form video and 2 Shorts."
---

# YouTube News Video

This skill produces one news episode in two phases:

- **Phase 1:** ask how long the episode should be, research the stories, write the scripts and YouTube metadata, ask how the narration should be voiced, whether the user wants to upload images and whether they have a reference animation, then stop until the clips (and any images or reference) are ready.
- **Phase 2:** the clips come from ElevenLabs with the user's key, the user's own ElevenLabs recordings, or a free local voice (Kokoro), plus any images or reference. Build the long-form video, 2 Shorts (unless the user asks for none) and a thumbnail in the cinematic motion style described below.

Always say which phase you are in. If the user uploads audio clips named like the ones below, go straight to Phase 2.

## Engine and house rules (bundled; this skill is standalone)

This skill needs no other skill. Everything it uses ships inside it (`<skill>` is this skill's folder); **don't use a separately installed documentary-animation, video-making, frontend-design or dataviz skill**, even if one is available.

- **Engine manual:** `<skill>/references/engine.md`, the build manual for Phase 2: setup (Remotion, Three.js via `@remotion/three`, Drei, postprocessing, GSAP), determinism, channel bible and lessons, timing (Whisper word timings, `timeline.json`, librosa), direction and style frames, camera and smoothness, Three.js rules, preview → final, sound and mix, Shorts, captions and quality checks. Read it all before Phase 2.
- **Scripts** (`<skill>/scripts/`; Python ones run with the project's `.venv/bin/python -I`): `render_scan.py` (blank, black, flashing or frozen frames, loudness, phone sheet), `beat_sheet.py` (a still after every beat), `check_shotlist.py` (shot variety rules), `check_palette.py` (neon, chroma and contrast), `check_frames.py` (washed-out or oversaturated frames), `cam_track.mjs` (parked 3D cameras), `eleven_voice.py` (voices the clips with ElevenLabs or the free local Kokoro voice, and checks any clips with Whisper), `sync_check.py` (is the voice in sync with the picture? transcribes the final video and compares every word with the timeline), `eleven_sfx.py` (ElevenLabs sound effects, only with the user's OK on credits), and for reference matching `ref_frames.py` (frames and contact sheets), `track_motion.py` (one element's position, size and fade per frame), `fit_easing.py` (timing and easing of one move, as a Remotion line) and `motion_compare.py` (reference vs ours, pass within ±0.08 s).
- **References** (`<skill>/references/`): `director.md` + `camera_bible.md` (shot choice and the director self-check), `living_motion.md` (smooth paths, idle motion, no empty-frame transitions), `hero_checklist.md` (measurable checklists for the signature pieces), `reference_matching.md` ("make it move like this"), `subframe_accumulation.md` (depth of field and motion blur when postprocessing `DepthOfField` renders blank).

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
- Use the category accent for the series that matters and neutral greys for the rest; never more than 4 colours in one chart. Check neon, chroma and contrast with `scripts/check_palette.py --hex "<colours>"`, and never tell two series apart by red versus green alone (add a label or a pattern).
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

## Phase 1: Episode length

Unless the user already said how long the episode should be, ask first, as one multiple-choice question (AskUserQuestion), before any research:

| Option | Long form | Stories | Each story |
|---|---|---|---|
| Quick | about 2 minutes | 5 | 15-20 s (~40-50 words) |
| Standard | about 5 minutes | 5-6 | 40-50 s (~100-125 words) |
| Full | about 8-12 minutes | 6-8 | 60-90 s (~150-220 words) |
| Custom (Other) | whatever the user says | scale from the rows above | |

Use about 2.5 spoken words per second to turn a length into word counts. Keep the intro and outro at 8-10 s each for Quick and 15-20 s for the other lengths. The 2 Shorts are always 40-55 s whatever the length. Remember the choice for Phase 2 and say it back in one line.

---

## Phase 1: Research

**Topics.** Cover world, tech, business and sports. Add others if there's major news, such as science, health, Africa/Nigeria or entertainment. Each episode has the number of stories that fits the chosen length (at least 5 unless the user asks for fewer), and at least 3 categories must be represented.

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
| `00_intro.txt` | Sign-on and a one-line teaser for the top 3 stories | from the chosen length |
| `01_story.txt` … `NN_story.txt` | One story each | from the chosen length |
| `99_outro.txt` | Quick recap and the sign-off | from the chosen length |
| `short_A.txt`, `short_B.txt` | Standalone condensed versions of the 2 Short stories, with a hook in the first 2 seconds | 40–55 s (~100–135 words) |

Add up the word counts and check that the long form lands within about 10% of the chosen length; trim or expand stories, not the intro and outro, to get there.

**Writing for voice (ElevenLabs).**

- Use short sentences in a conversational anchor tone. Open with the headline fact, then the context, then why it matters.
- Write numbers the way they're spoken ("two point five billion dollars"). Spell out uncommon acronyms or write them phonetically. Avoid symbols, URLs and parentheses.
- Put phonetic hints for hard names in the scene plan, not in the clip text.
- Use commas and full stops for pacing, and "..." only for a deliberate pause.

**Scene plan.** For each story, list the shots with the spoken line each one matches, the camera move (`CAMERA:`), the hero word(s) that get kinetic type, the keyword ticks, and the sound cues. Use the Cinematic Desk shot vocabulary below.

---

## Phase 1: YouTube metadata

- **Title:** under 70 characters, factual, no clickbait. Give 3 options.
- **Description:** a 2–3 line summary, chapters (fill in exact times in Phase 2), a full **Sources** list with links, a note that the visuals are animated graphics, and photo credits when photos are used.
- **Tags:** 15–25 tags.
- **Shorts:** a title and description for each, plus 3–5 hashtags including #Shorts.

Deliver Phase 1 as one doc, then do the two steps below.

---

## Phase 1: Voice, images and reference animation (ask every episode)

Photos are allowed, including photos of real people (for example the leader, athlete or chief executive a story is about). Claude doesn't fetch photos itself: they come from the user.

1. Add an **image wish list** to the Phase 1 doc: for each story, 1-3 images that would help, each with a file name, what it should show and the line it goes with. Example: `img_02_a.jpg`: the finance minister at the budget briefing, for "presented the budget on Tuesday". Shorts reuse the same names.
2. Ask these questions in one AskUserQuestion call:
   - **"How should the narration be voiced?"** Options: "ElevenLabs with my API key" (most natural voice; uses the user's ElevenLabs credits), "I'll record them in ElevenLabs" (the user makes the clips by hand on elevenlabs.io), and "Free voice on this computer" (Kokoro, an open-source voice that runs locally: no account and no credits, a little less natural). Skip it when the user already chose earlier in the conversation, or `settings.json` → `"voice"` → `"engine"` records a standing choice. If the user asks for a free voice "with Whisper", explain in one line that Whisper only listens (it checks the clips) and offer Kokoro.
   - **"Would you like to upload images for these stories, or should I go ahead without them?"** Options: "I'll upload images" and "Go ahead without images".
   - **"Do you have a reference animation you'd like any part of the episode to move like (the intro, the transitions, the headline reveal, the Shorts hook…)?"** Options: "Yes, I'll send it" and "No, use the house style". Skip this question when the user already gave a reference or said no to one earlier in the conversation.
3. Follow the matching voice route in **Voice** below; only the "I'll record them" route asks the user for clips. Also ask for the images with the names from the wish list if the user chose to upload, and the reference clip (a video or GIF file, or a link, with the part they mean and which piece it's for) if they have one. Ask the user to send only images they have the right to use (their own, licensed, official handouts or press kits, or Wikimedia Commons with its licence) and to tell you the credit line for each.
4. If the user goes ahead without images, build every shot from code graphics as described below. Any missing image falls back the same way.
5. If the user goes ahead without a reference, use the Cinematic Desk motion as written below. A reference matched in an earlier episode is already built into its component, so don't ask about that piece again unless the user wants to change it.

### Voice
All three routes end with the same clips in `<episode>/audio/` (`00_intro.mp3`, `01_story.mp3`, …, `99_outro.mp3`, `short_A.mp3`, `short_B.mp3`) and the same automatic checks. The tool is `scripts/eleven_voice.py`, run from the project root with `.venv/bin/python -I`. Save the user's route in `settings.json` → `"voice"` → `"engine"` (`elevenlabs`, `manual` or `kokoro`) and use it again next episode without asking, unless they want to change it.

**Route 1: ElevenLabs with the user's API key**
- **Key check:** look for `ELEVENLABS_API_KEY=` in the project's `keys.env` (or the environment) without printing it. If another of the user's projects has one, offer to copy that one line across without showing it.
- **If there's no key, give the user these steps** (never ask them to paste the key into the chat):
  1. Sign in at elevenlabs.io and open **Developers → API Keys** (in the left sidebar; on older layouts it's under the profile menu), then click **Create API key**.
  2. Give it access to **Text to Speech** and **Voices** (read), and **Sound Effects** if they want sound effects made too. Copy the key.
  3. Open `keys.env` in the project folder with a text editor (create it if it doesn't exist) and add one line: `ELEVENLABS_API_KEY=` followed by the key, with no spaces or quotes. Save the file.
  4. Say "done". The key stays on their computer; `keys.env` is never shared, zipped or committed (add it to `.gitignore`).
  Then check it works with the free `voices` command.
- **Voice:** `settings.json` → `"voice"` (`voice_id`, `voice_name`, `model_id` `eleven_v4`, `stability` 0.5, `similarity_boost` 0.75, `style` 0, `output_format` `mp3_44100_128`). On the first episode, if no voice is set, list the library with `voices` (free), ask which to use and save it; never change it between episodes unless the user asks.
- **Run:** `plan <episode>/scripts` (free: clips and characters ≈ credits) → `generate <episode>/scripts --out <episode>/audio --yes`, adding `--only 00_intro,01_story,…` when the user wants only some clips (for example no Shorts). Choosing this route counts as the OK to spend the credits; give the character total in the report. Existing clips are skipped (`--force` redoes one).
- **Licence:** ElevenLabs voices in monetised videos need a paid ElevenLabs plan; remind the user once if unsure.

**Route 2: the user records them in ElevenLabs**
Give the user these steps, with the clip texts from the Phase 1 doc:
1. Sign in at elevenlabs.io and open **Text to Speech**.
2. Pick the channel voice (the same one every episode) and the same model as the channel settings (`settings.json` → `"voice"` → `model_id`, Eleven v4 by default). Keep the voice settings the same for every clip.
3. For each script file (`00_intro.txt`, `01_story.txt`, …), paste its text exactly as written, click **Generate**, listen, and regenerate if a name is misread.
4. **Download** each clip as MP3 and rename it to match its script exactly: `00_intro.mp3`, `01_story.mp3`, …, `99_outro.mp3`, `short_A.mp3`, `short_B.mp3`.
5. Upload them in the chat, or put them in `<episode>/audio/`, and say "done".
Then run `check <episode>/scripts --out <episode>/audio` and report the results.

**Route 3: free voice (Kokoro, runs on the user's computer)**
- Kokoro is an open-source text-to-speech model (Kokoro-82M, Apache-2.0, commercial use allowed). It runs offline after a one-time download of about 330 MB, needs no account and costs nothing. It sounds clear but less natural than ElevenLabs, and it can't copy a custom voice.
- **Which machine (ask once, then save it):** setup differs by machine. If Claude can run commands, detect it first (`uname -sm` on macOS/Linux, `[System.Environment]::OSVersion` or `echo %PROCESSOR_ARCHITECTURE%` on Windows) and put that answer first, marked "(Recommended)". Ask as one multiple-choice question (AskUserQuestion): **"Which device will make the video?"** Options: "Mac with Apple Silicon (M1-M4)", "Mac with Intel", "Windows PC", "Android phone or tablet" (Linux goes in "Other"). Save it in `settings.json` → `"machine"` (`mac-apple-silicon`, `mac-intel`, `windows`, `linux`, `android`) and don't ask again unless the user changes device.
- **One-time setup per machine (ask before installing; choosing this route with the install described counts as the OK).** Kokoro needs Python 3.10-3.12 (check the project's with `.venv/bin/python -V`; if it's older, make a separate voice environment `.venv-voice` with Python 3.12 and run `eleven_voice.py` with it for this route, leaving the project's environment untouched). Tell the user roughly how much will download (PyTorch and the voice model, about 1-2 GB in all; the model alone is about 330 MB).
  - **Mac with Apple Silicon:** `brew install espeak-ng`, then `python3.12 -m venv .venv-voice` and `.venv-voice/bin/pip install kokoro soundfile faster-whisper librosa`. Current PyTorch works; no pins needed.
  - **Mac with Intel:** the same, plus pins in the same install: `"torch==2.2.2" "numpy<2" "transformers==4.46.3" "numba==0.60.0" "llvmlite==0.43.0"` (PyTorch stops at 2.2.x on Intel Macs, newer transformers needs PyTorch 2.6, and newer llvmlite has no Intel Mac build). PyTorch and Whisper load clashing copies of OpenMP here, so the voice tool runs each Whisper check in its own process (already built in).
  - **Windows PC:** install Python 3.12 from python.org (tick "Add python.exe to PATH") and espeak-ng with the `.msi` installer from the espeak-ng releases page on GitHub (`github.com/espeak-ng/espeak-ng/releases`); FFmpeg with `winget install -e --id Gyan.FFmpeg`. Then `py -3.12 -m venv .venv-voice` and `.venv-voice\Scripts\pip install kokoro soundfile faster-whisper librosa`, and run the tool with `.venv-voice\Scripts\python -I`. An NVIDIA graphics card makes it faster but isn't needed.
  - **Linux:** `sudo apt install espeak-ng ffmpeg` (or the distro's equivalent), then the same venv and pip install as Apple Silicon.
  - **Android phone or tablet:** Kokoro (and the Remotion video build) can't run on the phone itself. Tell the user plainly and offer: (1) record the clips in the ElevenLabs app or website on the phone (Route 2) and upload them, with the build done in Claude's cloud workspace or on a computer; (2) Route 1 if the cloud workspace can reach the ElevenLabs API; or (3) the free voice in Claude's cloud workspace (a Linux machine, so use the Linux setup without `sudo apt`), which works only if that workspace can install packages and download the model from Hugging Face. Try it once; if the install or download is blocked, say so and fall back to (1).
- **Voice:** `voices --engine kokoro` lists the news-friendly voices (`am_michael` warm American male is the default; `bm_george` British male, `af_heart` American female, and others). Ask which to use on the first episode, and save `"engine": "kokoro"` and `"kokoro_voice"` (optionally `"kokoro_speed"`, default 1.0) in `settings.json`.
- **Run:** `generate <episode>/scripts --out <episode>/audio --engine kokoro` (no `--yes` needed: nothing is spent), with `--only …` as above. The tool turns spaced-letter acronyms ("A I", "U S") into dotted ones for Kokoro, which otherwise reads a lone "A" as the word "a".
- **Tuning:** Kokoro reads a little slower than ElevenLabs; if the long form runs more than 10% over the chosen length, raise `"kokoro_speed"` (1.1 is still natural) and re-voice, since it costs nothing. If it misreads a name, add its IPA to `"kokoro_lexicon"` (for example `{"Nvidia": "ɛnvˈɪdiə"}`); the script text stays unchanged.

**Checks (every route, automatic):** every clip is transcribed with Whisper and compared with its script; generated clips below 0.85 are retaken (at most 2 retakes). `voice_report.json` flags low matches, clips more than 3 dB louder or quieter than the others, and clipping. Read the transcript of anything under 1.00: a misspelt name ("Besant") is Whisper, a missing or changed word is the voice. Report every flag; the user decides whether to keep or redo a clip.

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
- **Pace follows the voice.** Measure the words per second of each clip (engine section 4b): calm delivery (≤ 2.3 words/s, long pauses) gets a new shot every 5-8 s and fast moves only on emphasis words; brisk delivery (≥ 2.8 words/s) gets a new shot every 2-4 s; anything in between sits in the middle. Breaking stories may run brisk even when the voice is calm.

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

**Inside a story**, cut away from the brief to supporting 3D or 2.5D shots as the script needs: a lit globe with the location pin, an extruded chart, a timeline ribbon, a quote card (quotes under 15 words, attributed) or a photo. Then return to the brief.

**Photos (when the user uploaded them).** Show each one as a glossy print in the same world: clipped to the brief or lying on the desk, lit by the same gobo and key light, with a slow push-in or a gentle slide across it (never a static slide). A full-frame photo is allowed for a hero moment, with the same grade and grain. Put a small credit line on it ("Photo: …") and a name caption for any person shown. Keep faces clear of captions, labels and the safe-zone edges. Never alter a person's face or body, and never put a real person into a scene they weren't in.

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

1. Read `references/engine.md`. Set up or reuse the Remotion project and build the reusable components once: `NewsBrief`, `GoboLight`, `KineticHeadline`, `TrailWord`, `CheckTick`, `PaperPlaneFold`, `CategoryWorld`, `GlobePin`, `BigNumber`, `QuoteCard`, `PhotoPrint`, `TitleSting`, `Outro`.
   **Hero checklists:** before building each signature piece (`TitleSting`, `PaperPlaneFold`, each `CategoryWorld`, `Outro`, the thumbnail and each Short's first 3 s), write its checklist with `references/hero_checklist.md`, or re-use the saved one if the piece already exists and isn't changing.
   **Reference animation:** if the user sent one, follow `references/reference_matching.md` before building the piece it's for: break it down, write the motion spec, build it into that component, and compare until every row passes (±0.08 s, at most 5 rounds). A link is downloaded only with the user's OK, into its own folder, and the reference is never published.
   If the user uploaded images, copy them into `anim/public/photos/`, check each one opens and is at least 1280 px on its long side (tell the user about any that are too small), and log each with its credit line in `sources/sources.csv`.
2. Measure the clips, transcribe them for word timings (faster-whisper), and build `timeline.json`.
3. Write the storyboard from the Phase 1 scene plan.
4. Render test stills at the busiest moments at full size and look at them. Check the light, focus, readability and that frames aren't blank.
5. Render:
   - the long-form video at the chosen length, 1920×1080, 30 fps (60 fps for the transition flights if render time allows), H.264 + AAC
   - 2 Shorts at 1080×1920
   - a 1280×720 thumbnail rendered as a still from the 3D world: the brief under dramatic light with a 3–5 word headline
6. Do the sound pass and mix (see Sound design), then assemble with FFmpeg and finalize the chapter timestamps.

**If npm packages can't be installed** (no network), fall back to the preinstalled tools: Chrome plus Playwright rendering HTML, Canvas and CSS 3D transforms frame by frame, then FFmpeg. Fake the light with layered gradient and gobo-shadow overlays, blur for depth of field, and grain. Tell the user the full 3D look needs package installs enabled.

**Visual rules.** These are always required.

- Everything on screen is original graphics generated in code, plus the photos the user uploaded.
- Photos of real people are fine when the user supplied them. Claude never takes photos, footage or screenshots from news sites itself, never edits a real person's face or body, and never makes a real person appear somewhere they weren't.
- Never use news-outlet logos, watermarks or broadcast footage, or team, league or brand logos. Show names as text.
- Credit sources and photos as on-screen text and in the description.

---

## Final checks (before delivering)

- Re-check every fact, number, name and date against the source list.
- Watch sampled frames from every segment and transition:
  - text is sharp and readable, and nothing is cut off
  - focus lands on the hero word
  - there's no flicker and no blank WebGL frames
  - captions are in sync and clear of the Shorts UI zones
- Every hero checklist is graded (yes / partial / no, measured or eyeballed) and every reference spec row passes, or the user has been told which rows still fail and why.
- Run the director self-check (`references/director.md`): every scene changes on a spoken beat, there's one clear focus per shot, and nothing is static for more than ~4 s.
- Confirm that the durations match the audio, the long form is close to the chosen length, every clip was used, and the loudness is about -14 LUFS.
- Run `scripts/sync_check.py <final.mp4> anim/src/data/timeline.json` on every final video (long form and Shorts) and fix any FAIL before delivering: a voice that runs ahead of or behind the picture can't be seen on still frames.
- Every uploaded photo is used where planned, credited on screen and in the description, and sharp at 1080p.
- Deliver the long-form MP4, 2 Short MP4s, the thumbnail PNG and the final metadata.