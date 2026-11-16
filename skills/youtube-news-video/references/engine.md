# Build engine (youtube-news-video)

This is the build manual for Phase 2. It is part of this skill and needs no other skill. `<skill>` means this skill's folder (its `scripts/` and `references/`). Where this file and `SKILL.md` disagree, `SKILL.md` wins.

**Stack**
- **Remotion** renders the video as React components. Every frame comes from `useCurrentFrame()`, so timing is exact and repeatable.
- **Three.js via `@remotion/three`** (React Three Fiber inside Remotion), with **Drei** helpers and **postprocessing**, builds the Cinematic Desk world: the desk, the brief, the gobo light, the paper plane, the category worlds and the globe.
- **D3** draws the charts and the map on the globe (Natural Earth data via `world-atlas`).
- **FFmpeg** mixes, grades and encodes. **faster-whisper** and **librosa** handle word timing and audio analysis.
- **Fallback:** if npm packages can't be installed, see "If npm packages can't be installed" in `SKILL.md`.

**Licence note:** Remotion is free for individuals and for companies of up to 3 people, including commercial use. Bigger companies need a paid Company License. Mention this once on first setup.

## 1. One-time setup
Check what is already there, and ask once before installing anything missing.
1. **Node.js LTS 18+** (`node --version`). macOS: `brew install node`. Windows: `winget install -e --id OpenJS.NodeJS.LTS`. Linux: the distro's `nodejs` package. If `node` isn't found after installing, the user quits and reopens the Claude app in the same folder and says "continue".
2. **Remotion project** in `anim/` (create it by hand; no interactive scaffolding):
   - `package.json` scripts: `"studio": "remotion studio"`, `"render": "remotion render"`, `"still": "remotion still"`.
   - Install, keeping **every `remotion` and `@remotion/*` package on exactly the same version**:
     - Core: `npm i remotion @remotion/cli @remotion/three @remotion/transitions @remotion/paths @remotion/noise @remotion/motion-blur @remotion/captions @remotion/media-utils react react-dom`
     - 3D: `npm i three @react-three/fiber @react-three/drei @react-three/postprocessing postprocessing`
     - Charts, globe, motion, sound: `npm i d3 topojson-client world-atlas gsap flubber tone`
     - Dev: `npm i -D typescript @types/react @types/three @types/d3 @types/topojson-client`
     Use versions of R3F, Drei and postprocessing that fit each other and the installed React (check peer dependencies; never force-install). Known-good set: React 19 + R3F 9 + Drei 10 + `@react-three/postprocessing` 3.x + `postprocessing` 6.x.
   - `src/index.ts` (`registerRoot`), `src/Root.tsx` (compositions), `remotion.config.ts`.
   - On **Remotion 4.x** set `Config.setChromiumOpenGlRenderer('angle')` (`swangle` if there's no usable GPU). Remotion 5+ picks this itself. The first render downloads Remotion's headless browser; that's expected.
3. **Python tools** in the project's `.venv`: `.venv/bin/pip install faster-whisper librosa soundfile numpy pillow`.
4. **ElevenLabs:** `ELEVENLABS_API_KEY=...` in `keys.env`, for the voice clips (`scripts/eleven_voice.py`, see "Voice (recorded by Claude)" in `SKILL.md`) and sound effects (only with the user's OK on credits). Voice settings live in `settings.json` → `"voice"`. The key never goes into the skill, a zip or chat output.
5. **Machine profile (write the user's machine into `settings.json` → `machine` on first setup; these defaults are for low-power machines with an integrated GPU):** keep 3D light: instancing, ≤ ~200k triangles on screen, one `<ThreeCanvas>` at a time, one shadow-casting light at most (bake or fake the rest), postprocessing only where `SKILL.md` asks for it; `--concurrency` 2-4; `angle` GL on Remotion 4, `swangle` if 3D frames come out black. Postprocessing `DepthOfField` often renders blank frames on integrated GPUs, so use sub-frame accumulation for real depth of field (section 6). Measure render time on a short range and tell the user the estimate before every final render.

## 2. Determinism (critical)
All motion comes from `useCurrentFrame()` via `interpolate`, `spring`, `Easing` and `@remotion/noise`. Never use CSS animations or transitions, Tailwind `animate-*`, `Date.now()`, unseeded `Math.random()`, timers, D3 `.transition()`, or R3F's `useFrame()` for animation.
- **GSAP:** build timelines with `paused: true` and drive them only with `tl.seek(frame / fps)`; never let GSAP's ticker run, never use ScrollTrigger.
- **Flubber** (shape morphs, e.g. the fold of the brief): `flubber.interpolate(a, b)(p)` with `p` from the frame.
- Seed every random value (`random('seed')` from `remotion`, or `@remotion/noise`).

## 3. Channel bible and channel lessons
- **`channel_bible.md`** (project root): the channel name, palette, fonts, intro/outro, sign-on/sign-off and recurring components. Read it before every episode. Create it from the Brand section of `SKILL.md` once the brand is decided, and never change it between episodes unless the user asks.
- **`channel_lessons.md`** (project root): one row per correction the user has ever given (date, what happened, their words, the rule it added). Read it before every episode, right after the bible; it overrides this skill's defaults. When the user corrects something, add a row the same day with their exact words and say in one line that you did. If a correction contradicts an older row, update that row.

## 4. Timing
- **Segments:** one per clip (`00_intro`, `01_story` … `99_outro`, and each Short on its own). Each segment lasts exactly as long as its clip (`ffprobe`); never time-stretch the voice. Copy the clips into `anim/public/voice/`.
- **Words:** transcribe every clip with faster-whisper (`word_timestamps=True`) → `anim/src/data/transcript.json`, with the wording corrected against the `.txt` script (names, numbers, spelling).
- **Beats:** pick the frames where something happens: each headline word, the hero word, each keyword tick, each number, each cutaway.
- **`anim/src/data/timeline.json`:** fps, total frames, and per segment `{id, category, startFrame, durationInFrames, beats: {name: frame}}`, with the 2-3 s transitions placed between segments. Components read all timing from this file; never hard-code times.

### 4b. Audio analysis (librosa)
Analyse once in a short script in the project's `tools/` folder, save to JSON and read the values per frame. Load with `librosa.load(path, sr=22050, mono=True)` and `hop_length = round(22050 / fps)`, so one step ≈ one frame.
- **Pauses** → `voice_pauses.json`: gaps between `librosa.effects.split(y, top_db=35)` regions. Snap a shot change to a pause's middle when one is within ~0.3 s, so cuts never land mid-breath.
- **Pace** → `voice_pace.json`: words per second per clip (from the transcript) and pause density. The Director uses it to set the cut rate (see "Pace follows the voice" in `SKILL.md`).
- **Emphasis** → `voice_emphasis.json`: per-word RMS against the segment median; words ≥ ~1.4× louder are candidates for hero words, snap zooms and big numbers.
- **Music beats** (when a music bed is used) → `music_beats.json` via `librosa.beat.beat_track`. Put transitions on a beat within ±3 frames of the narration beat; the spoken word wins if they disagree. For a generated bed, use its known tempo.
- **Audio checks** before the mix: silences over ~1.5 s inside a clip, clipping (samples ≥ 0.99) and clips with very different loudness. Report them to the user instead of silently fixing the voice.

## 5. Direction, storyboard and style frames
1. **Director pass:** follow `references/director.md` with `references/camera_bible.md`. Each story is one "chapter" in the shotlist and its first shot is the `opener`. Write `anim/direction/shotlist.json` with a reason per shot and run `.venv/bin/python -I <skill>/scripts/check_shotlist.py anim/direction/shotlist.json direction/camera_history.json` until it passes. After the user approves the episode, append its shots to `direction/camera_history.json` so later episodes stay different.
2. **Storyboard** `anim/storyboard.md`, per shot: time range, spoken line, shot line with camera-bible codes and reason, what's on screen (brief, cutaway, photo), hero word, ticks, numbers and sound cues.
3. **Style system** in `anim/src/theme.ts`: the brand palette and category accents, fonts (local files in `public/fonts/`, loaded with the FontFace API and `delayRender`/`continueRender`), light rig, materials and motion language (entrances `Easing.out(Easing.cubic)` over 0.4-0.8 s, camera moves `Easing.inOut(Easing.cubic)` over 3-6 s, stagger 2-4 frames). Check the palette with `.venv/bin/python -I <skill>/scripts/check_palette.py --hex "<colours>"`.
4. **Hero checklists and reference matching:** write or re-use a checklist for each signature piece (`references/hero_checklist.md`). If the user sent a reference animation, follow `references/reference_matching.md` for the piece it's for, and put its spec rows into that piece's checklist.
5. **Style frames (stop here once):** render one still per story at its busiest moment (`npx remotion still src/index.ts Episode out/style_01.png --frame=<n>`), put them on a contact sheet, run `check_frames.py` and the fresh-eyes critic (section 10), grade each hero checklist against its still, fix what they flag, then show the user (with the checklist grades and, for a matched piece, the last compare table) and wait for a go-ahead.

### Project structure
```
anim/
  direction/   shotlist.json, sfx_plan.json, checklist_<piece>.md
  ref/<name>/  reference frames, tracks, motion spec and compare reports (reference matching)
  ours/<name>/ our frames of the same window, for the comparison
  public/      voice/, photos/, fonts/, sfx/, hdri/, textures/
  src/
    index.ts  Root.tsx  theme.ts
    data/      transcript.json, timeline.json, voice_*.json, chart data (with sources)
    lib/       NewsBrief, GoboLight, KineticHeadline, TrailWord, CheckTick, PaperPlaneFold, CategoryWorld,
               GlobePin, BigNumber, QuoteCard, PhotoPrint, TitleSting, Outro, Captions, CameraRig
    three/     cameraPaths.ts (CAMERAS per shot), lights, materials, shaders/
    stories/   01_<slug>.tsx, 02_<slug>.tsx, …
    Episode.tsx   16:9 master
    Short.tsx     9:16 layout reusing the same parts
```
Design long form on a 1920×1080 canvas and Shorts on 1080×1920. `Root.tsx` registers `Episode`, `ShortA` and `ShortB`, with durations from `timeline.json`.

## 6. Camera and smoothness
**Camera library** (the full list is `references/camera_bible.md`; the Director picks from it). All values come from `useCurrentFrame()`.

| Move | Use for | How |
|---|---|---|
| Slow push-in | building focus on the headline | dolly forward 3-6 s, `Easing.inOut(Easing.cubic)` |
| Dolly-tilt across the brief | reading down the page | move along the brief while tilting from headline to keywords |
| Pull-back reveal | detail → whole brief or globe | start close on the detail, ease out |
| Orbit | globe, 3D chart | camera on an arc around the target, 20-90° per shot |
| Rack focus | headline → keywords | move the focus point over 15-25 frames |
| Snap zoom | a big number | 8-12 frames, `Easing.out(Easing.exp)`, hold, settle |
| Whip / fly-through | transitions only | fast move with motion blur, lands with a tiny overshoot |
| Breathing drift | any held shot | 1-2% noise-driven wander so nothing is static for more than ~4 s |

**Camera contract:** every 3D shot's camera comes from one pure function in `anim/src/three/cameraPaths.ts`: `export const CAMERAS: Record<string, (frame: number, fps: number) => {position: [x,y,z], target: [x,y,z], fov: number}>`, keyed by shot id, frame local to the shot. `CameraRig` only calls `CAMERAS[id](frame, fps)`. For a path through several keys use `flow()` from `references/living_motion.md` (never overshoots). One primary move per shot; labels appear after a move settles.

**Smoothness toolkit**
- **Motion blur:** `@remotion/motion-blur` `<CameraMotionBlur>` (~6-10 samples) on fast 2D moves only; don't wrap a `<ThreeCanvas>` in it. For 3D, use 60 fps on the flights when render time allows, or sub-frame accumulation.
- **Depth of field / soft shadows:** where postprocessing `DepthOfField` renders blank, use sub-frame accumulation (`references/subframe_accumulation.md`) on the hero moments; render time × N, so measure first.
- **Drei (static helpers only):** `Environment` (HDRI), `ContactShadows`, `Text`/`Text3D`, `RoundedBox`, `useTexture`. Avoid helpers that animate themselves (`Float`, `Sparkles`, animated `Cloud`, `Stars` with speed, `OrbitControls`); if one is needed, drive its values from the frame.
- **Shaders:** set a `uTime` uniform from `frame / fps` (gobo drift, sky, glowing grid lines). Never read the clock in a shader.
- **Living motion:** follow `references/living_motion.md`: transitions never pass through an empty or dark frame, nothing enters from scale 0, and held shots keep a tiny idle layer.

## 7. Three.js rules (avoid flicker and crashes)
- Wrap 3D in `<ThreeCanvas width={width} height={height}>` sized from `useVideoConfig()`, with explicit lights or an `Environment`.
- Drive every transform, camera value, material value and uniform from `useCurrentFrame()`.
- A `<Sequence>` inside a `<ThreeCanvas>` must use `layout="none"`.
- **Only one `<ThreeCanvas>` mounted at a time**; mount 3D per segment. Too many WebGL contexts crash renders.
- Load textures, HDRIs and photos with `delayRender`/`continueRender` so no frame renders before they're ready.
- Sharp output: pass the render scale as a prop and set the canvas `dpr` from it; check a 3D still at final size.
- If 3D frames come out black, check the GL renderer with `npx remotion gpu`.
- **Traps that blank whole frames:** one NaN pixel turns the frame black through `Bloom`, so clamp every `pow()` base and divisor in shaders (`pow(max(x, 1e-4), k)`); `smoothstep(a, b, x)` with `a > b` returns 0 on ANGLE, so write `1.0 - smoothstep(b, a, x)`; colours baked into vertex attributes ignore the material colour.

## 8. Preview, review, final
1. **Live preview:** offer `npm run studio` in `anim/` so the user can scrub and comment by story number.
2. **Draft** at half size: `npx remotion render src/index.ts Episode ../renders/drafts/<ep>_draft.mp4 --scale=0.5 --muted`, then add the voice with FFmpeg. Before showing it (you can't watch video, only frames):
   - **Beat sheet:** `.venv/bin/python -I <skill>/scripts/beat_sheet.py <draft.mp4> anim/src/data/timeline.json --out anim/out/beats` gives one labelled still just after every beat. Check each one against the storyboard and `channel_lessons.md`. For a transition, sample a range: `--every 0.2 --from A --to B`.
   - **Camera track:** `node <skill>/scripts/cam_track.mjs anim` prints each 3D shot's camera at each beat and flags "PARKED" beats. Fix them unless the shotlist marks a deliberate hold.
   - **Render scan:** `.venv/bin/python -I <skill>/scripts/render_scan.py <draft.mp4> --out anim/out/scan --timeline anim/src/data/timeline.json` reads every frame. Fix every FAIL (flashes, empty or dark runs, peaks over −1 dBFS); fix or explain every WARN; read `phone_sheet.png` to check everything still reads at phone size.
   Fix, re-render the affected frames (`--frames=<start>-<end>`), and repeat until a pass is clean. Then send the draft.
3. **Final:** 1920×1080 (Shorts 1080×1920) as in `SKILL.md`, unless the user asks for a different size. Render a high-quality master (`--codec=h264 --crf=12 --muted`), with `--concurrency` at about half the CPU cores. Tell the user the measured estimate first.

## 9. Sound, grade, assembly, Shorts and captions
**Sound effects.** Build the channel kit from `SKILL.md` once and reuse it. Two sources:
- **ElevenLabs sound effects** (only with the user's OK on credits): write `anim/direction/sfx_plan.json` with one entry per distinct sound `{id, prompt, duration, loop, influence}`. Run `.venv/bin/python -I <skill>/scripts/eleven_sfx.py plan anim/direction/sfx_plan.json` (free), show the user the total, then `generate … --out anim/public/sfx --yes`. Files land as `el_<id>.mp3` and are logged in `sources/sources.csv`. Monetised use needs a paid ElevenLabs plan; remind the user once if unsure.
- **Procedural (free, no licence):** FFmpeg synthesis (filtered noise for whooshes and room tone, enveloped sine blips for ticks and clicks, low sine chords for pads) or Tone.js rendered offline with a fixed seed and tempo. Log them as "generated".
Place every sound on its beat frame from `timeline.json`. ElevenLabs output peaks near 0 dBFS, so set levels in the mix: about −20 to −28 dB under the voice for beds, −12 to −18 dB for accents.

**Mix and encode.** Narration on top; music 18-24 dB under with `sidechaincompress` ducking; normalise to `loudnorm=I=-14:TP=-1.5:LRA=11`. Apply a light grade (`eq`/`colorbalance`) and very light grain (`noise=alls=3:allf=t`) in the same final encode as `SKILL.md`'s settings. Confirm with ffprobe: resolution, fps, and audio/video lengths match within a frame or two.

**Shorts.** Each Short is its own clip (`short_A`, `short_B`), not a cut of the long video. Rebuild it for 9:16 (never crop): subject centred, cameras reframed vertically, a new visual every 2-4 s.
- **Frame 0 is a finished picture** with the hook headline already on it: no fade from black (Shorts autoplay muted and use frame 0 as the thumbnail).
- The hook is fully on screen by 1.0 s: ≥ 84 px at 1080 px wide, ≥ 7:1 contrast (on a dark pill if the scene is busy), inside the safe zone.
- **Muted test:** from `beat_sheet.py --every 0.5 --from 0 --to 3 --width 360`, someone must be able to tell what the Short is about.
- Labels and numbers ≥ 56 px. Output `<ep>_short_A.mp4`, `<ep>_short_B.mp4` (H.264, 1080×1920) plus an `.srt` for each.

**Captions (burned in on the long video and both Shorts; `.srt` exported too).**
- Text: Whisper word times with wording corrected against the script; numbers exactly as spoken and as shown.
- Build: `Captions.tsx` with `@remotion/captions` `createTikTokStyleCaptions`, rendered per frame.
- Look: Inter SemiBold/Bold in paper `#F4EFE6` on a rounded ink pill (`rgba(20,20,20,0.72)`), the active word in the story's category accent; each page slides up 6-8 px in 4-6 frames; no bouncing or flashing.
- Long form: 44-52 px, max 2 lines, ~7 words per page, bottom of the pill ≥ 10% above the frame bottom. Shorts: 64-76 px, 2-4 words per page, at 62-70% of the frame height, ≥ 140 px clear on the right.
- Captions never cover the headline, numbers, photos' faces or the key action (move the pill up for that page); no captions during the intro sting and outro.
- A page stays at least 0.6 s and changes on phrase breaks; words light up within ±2 frames of being spoken.

## 10. Quality checks (before showing any render)
Render stills at each story's start, middle and end and at every beat, and look at them:
- **Text:** headlines ≥ 64 px, labels ≥ 28 px, captions 44-56 px, nothing meant to be read below 24 px; inside the safe areas; never overlapping; spelled right.
- **Reading time:** text holds completely still for at least max(1.5 s, 1.0 s + 0.3 s × words) once it has fully arrived; quote cards 2.5-4 s. When unsure, hold longer.
- Focus lands on the hero word; no blank or black WebGL frames, no flicker, nothing frozen mid-animation at segment ends.
- Photos: sharp at 1080p, credited on screen, no faces covered by captions or labels.
- Charts honest (bar axes from zero, units and source shown); numbers match the narration and the source list.
- `check_shotlist.py` passes and every shot matches its shotlist entry.
- Every hero checklist line is graded; a matched piece passes `motion_compare.py` and `fit_easing.py --vs` within ±0.08 s.
- **Frame colour check:** `.venv/bin/python -I <skill>/scripts/check_frames.py anim/out/style_*.png` flags washed-out, flat, oversaturated and neon frames.
- **Fresh-eyes critic:** start one subagent that has not seen the build. Give it only the style-frame contact sheet, the spoken line for each frame, the `theme.ts` palette and this rubric, and ask it to score each frame 1-10 on: one clear focus, composition and depth, colour against the brand, text readability, does the picture match the spoken line, and clichés (decorative glows or particles that mean nothing, purple gradients, generic stock-looking layouts). Fix every frame below 7 (one round), and tell the user its scores next to yours.
- **Say what was measured.** In every report, mark each check as **measured** (a script or command produced it) or **eyeballed** (you looked at a still). Never say a check passed if you didn't run it.

## Credits for borrowed methods
Ideas adapted (no code copied unless noted) from **stazdev/cutaway** (MIT): corrections ledger, beat sheets, camera track, three.js traps; **Leonxlnx/cook** (MIT): frame colour check, fresh-eyes critic, measured vs eyeballed, sub-frame accumulation; **win4r/video-director** (MIT): render-scan checks, text size and reading-time rules, the muted first-3-seconds test; **rossark0/rossark-motion-skill** (MIT): living-motion recipes, `flow()`, no scale-from-0 and no empty-frame transitions.
