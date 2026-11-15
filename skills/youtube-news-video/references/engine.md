<!-- Bundled engine guide for youtube-news-video. -->
> **About this file.** This is a frozen copy of the **documentary-animation** skill, **v16** (2026-11-15). It is bundled here so this skill works on its own: no separate documentary-animation skill is needed, and if one is installed, **don't use it** (it has changed since and follows a different channel's style).
> - Read it as the engine manual for the build. `<skill>` in this file means the **youtube-news-video** folder: its `scripts/` and `references/` hold the same files.
> - Where this file and `SKILL.md` disagree, `SKILL.md` wins. In particular, ignore this file's house style (5a: low-poly toon + flat vector) and its "Midnight Rose" channel brand, intro, outro, story themes and sign-off lines: the news channel uses the **Cinematic Desk** look and the brand in `SKILL.md`.
> - **Not bundled (science channel only):** the Midnight Rose brand pieces in `references/brand/`. The voice tool `scripts/eleven_voice.py` is included, but the user normally records the news clips in ElevenLabs themselves; use it only if they ask Claude to generate the narration.


# Documentary animation (no footage): Remotion + Three.js

Turns a **voiceover** plus **scene/video prompts** into a fully animated explainer video: 3D environments wherever a scene shows a place or a physical thing, 2D motion graphics for diagrams and text, 3D walkthroughs, maps, charts, equations and kinetic text, all built in code by Claude. No stock footage, no AI video generators, no real footage.

**Engines**
- **Remotion** (primary): videos written as React components; every frame is rendered from `useCurrentFrame()`, so timing is exact and repeatable. Used for all 2D work, layout, text, transitions and the final render.
- **Three.js via `@remotion/three`** (React Three Fiber inside Remotion), with **Drei** helpers and **postprocessing** effects: the default for every **environment** (landscapes, coasts, oceans, underwater, sky, caves, cities, rooms) and every physical object with volume (globes, planets, terrain, rocks, volcanoes, molecules, cells, machines, cut-away models). See **Depth decision** below.
- **Blender 4.5 LTS** (scripted, headless) for **hero 3D**: shots where lighting and materials must look better than real-time Three.js can (soft shadows, ambient occlusion, volumetric light, glass, realistic water); rendered to image sequences and layered into Remotion. Also the model-preparation tool for downloaded 3D models.
- **D3** for accurate animated maps (Natural Earth data) and data charts; **KaTeX** for maths and chemistry formulas.
- **Fallback:** if Node.js can't be installed, build scenes as plain HTML/SVG pages and render them frame by frame with Playwright Chromium + FFmpeg (same timing rules below).

Uses the Documentary Starter setup: the project's `.venv` Python, FFmpeg, faster-whisper, `settings.json`, `fonts/`. Sound effects come from **ElevenLabs sound effects** first (`scripts/eleven_sfx.py`, see 5b); Freesound/Openverse (via documentary-sourcing's keys and rules) and code-built sounds are the fallback, plus any sounds the user supplies.

**License note:** Remotion is free for individuals and for companies of up to 3 people, including commercial use. Bigger companies need a paid Company License. Mention this once on first setup.

## One-time setup
Check, and ask once before installing anything missing:
1. **Node.js LTS** (`node --version`, `npm --version`; need 18+):
   - Windows: `winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements`
   - macOS: `brew install node`
   - Linux: the distro's `nodejs` package or nodejs.org.
   If `node` isn't found after installing, the user fully quits and reopens the Claude desktop app in the same folder and says "continue".
2. **Remotion project** in `anim/` (create it once; don't use interactive scaffolding):
   - `package.json` with scripts `"studio": "remotion studio"`, `"render": "remotion render"`, `"still": "remotion still"`.
   - Install, keeping **every `remotion` and `@remotion/*` package on the exact same version**:
     - Core: `npm i remotion @remotion/cli @remotion/three @remotion/transitions @remotion/paths @remotion/shapes @remotion/noise @remotion/motion-blur @remotion/captions @remotion/media-utils react react-dom`
     - 3D: `npm i three @react-three/fiber @react-three/drei @react-three/postprocessing postprocessing`
     - Maps, charts, maths: `npm i d3 topojson-client world-atlas katex`
     - Motion, transitions, assets, physics, sound: `npm i gsap flubber @remotion/lottie lottie-web matter-js tone @phosphor-icons/core @tabler/icons lucide-static` (+ `npm i -D @types/matter-js`). `@remotion/lottie` follows the same-version rule as every `@remotion/*` package.
     - 3D physics (only when a video needs it): `npm i @dimforge/rapier3d-compat` (baking only; no live physics components).
     - Rive (only when a video uses a Rive rig, see 5b): `npm i @remotion/rive` (same-version rule as every `@remotion/*` package). Claude-built `.riv` files need the **Rive CLI** (install per rive.app/docs/cli/overview; check with `rive --version`) and, as a free fallback, the community **rive-mcp** server (github.com/odu33104/rive-mcp). Ask once before installing either.
    - Dev: `npm i -D typescript @types/react @types/three @types/d3 @types/topojson-client`
     Use versions of `@react-three/fiber`, `drei` and `postprocessing` that are compatible with each other and with the installed React (check their peer dependencies; don't force-install). Known-good set: React 19 + R3F 9 + Drei 10 + `@react-three/postprocessing` 3.x + `postprocessing` 6.x.
   - `src/index.ts` (`registerRoot`), `src/Root.tsx` (compositions), `remotion.config.ts`.
   - Check the version with `npx remotion versions`. On **Remotion 4.x**, set `Config.setChromiumOpenGlRenderer('angle')` in `remotion.config.ts` (use `swangle` if the machine has no usable GPU). **Remotion 5+** picks this automatically.
   - The first render downloads Remotion's own headless browser; that's expected.
3. **Blender 4.5 LTS** (GPL; everything rendered with it belongs to the user):
   - macOS: `brew install --cask blender` (Homebrew gives 4.5 LTS on Intel Macs, newer versions on Apple Silicon). Windows: `winget install -e --id BlenderFoundation.Blender`. Linux: blender.org.
   - Command line: `/Applications/Blender.app/Contents/MacOS/Blender` on macOS (`blender` on Windows/Linux). Check with `--version`, then run a 1-frame EEVEE test render (`-b -P test.py`) and note the seconds per frame for time estimates.
4. **Settings:** `final_resolution` in `settings.json` is only the pre-selected suggestion; the final resolution is **always asked** before the final render (step 7.4). Allowed: `1280x720`, `1920x1080`, `2560x1440`, `3840x2160`. Also respect `fps` (30 default; 60 for motion-heavy videos when the user agrees).
5. **Machine profile (write the user's machine into `settings.json` → `machine` on first setup; the defaults below are for low-power machines with an integrated GPU and no discrete GPU):** 3D environments are expected in most videos, so keep each 3D scene light rather than avoiding 3D: low-poly toon geometry, instancing, ≤ ~200k triangles on screen, one `<ThreeCanvas>` at a time, no shadow maps (fake contact shadows with a dark transparent disc), postprocessing only on hero shots; when asking for the final resolution (step 7.4), suggest 2K for mostly-2D videos and 1080p when more than about a third of the runtime is 3D, but always let the user choose; `--concurrency` 2–4; use `angle` for GL on Remotion 4 and fall back to `swangle` if 3D frames come out black; render finals overnight-friendly (tell the user the estimated time first); on Intel Macs Blender must be 4.5 LTS (the last version for them); render with **EEVEE** on the GPU, never Cycles for motion on CPU-only machines (far too slow; Cycles only for single stills like the thumbnail); keep Blender to short hero shots (about 5-10 s of screen time per video unless the user accepts an overnight render), measure one test frame first and tell the user the estimated render time before rendering a sequence. Measured on a sample low-power laptop with Blender 4.5.16 (simple scene, 960×540): EEVEE 16 samples with ray tracing ≈ 25 s/frame; **EEVEE fast preset** (4 samples, ray tracing off, 1 shadow ray, motion blur off) ≈ 6.5 s/frame; Workbench ≈ 0.5 s/frame; the first frame costs extra for shader compilation. So: block out and time Blender shots with **Workbench** previews, render drafts with the EEVEE fast preset at 50% scale, and render finals at the resolution the user chose in step 7.4 with 8-16 samples (at 1080p ≈ 30-60 s/frame, so 1 s of video ≈ 15-30 min; scale the estimate for other resolutions and tell the user).
6. **Audio analysis:** `librosa` and `soundfile` in the project's `.venv` (`.venv/bin/pip install librosa soundfile`; ISC and BSD licences). Pure Python, runs anywhere. Used by step 1b.
7. **ElevenLabs:** `ELEVENLABS_API_KEY=...` in `keys.env` (the key needs text-to-speech, voices and sound-effects access; narration in step 0a, sound effects in 5b) and a `"voice"` block in `settings.json` (see step 0a). The key never goes into the skill, a zip or chat output.
8. **Optional:** Remotion publishes official agent skills (best-practice guides for coding agents). With the user's OK, they can be added to `.claude/skills/` for extra reliability. This skill works without them.

## Direction system (always on)
Every video is planned by two built-in roles before anything is animated. Read both reference files in full at the start of every video:
- **Composition decider** (`references/composition_decider.md`): reads the title, script and voice and decides the whole look: format (3D-led / hybrid / 2.5D-led / 2D-led), each scene's depth (2D, 2.5D, 3D, Blender hero), environment, time of day, weather, characters, energy and the **colour script**. Colours are always beautiful and story-matched and **never neon unless the script explicitly asks for neon** (checked by `scripts/check_palette.py`). Output: `anim/direction/look.json` + `look.md`.
- **Director** (`references/director.md` + `references/camera_bible.md`): designs every shot with the playbook formula (movement + angle + shot size + lens + composition) from the 130-entry camera bible, chooses by the narration's moment and emotion, times each move to its spoken word, writes a reason for every shot, and makes every scene unique (no repeated combinations, rotating families, signature moves once, different chapter openers, no repeats from recent videos). Output: `anim/direction/shotlist.json` (checked by `scripts/check_shotlist.py`) and shot lines in the storyboard.
A camera, look or colour the user writes in the script (`CAMERA:`, `LOOK:`, colour words) always overrides both roles.

## Depth decision: 3D when needed (decide per scene, before the storyboard)
Videos must never look flat. For every scene, decide **3D**, **2.5D** or **2D** and write the choice and a one-line reason in the storyboard:
- **3D (default for places and things):** the scene shows an environment the viewer could stand in (beach, river valley, mountains, coast from above, open ocean, underwater, seafloor, sky and clouds, cave, city, room), the Earth or a planet, or a physical object whose shape matters (rock, volcano, vent, cell, molecule, organ, machine, building). Build it in Three.js with the 3D environment kit below and move a real camera through it.
- **3D hero (Blender):** a 3D scene where image quality is the point: close-ups of materials (wet rock, glass, crystals, water surfaces, skin of a model), volumetric light (god rays, underwater haze, smoke, steam), soft shadows and ambient occlusion that sell scale, the title or thumbnail shot, and the twist/payoff scene. Build it in Blender with the pipeline in **5d**. Everything else that is 3D stays in Three.js.
- **2.5D (when a full 3D build is too heavy or the scene is mostly illustration):** flat illustrated layers placed at real depths in 3D space (planes at z = -40 … 0 in a `<ThreeCanvas>`, or SVG layers with perspective transforms), with fog and a moving perspective camera, so parallax, scale and haze come from the camera, not from hand-tuned offsets.
- **2D (graphics only):** diagrams, charts, maps meant to be read flat, formulas, kinetic typography, chapter cards, titles, Big Numbers, comparisons. These sit as overlays on top of a 3D or 2.5D background whenever the scene also has a setting (hybrid), not on an empty flat backdrop.
- A flat-colour or simple-gradient background behind illustrated scenery is a failure; give it depth (3D or 2.5D) or replace it with a 2D graphics-only composition.
- The channel bible's limit on 3D scenes, if any, counts **3D hero shots** (heavy models, postprocessing, glass, physics), not light 3D/2.5D environments. If the bible clearly forbids 3D environments, follow the bible and tell the user.

### 3D environment kit (build once in `anim/src/three/env/`, reuse across videos)
- **Terrain:** noise-displaced `PlaneGeometry` (`@remotion/noise` `noise2D`, 2-3 octaves), flat-shaded toon, colour by height and slope (sand → grass → rock → snow in palette colours); carve rivers by lowering vertices along a spline; rocks as instanced, randomly scaled icosahedrons (detail 0-1).
- **Water / ocean:** a plane with a custom `ShaderMaterial` (`uTime` = frame / fps): 2-3 summed sine/noise waves for vertex height, fresnel-style colour from deep to light teal, foam where the surface meets the shore (depth or distance to terrain). Rivers are a ribbon mesh along a `CatmullRomCurve3` with scrolling UVs (offset = frame-driven) so the flow reads.
- **Sky and air:** a large inverted sphere with a vertical gradient shader; low-poly clouds from merged icosahedrons; sun as an unlit disc with a soft glow sprite; `fog` (linear) for atmospheric perspective, lighter and less saturated with distance.
- **Underwater:** blue-to-navy fog, god rays as additive transparent cones that sway with noise, drifting particles (instanced points), seafloor terrain, caustics as a scrolling noise texture on the floor.
- **Foliage and props:** instanced low-poly trees (cone + cylinder), bushes, houses, boats, built from primitives in palette colours.
- **People:** simple original low-poly figures from primitives, or 2D characters on a camera-facing plane inside the 3D scene.
- **Living motion:** every environment shows its processes happening, with the amplitudes and periods in `references/living_motion.md` (smoke and plumes rise and fade, water bobs and flows, plants sway, clouds drift, fire leans); transitions never pass through an empty or dark frame; nothing enters from scale 0; children trail parents by 2-4 frames.
- **Camera rig:** `CameraRig` that sets position, look-at and fov from props each frame (no `useFrame`); for a path through several key positions, prefer `flow()` per axis from `references/living_motion.md` (passes every key smoothly and never overshoots, so the camera can't dip through terrain); otherwise camera paths as `CatmullRomCurve3` (centripetal) sampled by eased progress; apply the camera library's moves (push-in, crane, orbit, fly-through, follow cam) in real 3D.
- **Labels in 3D:** project a 3D point to screen (`vector.project(camera)`) in the scene component and position the 2D HTML `Label` there, so labels track objects while the camera moves.
- **Lighting:** one warm key directional light, a cool fill, ambient 0.5-0.8; toon materials; emissive for lava, vents, screens.

## Channel brand system: "Midnight Rose" (approved 2026-11-13)
The channel's intro and outro are **fluid and slow**: soft word fades, liquid droplets that merge (SVG gooey metaball filter), a wobbling blob that morphs (Flubber) into the Curiosity Drop logo, one eased frame squeeze, no hard cuts, no fast pops. Reference implementation (approved; copy into each video's `anim/src/lib/`, change only the props): `references/brand/IntroFluid.tsx`, `references/brand/OutroFluid.tsx`, `references/brand/fonts.tsx`; sound mix recipe `references/brand/mix.py`; voice lines `references/brand/voice_script.md`.
- **Ground (every video, every scene's brand pieces):** ink `#0C0A0E`, plum `#1A1320`, cream text `#F6F1EA`. No navy/blue brand colour.
- **Story theme (per video):** the accent colours of the intro, outro, captions' active word, chapter cards, labels' dots, Big Numbers and Fact Badges come from the story, chosen by the composition decider (`look.json → story_theme`): `ocean` (sea-glass teal), `blood` (warm red: heart, body, medicine), `plants` (leaf green), `sand` (warm brown: deserts, rocks, soil), `space` (soft violet), `fire` (ember orange: heat, volcanoes, energy). Hex values are in `STORY_THEMES` in `IntroFluid.tsx` and in `composition_decider.md`; all pass `check_palette.py`.
- **Intro:** long form 9.07 s (272 frames @30) right after the cold open: "Ask why." soft fade → droplets → liquid merge → blob → drop logo → wordmark + episode question, **title held still ≈ 2 s** → soft fade. Shorts version 6.97 s (209 frames), same choreography, placed right after the Short's 1-2 s hook.
- **Outro:** long form 20 s: recap droplets with chapter icons → merge → logo → "There's science behind everything." → end screen (next question on the left; right half EMPTY for YouTube's end-screen elements) → fade. Shorts outro 5.5 s: sign-off → logo → "Follow for the next question".
- **Sound and icon kit (ElevenLabs sound effects + 3D icons, approved 2026-11-13):** all intro/outro sounds are the channel's own ElevenLabs generations, made from `references/brand/brand_sfx_plan.json` with `scripts/eleven_sfx.py`: warm ambient pad `el_brand_pad` (bed, seamless loop), theme under-beds `el_under_ocean` (ocean/water), `el_under_heartbeat` (blood), `el_under_leaves` (plants), sparkle `el_twinkle` (droplets appear), `el_liquid_merge` (liquid merge), `el_whoosh_soft` (peak on the blob morph), `el_logo_chime` (drop logo forms; replaces the old sonic logo). The approved files live in the user's `brand/midnight-rose/public/sfx/` (alternate takes in `alts/`): copy them into each video's `anim/public/sfx/`; regenerate from the plan only if they're missing. For a new story theme (sand, space, fire), add one under-bed to the plan (desert wind, soft cosmic hum, gentle crackling embers), generate it and add it to `UNDER_DB` in `references/brand/mix.py`. `mix.py` levels every clip, lands each sound's onset or peak on its visual beat (scaled ×1/1.3 for Shorts) and normalises to −14 LUFS. Recap icons are **3D** Microsoft Fluent Emoji (MIT): droplet, rock, water_wave, volcano, sun, cloud_with_rain, mountain, salt, anatomical_heart, drop_of_blood, seedling, desert, ringed_planet, fire, microscope, test_tube, shown inside the outro's liquid droplets (`ICON_FILE` in `OutroFluid.tsx`); fetch them with `references/brand/fetch_brand_assets.sh <anim dir> keys.env` (it also fetches the old Freesound set, now only a fallback) and log each in `sources/sources.csv` (see `references/brand/sources_log.csv`).
- **Voice:** the intro needs none. The outro uses the narrator's teaser line at the end of the narration ("Next time: …?") and the sign-off "There's science behind everything." starting 5.9 s into the long outro (Shorts: one line at 0.05 s). Give the user these lines in the ElevenLabs script when the narration doesn't contain them.
- **Pace rule for brand pieces:** smooth sine easing, no move or fade shorter than ~0.5 s, every title readable and still for ≥ 1.5 s before it leaves.
- These approved pieces override older channel-bible descriptions of the sting, outro and colours.

## Channel bible
If `channel_bible.md` exists in the project root, read it before every video and follow it: its structure, recurring elements (Curiosity Drop, Big Number, Fact Badge, chapter cards, Myth vs Fact), scene format, pacing rules, sound identity and never-list override the generic defaults in this skill. Build each recurring element once as a reusable component in `anim/src/lib/` (e.g. `CuriosityDrop.tsx`, `BigNumber.tsx`, `FactBadge.tsx`, `ChapterCard.tsx`, `TitleSting.tsx`) and reuse it unchanged in every video so the channel looks consistent.

## Channel lessons (corrections ledger; idea from stazdev/cutaway, MIT)
`channel_lessons.md` in the project root holds one row per correction the channel owner has ever given (date, what happened, their words, the rule it added). **Read it before every video, right after the channel bible; it overrides this skill's defaults.** Copy every relevant row into the storyboard's checks and into the hero checklists, and check the draft against all rows before showing it.
- The moment the user corrects something ("too fast", "no blue", "the cloud isn't shown"), add a row the same day with their exact words, and say in one line that you added it. If a correction contradicts an older row, update that row instead of adding a second one.
- If the file doesn't exist, create it with the header from this section and the first correction.

## Inputs
1. **Voiceover:** either a voice file from the user (copy it into `anim/public/voice.<ext>`), or the user's **production script** with a "Voice script for Eleven v4" section, from which step 0a generates the voice with ElevenLabs.
2. **Video prompts:** what should be on screen for each part. Any format; `[S01] …` markers are ideal. `VISUALS:` lines from documentary-story-flow or documentary-sourcing scripts work too.
3. Optional: style wishes ("flat vector", "isometric", "low-poly 3D", "chalkboard", "paper cut-out", "clay-like 3D"), resolution, fps, platform.

If a part of the narration has no prompt, design visuals from the narration itself and mark them as Claude's choice in the storyboard.

## Rules
- **Original art only.** Draw everything in code (SVG, CSS, procedural 3D geometry, shaders). No copyrighted characters, mascots, logos or recognizable brand designs; no tracing real artworks. Characters are simple original figures with a consistent design.
- **Outside assets:** only CC0/public domain, logged in `sources/sources.csv`:
  - **Poly Haven** (HDRI sky lighting, textures, models), **ambientCG** (textures), **Kenney** and **Quaternius** (low-poly models): all CC0.
  - **Natural Earth** map data (public domain), via the `world-atlas` package (TopoJSON built from Natural Earth) or downloaded directly.
  - Sound effects: generated with ElevenLabs (5b; the user's own generations, paid plan for commercial use). Music, and fallback SFX, via documentary-sourcing's rules (CC0 / CC BY / platform licenses; never NC or ND).
  - Scientific 3D models (anatomy, molecules, fossils, spacecraft) from the libraries in **Scientific model libraries** below, with their licenses checked per model.
  Prefer building it in code when that looks as good. CC BY assets are allowed with a credit line; CC BY-SA, NC and ND assets are not used unless the user explicitly approves after being told the consequences.
- **Accuracy:** diagrams, maps, charts, formulas and 3D models must be correct in what they claim (labels, borders for the period shown, order of steps, relative sizes where they matter, chart axes starting honestly). Check uncertain facts with web search and note the source in the storyboard. Historical maps need period-correct borders; say "approximate" on screen when they're approximate.
- **Determinism (critical):** all motion comes from `useCurrentFrame()` (via `interpolate`, `spring`, `Easing`, `@remotion/noise`). Never use CSS animations/transitions, Tailwind `animate-*` classes, `Date.now()`, `Math.random()` without a seed, timers, D3 transitions (`.transition()`), or React Three Fiber's `useFrame()` for animation.
- **Avoid generic "AI video" clichés** (list adapted from Leonxlnx/cook, MIT): purple/violet gradients or a default purple accent (the `space` story theme's soft violet is the only exception), glowing orbs, shockwave rings, decorative particles that mean nothing, long thin decorative lines, floating icons with no reason, "01 / 02 / 03" counters used as decoration, small all-caps monospace "eyebrow" labels, random serif fonts outside `theme.ts`, beige/grey washed-out frames, and cheap synth bells or rising-pitch whooshes in sound. Every element on screen must explain something or carry the story; if it's only decoration, cut it.
- Never print API keys.

## Workflow

### 0a. Voice from ElevenLabs (when the user gives a production script instead of audio)
The channel's production scripts contain a **"Voice script for Eleven v4"** section: chunks headed `voice_NN_chX.mp3 : <part>`, each opening with the narrator tag `[calm, warm, curious narrator]`, a few emotion tags, ellipses and line breaks for pacing, IPA in slashes for hard words, and a "Checks after generating" line. `scripts/eleven_voice.py` turns it into the narration. Run it with the project venv: `.venv/bin/python -I <skill>/scripts/eleven_voice.py <command>` from the project root.
- **Key and voice:** the key is `ELEVENLABS_API_KEY` in `keys.env` (never print it, never copy it into the skill or a project). The default voice is `settings.json` → `"voice"` (`voice_id`, `model_id` `eleven_v4`, `stability` 0.5, `similarity_boost` 0.75, `style` 0, `output_format` `mp3_44100_128`, `chapter_gap_s` 1.3, `part_gap_s` 0.5). The channel voice is **Daniel - Warm, Clear & Dynamic Guide** (`ynTHHllfDmGsZ3G8QJt9`). A line in the script's production notes overrides it for that video only: `VOICE: <voice ID or name> · stability 50 · similarity 75 · style 0 · model eleven_v4` (names are looked up in the user's ElevenLabs account; if several match, ask).
- **1. Plan (free):** `plan <script.pdf|.txt|.md> --json anim/direction/voice_plan.json`. Show the user the voice, model, settings, every chunk with its character count and the total (≈ credits), and the IPA fixes and listen-check words it found. Flag any chunk over 2,500 characters. **Ask before spending credits.**
- **2. Test chunk:** `generate <script> --out projects/<video>/voice --only ch0`, then let the user listen and approve the sound.
- **3. The rest, after a clear yes:** `generate <script> --out projects/<video>/voice --yes` (skips chunks that exist; `--force` or `--only ch3,ch6b` to redo). Never use the "v4 Enhance" behaviour or rewrite the narration; tags and text are sent exactly as written.
- **Automatic checks per take** (Whisper + librosa; results in `voice/voice_report.json`): a bracketed tag read aloud → retake, and on the last retake that tag is removed; a listen-check word missing or misheard → retake, then the IPA from the script's notes is put in for that chunk only; transcript match below 0.85 is flagged; loudness of every take is compared and takes more than 3 dB from the others are flagged. At most 2 retakes per chunk. Report every flag and every IPA substitution to the user; they decide whether to keep or regenerate. `check <script> --out DIR` re-runs the checks on existing files (e.g. chunks the user made by hand).
- **4. Join:** `join <script> --out projects/<video>/voice` trims each chunk's edge silence and joins them with `chapter_gap_s` between chapters and `part_gap_s` between parts of one chapter (ch6a → ch6b), writing `voice.mp3` and `voice_chunks.json` (start/end of each chunk; use it to place chapter cards and check the timing in step 1). Copy `voice.mp3` into `anim/public/` and continue with step 0.
- If the user records chunks themselves in ElevenLabs, skip 2-3 and run `check` and `join` on their files.

### 0. Composition decision (before anything else)
Follow `references/composition_decider.md`: read title, script and voice (a quick librosa pass for pace and energy), decide format, per-scene depth/environment/characters, energy and the chapter colour script; write `anim/direction/look.json` and `look.md`; run `python3 <skill>/scripts/check_palette.py anim/direction/look.json` and fix any failure. `<skill>` is this skill's folder.

### 1. Timing
- Transcribe the voiceover with faster-whisper (`word_timestamps=True`, language and model from `settings.json`) → `anim/src/data/transcript.json`.
- Match each prompt to its stretch of narration. Each scene runs from its first word to the next scene's first word.
- Pick **beats** inside each scene: key words where something happens on screen ("sodium" → the sodium label pops).
- Write `anim/src/data/timeline.json`: fps, total frames, and per scene `{id, slug, startFrame, durationInFrames, beats: {name: frame}}`. Components read all timing from this file; never hard-code times.

### 1b. Audio analysis (librosa)
Analyse once, save to JSON, read per frame (same "bake, don't compute live" rule as physics). Script: `scripts/analyse_audio.py`, run with the project's `.venv` Python; load audio with `librosa.load(path, sr=22050, mono=True)` and use `hop_length = round(22050 / fps)` so one analysis step ≈ one video frame. Convert every time to frames with the composition fps.

- **Narration pauses** → `src/data/voice_pauses.json`: `librosa.effects.split(y, top_db=35)` gives the speech regions; the gaps between them are pauses. When a scene boundary from step 1 falls within ~0.3 s of a pause, snap it to the pause's middle so cuts never land mid-breath. Whisper stays the source of word timing.
- **Emphasis** → `src/data/voice_emphasis.json`: per-word loudness from `librosa.feature.rms` (averaged over each word's Whisper span) compared with the scene's median. Words ≥ ~1.4× louder are emphasis candidates for snap zooms, Big Numbers and pops; the storyboard still decides which ones get used.
- **Voice envelope** → `src/data/voice_rms.json`: one smoothed, 0–1 normalised RMS value per frame. Use for voice-reactive elements: a gentle pulse on the Curiosity Drop or waveform icons, a "speaking" glow on a narrator element, or mouth open/close for a simple character. Keep the effect subtle (scale ±3%, opacity ±15%).
- **Music beats** (when a music bed is used) → `src/data/music_beats.json`: `librosa.beat.beat_track(y=music, sr=sr, hop_length=hop, units='time')` for beat times and tempo. Prefer placing transitions, chapter cards and list pops on a beat that falls within ±3 frames of the narration beat; the spoken word always wins if they disagree. For generated (Tone.js/FFmpeg) beds, use the known tempo instead of detecting it.
- **Real sound visuals** (videos about sound, hearing or music) → `src/data/spectrum_<scene>.json`: a mel spectrogram (`librosa.feature.melspectrogram`, 32–64 bands, converted with `librosa.power_to_db`, normalised 0–1) for animated EQ bars or a scrolling spectrogram, and a pitch line from `librosa.pyin(y, fmin=65, fmax=400)` (NaN where unvoiced). Draw them in the house style. Label them as real data from the narration (or the demo sound), and keep axes honest (low notes left, high right; "pitch" not exact Hz unless the scene needs numbers).
- **Audio checks** before the final mix: flag silences longer than ~1.5 s inside narration, clipping (samples ≥ 0.99), voice chunks with very different loudness, and gaps or overlaps where voice files were joined. Report them to the user rather than silently fixing the voice.

Round values to 3–4 decimals; for long per-frame arrays, store `Float32Array` binaries instead of JSON. librosa only analyses audio: generating, mixing and loudness normalising stay in FFmpeg (step 8).

### 1c. Director pass
Follow `references/director.md`: classify each scene's moment, choose shots from `references/camera_bible.md`, time them to the beats from steps 1/1b, write `anim/direction/shotlist.json` with a reason per shot, and run `python3 <skill>/scripts/check_shotlist.py anim/direction/shotlist.json direction/camera_history.json` until it passes. After the user approves the final video, append its shots to `direction/camera_history.json` (project root) so the next videos stay different.

### 1d. Reference matching (when the user gives a reference animation)
"Make it move like this": an intro, transition, title reveal, chart animation or scene from a reference video or GIF. Follow `references/reference_matching.md`: break it down with `scripts/ref_frames.py`, measure cuts with `scripts/motion_compare.py` (self) and each element with `scripts/track_motion.py` + `scripts/fit_easing.py`, write the motion spec (one row per element per property), build it in our brand, then compare ours against the reference with `ref_frames.py --like` + `motion_compare.py` and `fit_easing.py --vs` until every row passes (±0.08 s; 2-5 rounds). Default fidelity is **motion-faithful**: timing, easing, order and overshoot match; art, colours and fonts stay ours. Never publish a pixel copy of someone else's design.

### 2. Storyboard + style
**Science terms (said and shown):** from the script, list 1-3 standard terms per chapter, the words a viewer would type into a search box ("chemical weathering", "hydrothermal vent", "evaporation"). Each one is shown on screen **at the moment the narrator says it** (a term label or Fact Badge in brand style, spelled exactly as the field spells it), held for its reading time, and the captions spell it the same way. Add a `terms` list per scene to the storyboard; the draft check confirms every term was both said (transcript) and shown (beat sheet). If the script explains an idea but never says its standard term, tell the user and suggest the line; never rewrite the narration yourself.

Write `projects/<name>/anim/storyboard.md`: per scene: id, time range, narration, chapter mood and palette (from look.json), shot lines with camera-bible codes and reasons (from shotlist.json), scene type, **depth (3D / 2.5D / 2D) with a one-line reason** (see Depth decision), **map / chart / formula** if any, look (5a-3, if any), what's on screen, camera move, beats, and planned sound effects.

Define the **style system** once in `anim/src/theme.ts`:
- Palette (background, 2–3 main colours, 1 accent, text colours with strong contrast), reused for 2D fills, chart colours, map fills and 3D materials.
- Fonts from `fonts/` copied into `anim/public/fonts/`, loaded with the FontFace API and `delayRender`/`continueRender` until loaded.
- Line weight, corner radius, shadow style, illustration style; for 3D: material type (toon vs standard), light rig, environment map, camera lens.
- Motion language: entrances `spring({damping: 200})` or `Easing.out(Easing.cubic)` over 0.4–0.8 s; camera moves `Easing.inOut(Easing.cubic)` over 1.5–4 s; pops with slight overshoot; stagger 2–4 frames.
- Look: the colour grade and grain settings used in the final pass (see step 8), so previews and finals match.

**Style frames before rendering:** render one still per scene at its key moment (`npx remotion still src/index.ts Documentary anim/out/style_S##.png --frame=<n>`), combine into a contact sheet (`anim/style_frames.png`), run the frame colour check and the fresh-eyes critic (see **Quality checks**), fix what they flag, then show the user and get a go-ahead or changes.

### 3. Project structure
```
anim/
  direction/         look.json, shotlist.json, sfx_plan.json, checklist_S##.md (hero checklists)
  public/            voice, fonts, sfx, CC0 assets (hdri/, textures/, models/)
  src/
    index.ts  Root.tsx  theme.ts
    data/            transcript.json, timeline.json, chart data (*.json with sources)
    lib/             easing helpers, seeded RNG, camera helpers, Label, Arrow, Counter, Caption, Formula
    scenes/          S01_<slug>.tsx, S02_<slug>.tsx, …
    three/           cameraPaths.ts (CAMERAS per scene), Globe, Planet, Terrain, Molecule, Lights, CameraRig, shaders/
    maps/            projections, MapLayer, RouteLine, RegionHighlight
    charts/          BarChart, LineChart, ScaleCompare, Counter
    Documentary.tsx  16:9 master: TransitionSeries of scenes
    Short.tsx        9:16 layout reusing the same scene parts
```

**Design canvas vs output size:** every composition is designed at **1920×1080** (Shorts at 1080×1920). Higher resolutions come from Remotion's `--scale` at render time (step 7), so layouts never change and vector art stays sharp.

`Root.tsx` registers `Documentary` (1920×1080, fps from settings, duration from `timeline.json`) and, whenever Shorts are made (always for videos over 5 minutes, see 8a), `Short1` and `Short2` (1080×1920). Each scene is its own component and starts its own local timeline at frame 0 inside a `<Sequence>`/`TransitionSeries.Sequence`.

### 4. Scene library
**2D (React + SVG):**
- **Title card:** mask reveal or letter stagger, subtle background drift.
- **Walkthrough (2D):** a large illustrated world bigger than the frame; a camera group pans/zooms point to point on the beats, with parallax layers.
- **Explainer diagram:** parts appear in narration order; arrows draw on with `@remotion/paths` (`evolvePath`); labels pop beside what they name; active part highlighted, others dimmed.
- **Process / cycle:** steps around a loop or path with a marker travelling between them.
- **Cross-section / zoom-in:** cut-away view, then a magnifier or continuous zoom into a detail.
- **Character moment:** simple original character blinks, tilts, points; sparingly.
- **Kinetic typography:** key phrase word by word on the beats.
- **Split / comparison:** two panels, wipe between before and after.
- **End card:** recap line, space for subscribe prompts (no third-party logos).

**Maps (D3 + Natural Earth):**
- Use `d3-geo` projections (e.g. `geoNaturalEarth1` for world views, `geoMercator`/`geoConicConformal` for regions; `geoOrthographic` for a 2D spinning-globe look) and `topojson-client` to turn `world-atlas` TopoJSON into SVG paths.
- Animate with frame-driven values only: projection rotate/scale/translate for camera moves; `evolvePath` for routes (trade routes, migrations, rivers, journeys); fill/opacity for regions lighting up; labels and markers popping on beats.
- Keep map styling on-theme: muted land, soft coastlines, accent colour for the subject; city dots and labels sized for 1080p readability.

**Charts (D3):**
- Use `d3-scale`, `d3-shape`, `d3-array` to compute geometry, and render it as SVG in React. Never use D3's DOM manipulation or `.transition()`; React renders, the frame drives the animation.
- Patterns: bars growing in sequence, lines drawing on with a moving end dot, numbers counting up beside them, scale comparisons (a tiny circle vs a huge one), stacked area reveals, before/after morphs.
- Honest charts: bar axes start at zero, labels on axes, units shown, data source as a small caption, data saved in `src/data/` with its source URL.

**Formulas (KaTeX):**
- Import `katex` and `katex/dist/katex.min.css`; render with `katex.renderToString(tex, {output: 'html', throwOnError: false})` into a container, and wait for KaTeX fonts with `delayRender` before the first frame.
- Animate by revealing terms in order (opacity/clip per part, using `\htmlClass` or separate KaTeX spans), highlighting the term the narrator mentions, and moving terms between steps of a derivation. Use `\ce{}` via KaTeX's mhchem extension for chemistry if needed.
- Formula size at least ~48 px at the design canvas; never more than two lines on screen at once.

**3D (`@remotion/three` + Drei + postprocessing), when depth genuinely helps:**
- **Globe / planet:** rotating Earth or planets from spheres with procedural or CC0 textures; camera flies to a region; markers and arcs appear on beats. Can share coordinates with the D3 maps for consistency.
- **Terrain fly-through:** procedural landscape (noise-displaced plane) with rivers, mountains, ocean; camera glides along a spline.
- **Cut-away model:** layered 3D object (Earth's layers, a volcano, a cell, an engine) that splits apart on the beats.
- **Molecules / particles:** atoms as spheres, bonds as cylinders; deterministic instanced particles for rain, bubbles, vapour, stars.
- **Isometric 3D:** orthographic camera, low-poly blocks, for "how things are made" and system walkthroughs.
- **Hybrid:** 3D background with 2D labels, arrows, formulas and captions layered on top in a normal `AbsoluteFill`.

**Transitions:** `@remotion/transitions` (`TransitionSeries` with fade, slide, wipe, or a custom zoom-through) and match cuts (a shape in one scene becomes the next scene). Avoid plain crossfades everywhere.

### 5. Smoothness and immersion toolkit
- **Motion blur:** wrap fast 2D camera moves, whip pans and quick pops in `@remotion/motion-blur` (`<CameraMotionBlur>`, ~6–10 samples; it multiplies render time for that section, so use it only where motion is fast). Use `<Trail>` for streaking objects. Don't wrap a `<ThreeCanvas>` in it (multiple WebGL renders); for 3D, rely on 60 fps and postprocessing instead.
- **60 fps:** for videos with many camera moves or fly-throughs (doubles render time). Keep 30 fps for calmer explainers.
- **Depth of field:** on integrated GPUs, postprocessing `DepthOfField` gives blank frames, so for real 3D depth of field, motion blur and soft shadows on **hero moments** use **sub-frame accumulation** (`references/subframe_accumulation.md`: render N sub-frames per frame with a jittered lens/time/light, average them with FFmpeg `tmix`; render time × N, measure first). In 2D, blur far parallax layers slightly (CSS `filter: blur()` set per frame); for cheap 3D depth, CSS `backdropFilter` blur bands over the far region.
- **Drei (static helpers only):** `Environment` with a Poly Haven HDRI for realistic lighting, `Sky`, `Stars` (speed 0), `ContactShadows`/`SoftShadows`, `Text3D`/`Text`, `RoundedBox`, `useGLTF`/`useTexture` for CC0 assets. **Avoid Drei helpers that animate themselves** (`Float`, `Sparkles`, animated `Cloud`, `Stars` with speed, `PresentationControls`, `OrbitControls`); if one is needed, drive its values from the frame.
- **Postprocessing** (`@react-three/postprocessing`, inside the `ThreeCanvas`): `Bloom` for lava, stars, screens and glowing labels; `Vignette`; `DepthOfField`; very light `Noise`. Render a test still at final scale to confirm it isn't blank or too slow before using it across a video.
- **Custom shaders:** `shaderMaterial`/`ShaderMaterial` with a `uTime` uniform set from `frame / fps` for moving water, drifting clouds, flowing lava, heat shimmer, glowing energy fields and stylized skies. Never read the clock inside a shader.
- **Animated captions:** always burned in, on the long video and on every Short; full rules in **8b**. The `.srt` is exported as well.
- **Audio-reactive touches (optional, subtle):** `useAudioData` + `visualizeAudio` from `@remotion/media-utils` to make a glow, particle field or background pulse gently with the music bed. Never distracting.
- **Sound design pass:** see step 8.

### 5a. House style: low-poly 3D worlds + flat geometric vector graphics, with grain (default)
Every video uses this look unless the user asks otherwise: environments and objects are low-poly toon 3D (or 2.5D layers in 3D space) in the palette below; diagrams, labels, numbers and text are flat geometric vector graphics layered on top. Put its values in `theme.ts`; if `anim/public/style_reference.png` exists (an image the user picked), sample its colours and shapes and adjust the values below to match it.

- **Shapes:** simple, bold geometric shapes; smooth two-stop gradients; **no outlines** on illustrations (outlines only for UI labels and icons); rounded corners where natural; soft long shadows at one consistent angle (≈ 35°, lower-right) drawn as darker, low-opacity shapes, never blurred drop shadows.
- **Palette:** scene and environment colours come from the composition decider's colour script (mood palettes, never neon unless the script asks). Recurring brand pieces (intro, outro, chapter cards, labels, captions, Big Numbers, Fact Badges) use the **Midnight Rose** ground (ink `#0C0A0E`, plum `#1A1320`, cream `#F6F1EA`) with the video's **story theme** accent (see Channel brand system). Max 5 colours plus neutrals per scene. Text is cream on dark or ink on light, never mid-grey.
- **Grain (signature texture):** a full-frame SVG noise overlay on every scene: `feTurbulence type="fractalNoise" baseFrequency≈0.8 numOctaves=3` → `feColorMatrix` to grey → blended at 6–10% opacity (`mix-blend-mode: overlay` or `soft-light`). Seed changes every 2 frames (`seed = Math.floor(frame/2)`) for a gentle living texture, or stays fixed for calmer videos. Grain also hides gradient banding, so the final FFmpeg grain (step 8) is reduced to `noise=alls=1:allf=t` or skipped.
- **Typography:** one signature display font for titles and big numbers, chosen once per channel from Google Fonts (OFL licence; loaded via local files in `public/fonts/`), with Inter for labels and captions. Record the choice in `theme.ts` and never change it between videos.
- **Depth:** 3–4 parallax layers per scene (far, mid, near, foreground) with lighter, less saturated colours further back.
- **3D in this style (most environment scenes):** match it: `MeshToonMaterial` or flat-shaded low-poly, palette colours only, soft single key light, the same grain overlay on top so 2D and 3D feel like one world.

### 5a-2. Camera library
The full library is `references/camera_bible.md` (130 movements, angles, shot sizes, compositions and lens guide); the Director picks from it. The table below is the quick reference for implementing common moves. Every scene declares its shots in the storyboard (`CAMERA:` / shot lines with bible codes). Implement 2D moves as transforms on a `CameraRig` group wrapping parallax layers (each layer gets a depth factor: far 0.3, mid 0.6, near 1.0, foreground 1.4); implement 3D moves on the Three.js camera. All values come from `useCurrentFrame()`.

| Move | Use for | How |
| --- | --- | --- |
| Slow push-in | building focus while explaining | scale 1.00 → 1.06–1.12 over the shot, `Easing.inOut(Easing.cubic)` |
| Pull-back reveal | detail → big picture | start scale 1.6–3 on the detail, ease out to 1.0 |
| Parallax truck | depth in flat scenes | translate X; each layer moves by its depth factor |
| Crane up/down | rising/sinking between levels (seafloor → surface) | translate Y with parallax, slight scale change |
| Continuous scale zoom ("Powers of Ten") | rock → mineral → crystal → atom | nested scenes, exponential zoom (scale = e^(k·t)); cross-fade each level as the next fills the frame; channel signature move |
| Zoom-through transition | into a cell/window/droplet → next scene | zoom into a shape until it fills the frame, then the next scene starts from inside it; pair with the Curiosity Drop |
| Follow cam | journeys (raindrop → river → sea; blood through the heart) | camera position = object position on its path (`@remotion/paths` `getPointAtLength`) with a slight lag and look-ahead |
| Orbit | 3D objects (heart, globe, battery) | camera on a circle/ellipse around the target, `lookAt` target, 20–90° per shot |
| Dolly zoom ("vertigo") | "wait, what?!" twist moments | 2D: background scales up while subject counter-scales to stay the same size; 3D: move camera back while narrowing FOV. Max once per video |
| Spiral dive | atmospheric chapter openers (deep sea, into the ground) | combine descend + slow rotate (≤ 20°) + push-in |
| Snap zoom | a key word or Big Number | 8–12 frames to scale 1.3–1.5, `Easing.out(Easing.exp)`, hold, settle |
| Whip pan | jump between two places | 8–12 frame horizontal slide with `<CameraMotionBlur>` (2D only), land with tiny overshoot |
| Rack focus | move attention label ↔ object | animate blur of foreground vs background layers (or postprocessing `DepthOfField` focus in 3D) over 15–25 frames |
| Impact shake | lightning, eruptions, "attacks" | decaying noise offset (`@remotion/noise`), amplitude ≤ 12 px, ≤ 0.5 s |
| Breathing drift | default on every static shot | 1–2% noise-driven position/scale wander |
| Reveal behind foreground | wipe into the next view | a near/foreground silhouette (rock, wave) passes across the frame, the cut happens while it covers the screen |
| Dutch tilt | tension, something going wrong | rotate 3–6°, rarely |

**In 3D scenes** use the same moves on a real perspective camera (fov 30-45): push-in = dolly forward, crane = camera Y on a curve, follow cam = position on a `CatmullRomCurve3` with look-ahead, orbit = angle around the target, fly-through = spline through the environment just above the terrain. Real camera movement through a 3D world is the default for environment scenes.

**Camera rules** (the Director's uniqueness rules in `references/director.md` are the full, enforced version): one move per shot, motivated by the narration; slow-in/slow-out on everything except snap zooms and whip pans; no move faster than ~30% of the frame width per second except whips and snaps; labels appear after a move settles and are counter-scaled so text size stays stable; motion blur only on fast moves; never the same signature move twice in a row, and each chapter opens with a different signature move; check every move at preview speed for smoothness before the final render.

### 5a-3. Look library (ideas borrowed from Lemo-Opuscar)
The channel look stays flat geometric vector with grain. These are **scene looks**: variations used inside one scene or chapter for variety, always in the channel palette, fonts and grain. The prompt can ask for one with `LOOK:` (for example `LOOK: microscope story`); otherwise pick at most two per video.

| Look | Use for | How (in house style) |
|---|---|---|
| Microscope story | cells, bacteria, crystals, enzymes | circular vignette "lens", soft focus edges, slow drift, rack focus between depth layers, a small scale bar ("10 µm") |
| Exploded teardown | how a device works (battery, headphones, card reader) | parts separate along one axis with thin leader lines and labels, then reassemble; 3D: offset each mesh along its normal, orbit 30–60° |
| Isometric infographic | systems and flows (power grid, water supply, payment networks) | 30° isometric grid, flat-shaded blocks, animated dashed paths for flow, labels on flat tags |
| Blueprint | engineering, physics, "how it was designed" | navy background, thin light-teal lines drawn on with DrawSVG, dimension arrows, gold for the one important part |
| Data storytelling | numbers that change over time | one chart per idea, bars and lines grow on the spoken number, the key value becomes a Big Number |
| Satellite briefing | Earth-scale stories (Harmattan dust, ocean currents, storms) | top-down map with D3 + Natural Earth, slow push-in, coordinate ticks, pulsing markers, haze layers |
| Projection on white model | explaining a 3D shape (heart, ear, volcano) | a plain white/ivory 3D model with palette-coloured "projected" highlights and arrows moving over it; strongest 3D look for anatomy |
| Sci-fi HUD | targeting or detection (how mosquitoes find you, how GPS locks on) | rings, ticks and readouts in light teal over the scene, switching modes on beats |
| Tilt-shift miniature | everyday places shown as tiny worlds (a kitchen, a city) | 3D low-poly scene, strong depth of field top and bottom, high camera, slightly sped-up motion |
| Low-poly island / diorama | self-contained worlds (a volcano, a river system, an ecosystem) | 3D flat-shaded low-poly on a floating base, orbit camera, palette colours only |
| Glass render | showing what's inside a transparent object (a bulb, a battery cell, a drop) | Blender hero shot (Glass/Transmission in EEVEE), or Three.js `MeshPhysicalMaterial` with transmission for short moments; check render time on the target machine |

**Borrowed working habits:**
- **Storyboard gate:** for every video, stop once after the style-frame contact sheet (step 2) and wait for the user's go-ahead before rendering motion.
- **Director self-check:** after the draft render, watch it against this list and fix once before showing the user: Is the story clear without sound? Does every scene change on a spoken beat? Is there one clear focus per shot? Does each chapter open with a different signature move? Is anything static for more than ~4 seconds? Are the sound effects sparse and on their beats?
- **Rhythm:** alternate busy and calm scenes; follow every dense diagram with a simpler "breathing" shot (a Big Number, an icon, a slow push-in).

**Rules for borrowing:** take ideas only. Don't copy Lemo-Opuscar's demo films, stills or narration (the demos are CC BY 4.0 and some narration is excluded), and don't use its voices for channel videos: narration always comes from the user's ElevenLabs files. If the Lemo-Opuscar plugin is installed (`~/lemo-opuscar/styles/<style>/STYLE.md`), you may read a style's STYLE.md for motion and sound ideas when the user names it, then rebuild the look here in Remotion in the house style.

### 5b. Motion, transitions, assets, science and sound toolkit
**Motion and transitions**
- **GSAP** (`gsap`, free for commercial use including all plugins): use for complex choreography and its SVG plugins: **MorphSVGPlugin** (shape to shape), **DrawSVGPlugin** (lines drawing on), **MotionPathPlugin** (objects following curves, e.g. a water droplet around the water cycle), **SplitText** (titles by letter or word), **CustomEase** (the channel's signature easing). **Determinism rule:** build every GSAP timeline with `paused: true` and drive it only with `tl.seek(frame / fps)` (or `tl.progress(...)`) inside the component on every frame; never let GSAP's ticker run (`gsap.ticker.lagSmoothing(0)` and no `.play()`), never use ScrollTrigger. For simple fades and moves, keep using Remotion's `interpolate`/`spring`.
- **Flubber** (`flubber`): smooth morphs between any two SVG paths (`flubber.interpolate(a, b)(p)` with `p` from the frame). Use for signature match-cut transitions: raindrop → salt crystal → globe; one shape becomes the next scene.
- **Lottie** (`@remotion/lottie`): ready-made animated icons and small loops. Only use files whose licence allows commercial use (check each file on LottieFiles; prefer the Lottie Simple License or CC0), recolour them to the palette, and log each one in `sources/sources.csv`.
- **Transition grammar for this style:** match cuts with Flubber morphs; iris/shape wipes using a palette-coloured circle or droplet; slide-and-settle with a slight overshoot; never generic crossfades for more than one transition per video.

**Assets (flat style)**
- **Open Peeps** (openpeeps.com, CC0; confirm on the site): mix-and-match hand-drawn people when a scene truly needs a person. Recolour to the palette, and keep proportions consistent across the video.
- **Icons:** Phosphor (`@phosphor-icons/core`), Tabler (`@tabler/icons`) and Lucide (`lucide-static`), all permissively licensed. Use one icon family per video, in the fill weight that matches the style, recoloured to the palette.
- **Never** use icon or illustration packs that are free for personal use only, and never trace brand logos.

**Science-specific**
- **Matter.js** (`matter-js`) for physics: floating and sinking (buoyancy), falling, collisions, stacking, particles bouncing. **Simulate first, animate second:** run the simulation at a fixed time step from t = 0 in a Node script, save positions/rotations per frame to `src/data/physics_<scene>.json`, and have the component read the frame's values. Never run the physics engine live during render.
- **Rapier** (`@dimforge/rapier3d-compat`; MIT) for **3D physics**: crystals tumbling into a pile, pebbles rolling down a riverbed, droplets bursting from a cut onion (as small spheres), ions bouncing inside a battery, parts falling apart in an exploded teardown, dominoes, things floating and sinking in 3D. Same rule as Matter.js: **bake, don't simulate live.** Remotion renders frames in parallel and out of order, so a live simulation gives different results per frame and per render.
  1. Write `scripts/bake_<scene>.mjs`: `await RAPIER.init()`, build the world with gravity, add bodies and colliders in a fixed order, seed every random start value, and set a fixed `world.timestep = 1 / fps` (or step 2–4 substeps per frame for fast or small objects).
  2. Step from t = 0 to the scene's last frame; each frame, store every body's translation and rotation (quaternion) → `src/data/physics_<scene>.json` (round to 4 decimals; for hundreds of bodies, use a binary `Float32Array` file instead).
  3. In the scene, render plain meshes (or one `InstancedMesh`) and set each body's position and quaternion from the JSON for `useCurrentFrame()`. Use the same frame rate as the composition.
  4. Rapier is rigid-body physics: use it for solid objects. Fake liquids and gas with particles, noise and shaders, and keep a hand-animated override for the hero object so the important motion lands exactly on its beat.
- **Our World in Data** (ourworldindata.org): charts and data produced by OWID are CC BY; much of its data comes from third parties (WHO, UN, World Bank) under their own licences, so check the source licence for each dataset. Download the CSV, store it in `src/data/` with its source URL, rebuild the chart in the house style with D3, show "Source: Our World in Data / <original source>" on screen, and add it to the credits.
- Keep using KaTeX for formulas, D3 + Natural Earth for maps, and the scientific model libraries (5c) for 3D.

**Sound effects: ElevenLabs is the main source**
- **Every scene's SFX and ambience are generated with ElevenLabs sound effects** (`eleven_text_to_sound_v2`) using `scripts/eleven_sfx.py` and the `ELEVENLABS_API_KEY` in `keys.env`. Settings: `settings.json` → `"sfx"` (`model_id`, `prompt_influence` 0.4, `output_format`).
- **Plan:** from the storyboard's planned sounds, write `anim/direction/sfx_plan.json`: one entry per distinct sound `{id, prompt, duration, loop, influence, scene, beat}`. Reuse one sound across beats instead of generating near-duplicates (one whoosh family, one pop family per video). Size each `duration` to its moment (0.5-30 s; whooshes/pops 0.5-2 s, risers 2-4 s, ambience beds 10-30 s with `loop: true`, repeated in the mix).
- **Prompts:** describe source, action, material, space and distance, and mood, e.g. "deep underwater hydrothermal vent hissing, low muffled rumble, bubbles rising, distant", "soft airy whoosh passing left to right, smooth", "tiny glassy crystal tick, close, dry". Add "no music, no voices" unless wanted. Match the story theme and the scene's look (soft and organic for calm videos; never harsh or cartoonish unless the script asks).
- **Run:** `.venv/bin/python -I <skill>/scripts/eleven_sfx.py plan anim/direction/sfx_plan.json` (free: list, lengths, total seconds) → show the user and **ask before spending credits** → `generate anim/direction/sfx_plan.json --out anim/public/sfx --yes` (skips files that exist; `--only id1,id2 --force` to redo one; `--takes 2` for hero sounds, then keep the best take as `el_<id>.mp3`). Files are `anim/public/sfx/el_<id>.mp3`; each is logged automatically in `sources/sources.csv`; `sfx_report.json` flags near-silent results. Listen-check hero sounds; regenerate with a sharper prompt or higher `influence` if one misses.
- **Licence:** ElevenLabs sound effects may be used in monetised videos only on a paid ElevenLabs plan. Remind the user once per video if unsure of their plan.
- **Reuse:** generated sounds that work well become the channel kit: copy them to `brand/sfx_kit/` with a short note of what they're for, and reuse them in later videos before generating new ones.
- **Brand intro/outro keep their approved Freesound sounds** (see Channel brand system) unless the user asks to replace them.
- **Fallbacks** (only when ElevenLabs fails, no key/credits, or the user asks): Freesound (CC0) via the key in `keys.env`, then the procedural kit below.

**Sound (procedural, licence-free): fallback**
- Generate ambience, beds and effects in code so no licence is needed, and log them as "generated" in `sources/sources.csv`:
  - **FFmpeg synthesis** (always available): brown/pink noise through low-pass filters with slow volume swells for ocean, wind and rain; low sine chords for soft pads; short filtered noise bursts for whooshes; enveloped sine blips for pops and clicks.
  - **Tone.js** (`tone`) for richer musical beds: render with `Tone.Offline` in a headless browser page (or Remotion Studio) to a WAV file, using a fixed seed and tempo, then mix with FFmpeg.
- Build a small reusable sound kit in `anim/public/sfx/` (whoosh, pop, click, riser, shimmer, ambience beds per environment: ocean, wind, deep sea, forest, lab hum) and reuse it across videos for a consistent channel sound.
- Place effects on the beat frames from `timeline.json`; keep them short and quieter than the narration; mix per step 8.

**Rive: advanced rigged animation, built by Claude (no Rive editor needed)**
Claude authors every `.riv` file itself. The user never has to open the Rive editor.

- **Use Rive for** what SVG/GSAP does poorly: characters and creatures with bones, IK and mesh deformation (a mascot that blinks, talks and points; an animal walking; a heart beating with soft squash), organic morphs, layered animation, and reusable animated props across videos. Keep Remotion/GSAP/Three.js for layout, camera, text, charts and 3D.
- **Build route 1 (preferred): official Rive CLI + RML.** Create a project (`rive.yaml`, `scene.rml`) and write the scene as RML: artboards, shapes, bones, skinning, timelines with easing, state machines. First read the `AGENTS.md`/`CLAUDE.md` the CLI writes into each new project, since it documents the current RML syntax. Compile with `rive <project> --once` (`--verify` checks without writing). Use the CLI's headless frame capture to render test frames and look at them before using the file. A clean, watermark-free `.riv` needs the project bound to the user's Rive account (`rive push`) on the Cadet plan or higher; if the user is not on a paid plan, use route 2 for final renders.
- **Build route 2 (free fallback): `rive-mcp`** (community MCP server; unofficial). Use `riv_create` to build a `.riv` from a JSON scene spec (shapes, gradients, embedded PNGs, text, bones + skinning, IK, mesh deformation, keyframes with easing, state machines), `riv_edit` for lossless edits, and its render/state-machine tools to check frames. Pin the version, and test each new feature on a small scene before relying on it.
- **Art inside the rig:** draw parts as clean palette-coloured shapes (or import the video's own SVG parts) so each limb, eye and mouth is a separate piece that bones can move. Keep the house style: flat palette colours, consistent proportions. Highly detailed painterly characters are out of scope; simplify to the flat style.
- **Structure every rig the same way:** one artboard per character/prop, named timelines (`idle`, `blink`, `talk`, `point`, `walk`, `enter`, `exit`), loopable where it makes sense. Write the names to `anim/direction/rive_<name>.json` so scenes reference real names. Save files to `anim/public/rive/<name>.riv`; keep the editable source (`.rml` project or JSON spec) in `anim/rive_src/<name>/` so the rig can be changed later. Reusable channel characters go in `brand/rive/` with their source. Log each file as "generated" in `sources/sources.csv`.
- **Determinism rule (same as GSAP):** animation is driven by Remotion's frame, never by Rive's own clock. Play named timelines through `@remotion/rive`'s `<RemotionRiveCanvas src artboard animation fit alignment>`, which advances with the composition frame. For switching animations on beats or blending, use `onLoad` to get the Rive instance and set the state from `useCurrentFrame()` each frame (e.g. scrub a timeline to `frame / fps - beatStart`). Avoid state machines that react to elapsed time or randomness; if one is needed, set its inputs from the frame.
- **Timing to narration:** map each animation change to a beat frame in `timeline.json` (point on the spoken keyword, blink every 3-5 s, `talk` while the VO plays, driven by `voice_rms.json` for mouth open/close). One Rive hero per shot.
- **Verify:** render the same frames twice and out of order (`render_scan.py`) and confirm the Rive layer matches; check render time on the target machine; include a Rive still in the style-frame contact sheet (storyboard gate). If a file renders inconsistently or a feature fails, rebuild that part in SVG/GSAP and tell the user.

### 5c. Scientific model libraries
Use real scientific geometry when accuracy matters more than stylization. **Check and log the license of every file you actually use**; libraries mix licenses, and some change them between releases.

| Library | What it's good for | License to expect |
|---|---|---|
| **BodyParts3D** (DBCLS, `dbarchive.biosciencedbc.jp/en/bodyparts3d`) | Human anatomy: bones, muscles, organs, vessels, nerves, each as a separate mesh named by FMA ID | Current release: **CC BY 4.0**, credit "BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International". Older releases and mirrors were **CC BY-SA 2.1 JP**: download the current release from DBCLS, not old copies. |
| **Z-Anatomy** | Organized, labelled atlas built on BodyParts3D | **CC BY-SA 4.0**, and it includes some **NC** parts. Use only as a visual reference for layout, not as an asset, unless the user approves. |
| **NIH 3D** (`3d.nih.gov`) | Organs, cells, viruses, proteins, medical models | Varies per model (many public domain or CC); check each. |
| **RCSB Protein Data Bank** (`rcsb.org`) | Real protein, DNA and virus structures (atom coordinates) | PDB data is free to use (CC0). Build the molecule in Three.js from the coordinates (spheres for atoms, cylinders for bonds, or a smooth ribbon). |
| **Smithsonian Open Access 3D** (`3d.si.edu`) | Fossils, skulls, artifacts, historical objects | Items marked **CC0** only. |
| **NASA 3D Resources** | Spacecraft, rovers, asteroids, planets | Generally free to use; follow NASA media guidelines and never imply endorsement. |
| **Sketchfab** / **Poly Pizza** | Everything else | Filter for downloadable **CC0** or **CC BY**; check each model. |

**Preparing models for Remotion:**
1. Download only the parts needed (e.g. the heart and its vessels, not the whole body). BodyParts3D offers reduced-polygon versions (95%/99% reduction): start with those.
2. Convert OBJ/STL to **GLB** in Blender (see 5d, Model preparation): decimate and export with Draco compression. Aim for a few hundred thousand triangles per scene at most.
3. Map names to parts: BodyParts3D files are named by FMA IDs; use its parts list to find the right files and to label structures correctly with standard anatomical names.
4. Place models in `anim/public/models/` and load with `useGLTF` (Drei) inside `delayRender`/`continueRender`.
5. Log each model in `sources/sources.csv` and add its credit line to `exports/<name>_credits.txt`.

**Styling scientific models for an educational channel:**
- Use clean, readable materials: soft toon or matcap shading, one colour per system (bones ivory, muscles warm red, vessels red/blue, nerves yellow), semi-transparent "ghost" layers to show what's inside.
- Reveal layer by layer on the beats (skin fades → muscles → organ of interest highlighted), with labels that point at the exact structure being named.
- Keep it non-graphic: no gore, wounds or realistic surgery. Show anatomy the way a textbook does.
- Don't present a simplified model as clinically exact, and never give medical advice in on-screen text.

### 5d. Blender: hero 3D design and rendering
**Before building any hero shot** (Blender or Three.js), any scene matched to a reference image, and any scene the user corrected before, write its numbered checklist with `references/hero_checklist.md` (10-12 lines, numbers instead of vague words, a NEVER line per failure, every narrated object, readability last) into `anim/direction/checklist_S##.md`, grade the style frame line by line (yes / partial / no, measured or eyeballed), and stop after round 2 to show the user.

Blender is used **only through Python scripts run headless**, so every shot is reproducible and re-renderable after changes. Never rely on manual clicks in the Blender UI; save the `.blend` next to the script so the user can open it.

**Files:** `anim/blender/S##_<slug>.py` (builds the scene), `anim/blender/S##_<slug>.blend` (saved result), frames in `anim/public/blender/S##/0001.png …`, camera data in `anim/src/data/camera_S##.json`.

**Run:** `<blender> -b -P anim/blender/S##_<slug>.py -- --timeline anim/src/data/timeline.json --scene S## --scale 0.5 --samples 16 --out anim/public/blender/S##/` (block-out previews with `--engine workbench`; drafts with the EEVEE fast preset at `--scale 0.5 --samples 4`; finals at the user's chosen resolution with 8-16 samples on low-power machines, more on faster ones). Run long renders in the background, one scene at a time; set `render.use_overwrite = False` so an interrupted render resumes.

**Building the scene (original art only):**
- Start from an empty scene (`bpy.ops.wm.read_factory_settings(use_empty=True)`); model from primitives, modifiers (Subdivision, Displace with noise textures, Decimate for low-poly, Solidify, Array), curves and Geometry Nodes scatter (trees, rocks, particles) with fixed seeds.
- Materials: Principled BSDF in palette colours (from `theme.ts`, converted to linear), roughness 0.5-0.9 for the stylised look; Glass/Transmission, Emission (lava, vents), Volume Scatter (underwater haze, god rays) only where the shot needs them. Use the **Standard** view transform (not AgX/Filmic) so palette colours render as specified.
- World: gradient sky shader or a CC0 Poly Haven HDRI; one sun or area key light plus fill, consistent light direction with the rest of the video.
- EEVEE settings: soft shadows on, ambient occlusion/ray tracing on if the GPU copes, bloom via the compositor Glare node, motion blur on for fast moves, film filter 1.5 px; fixed seed for everything noisy.

**Timing and camera (keep it frame-exact):**
- Read `timeline.json`: set `scene.render.fps` from it and `frame_end = durationInFrames` for the scene; keyframe every action on its beat frame (scene-local, frame 1 = scene start). No physics or particle simulations unless baked first.
- Camera moves use the camera library: keyframed location/rotation or a Follow Path constraint on a curve, with ease-in/out F-curves. One move per shot.
- After keyframing, the script writes the camera's position, look direction and lens for every frame to `camera_S##.json` (convert Blender Z-up to Three/Remotion Y-up: `(x, z, -y)`), so 2D labels in Remotion use the same projector maths and stay pinned to objects.

**Into Remotion:** play the PNG sequence inside the scene's `<Sequence>` with `<Img src={staticFile(`blender/S##/${pad(frame + 1)}.png`)}>` (frame-exact; no video decoding), render with transparent background (RGBA PNG) when 2D graphics or a Three.js layer sit behind it, then put labels, Big Numbers and formulas on top as usual. The grain overlay goes over Blender frames too so all shots match.

**Model preparation (replaces obj2gltf / gltf-transform):** import OBJ/STL/FBX/glTF from the scientific libraries (5c) with `bpy.ops.wm.obj_import` / `stl_import` / `import_scene.gltf`, keep only the parts needed, apply transforms, Decimate to the triangle budget, assign palette materials, and export GLB with Draco compression (`bpy.ops.export_scene.gltf(filepath=..., export_format='GLB', export_draco_mesh_compression_enable=True)`) for Three.js, or render the model directly in Blender for hero shots.

**Licences:** Blender is GPL; renders and `.blend` files belong to the user. Use only built-in Blender features, free add-ons with permissive licences, and the CC0/CC BY assets allowed in Rules. No paid or "personal use only" asset packs.

### 6. Three.js rules (avoid flicker and crashes)
- Wrap 3D in `<ThreeCanvas width={width} height={height}>` sized from `useVideoConfig()`, with explicit lights (or an `Environment` HDRI) so materials read correctly.
- Drive every transform, camera position, material value and shader uniform from `useCurrentFrame()`. No `useFrame()` for animation.
- Any `<Sequence>` inside a `<ThreeCanvas>` must use `layout="none"`.
- **Only one `<ThreeCanvas>` mounted at a time**; render 3D scenes conditionally by scene. Too many WebGL contexts crash renders.
- Keep geometry light: low/mid-poly, instanced meshes for repeated objects. Textures 2K for 1440p output, 4K only for hero objects at 4K output.
- Sharpness at higher output sizes: pass the render scale as an input prop (`--props='{"renderScale":1.3333}'`) and set the canvas `dpr={renderScale}`; check a 3D still at final size for softness.
- Load textures/models/HDRIs with `delayRender`/`continueRender` (or Remotion's helpers) so no frame renders before assets are ready.
- Seed every random value (`random('seed')` from `remotion`, or `@remotion/noise`).
- If 3D frames come out black or empty, check the GL renderer (Remotion 4: `angle`, or `swangle` without a GPU) with `npx remotion gpu`.
- **Camera contract:** every 3D scene's camera comes from one pure function in `anim/src/three/cameraPaths.ts`: `export const CAMERAS: Record<string, (frame: number, fps: number) => {position: [x,y,z], target: [x,y,z], fov: number}>`, keyed by scene id, frame local to the scene. `CameraRig` only calls `CAMERAS[id](frame, fps)`. This keeps cameras deterministic and lets `scripts/cam_track.mjs` measure them.
- **Traps that blank whole frames (from stazdev/cutaway):** one NaN pixel turns the whole frame black through `Bloom`, so clamp every `pow()` base and every divisor in custom shaders (`pow(max(x, 1e-4), k)`); `smoothstep(a, b, x)` with `a > b` returns 0 on ANGLE/D3D, so write `1.0 - smoothstep(b, a, x)`; a glow colour above 1 (HDR `MeshBasicMaterial`) breaks `Color.getHSL`, so read and write it at unit peak; colours baked into vertex attributes ignore the material colour, so update the `color` attribute too.

### 7. Preview → review → final
1. **Live preview:** offer `npm run studio` in `anim/`. It opens Remotion Studio in the browser, where the user can scrub through the video and comment by scene number.
2. **Draft render** (fast, 960×540): `npx remotion render src/index.ts Documentary ../renders/drafts/<name>_preview.mp4 --scale=0.5 --muted`, then add the voice with FFmpeg for review. Ask for changes by scene number.
   **Before showing the draft** (you can't watch video, only frames):
   - **Beat sheets (measured frames):** `.venv/bin/python -I <skill>/scripts/beat_sheet.py <draft.mp4> anim/src/data/timeline.json --out anim/out/beats` gives one labelled still 0.3 s after every beat. Read every tile against the storyboard, the hero checklists and `channel_lessons.md`: is the thing being named on screen, is the beat's action visible, nothing frozen or blank? For a transition, sample the range: `--every 0.2 --from A --to B`.
   - **Camera track (measured):** `node <skill>/scripts/cam_track.mjs anim` prints every 3D scene's real azimuth, elevation, distance and fov at each beat and flags "PARKED" beats (camera barely moved since the last beat). Fix parked beats unless the shotlist marks that shot as a deliberate hold with a reason.
   - **Render scan (measured, every frame):** `.venv/bin/python -I <skill>/scripts/render_scan.py <draft.mp4> --out anim/out/scan --timeline anim/src/data/timeline.json --holds <designed holds, e.g. 412-415>` reads every frame in seconds and costs no image tokens. It FAILs single-frame flashes, mid-film runs of empty frames (nothing readable on screen, e.g. a transition through an empty or dark frame) and a true peak over −1 dBFS; it WARNs an empty frame 0, pops that aren't planned cuts, frozen stretches over 1 s that aren't marked holds, and loudness off −14 LUFS; it lists the silences and the loudest moment, and writes `phone_sheet.png` (1 frame per second at 360 px wide). Read the phone sheet: every label, number and caption must still read at phone size. Fix every FAIL; for every WARN, fix it or say why it is deliberate.
   Fix, re-render the affected frames, and repeat until a full pass finds nothing. Then send the draft.
3. Apply changes. Re-render only what's needed with `--frames=<start>-<end>` when checking a scene.
4. **Ask for the resolution first (always).** Never start a final render, a Blender final sequence or the Shorts finals until the user has picked a resolution for this video, even if `settings.json` has one or a previous video used one. Ask once, as a single multiple-choice question, right after the draft is approved, listing for each option its size and an estimated render time for this video (from the draft's measured render speed: 720p ≈ 0.6×, 1080p = 1×, 2K ≈ 1.8×, 4K ≈ 4× the 1080p time; Blender shots scale the same way) and file size:
   - **720p** 1280×720: `--scale=0.6667`
   - **1080p** 1920×1080: `--scale=1`
   - **2K** 2560×1440: `--scale=1.3333`
   - **4K** 3840×2160: `--scale=2`
   Pre-select `final_resolution` from settings as the suggested option. Shorts follow the choice: 720p → 720×1280, everything else → 1080×1920. Don't re-ask for re-renders of the same video unless the user changes it. Then render the final at the chosen scale from the 1920×1080 design canvas:
   Render a high-quality intermediate for the grading pass: `npx remotion render src/index.ts Documentary ../renders/final/<name>_master.mp4 --codec=h264 --crf=12 --muted --scale=<s> --props='{"renderScale":<s>}'`, with `--concurrency` at roughly half the CPU cores (lower it if 3D scenes run out of memory).
   Expect about 0.6× the 1080p render time at 720p, 1.8× at 2K and about 4× at 4K; 3D-heavy scenes take the biggest hit. Warn the user before a 4K render of a 3D-heavy video, and check free disk space (4K masters can be several GB).

### 8. Sound, grade and assembly (FFmpeg)
- **Sound design pass:** for each scene, add room tone or ambience that fits (wind, ocean, rain, a quiet lab hum, crowd murmur for history scenes) at a low level; soft whooshes on camera moves and transitions; gentle pops/clicks on labels and chart reveals; a subtle riser into big reveals. Place them on the beat frames from `timeline.json`. Keep it sparse and always quieter than the voice. Generate them with ElevenLabs sound effects (5b, `scripts/eleven_sfx.py`) as the main source; use Freesound or the procedural kit only as fallbacks. ElevenLabs output peaks near 0 dBFS, so set each SFX level in the mix (about −20 to −28 dB under the voice for ambience, −12 to −18 dB for accents). Log every sound with its licence.
- **Mix:** narration on top; music bed about 18–24 dB under the voice with `sidechaincompress` ducking; ambience below the music; SFX short and soft. Normalize to about -14 LUFS (`loudnorm=I=-14:TP=-1.5:LRA=11`).
- **Colour grade + grain:** apply the theme's look to the master in the same final encode: a consistent grade (FFmpeg `eq`/`colorbalance`/`curves`, or `lut3d` with a CC0/self-made `.cube` file) and very light grain (`noise=alls=3:allf=t`, adjust to taste). Grain also reduces banding in gradients and dark scenes. Keep it subtle; test on a still first.
- **Final encode:** grade + grain + mixed audio → `renders/final/<name>.mp4`, H.264 `-crf 16` (1440p/4K) or `-crf 18` (1080p), `-preset slow`, `-pix_fmt yuv420p`, AAC 320 kbps, `-movflags +faststart`. Confirm with ffprobe: right resolution, fps, and audio/video lengths matching within a frame or two.
- **Extras:** `exports/<name>.srt` captions from the transcript, chapters from scene titles, and a 1280×720 thumbnail made with `remotion still` (at `--scale=1`, design canvas cropped/arranged for a thumbnail) plus a short title.
- **Shorts:** for every long video **longer than 5 minutes, always make 2 YouTube Shorts** from its most interesting moments (automatically, no need to ask). For videos of 5 minutes or less, make Shorts only if `also_export_shorts` is true or the user asks. Full rules in **8a**.

### 8a. YouTube Shorts from long videos
**When:** automatically, **2 Shorts for every long video over 5:00**. Shorter videos: only when `also_export_shorts` is true or the user asks.
**Picking the 2 moments (the most interesting, different from each other):**
1. Score every 25-60 s stretch of the narration that can stand on its own: +3 a surprising fact or the twist, +3 a Big Number or "That's like…" comparison, +2 a strong visual (3D hero shot, reveal, transformation), +2 it opens with a question or bold claim (a hook in the first 2 s), +2 it ends on a clear payoff, +1 high voice emphasis (voice_emphasis.json); −3 it needs earlier context to make sense, −2 it starts or ends mid-sentence.
2. Take the top two that **don't overlap** and come from **different chapters**; prefer one "wow fact" Short and one "how it works" Short.
3. Cut on sentence boundaries and pause midpoints; total length 30-60 s (never over 60 s).
4. Write the picks, their scores and reasons into `anim/direction/shorts.json`, and show them to the user with the draft.
**Building each Short (rebuild for vertical, never just crop):**
- `Short.tsx` composition, 1080×1920, same fps; reuse the same scene components with vertical layouts: subject centred, camera reframed for 9:16 (3D scenes re-render with a vertical camera; Blender hero shots re-render at 1080×1920 or use the 16:9 frames inside a designed vertical layout, never stretched).
- **Hook in the first 1-2 s:** open on the most striking frame of the moment with a 3-6 word title card or kinetic text of the question/claim; then the **Shorts intro** (6.97 s, Channel brand system) plays, then the moment. End with the **Shorts outro** (5.5 s).
- **The first 3 seconds, sound off (Shorts autoplay muted and use frame 0 as the thumbnail):**
  - **Frame 0 is a finished picture:** the striking frame with the hook text already on it. No fade from black, no empty ground, no half-built composition (`render_scan.py` must not warn on frame 0 for a Short).
  - **The hook line is fully on screen by 1.0 s and readable by 3.0 s:** ≥ 84 px at 1080 px wide, full opacity, ≥ 7:1 contrast against what is actually behind it (put it on a dark pill if the scene is busy), inside the Shorts safe area (top 15% and bottom 20% stay clear of YouTube's UI).
  - **Muted test:** from the first 3 s alone (`beat_sheet.py --every 0.5 --from 0 --to 3 --width 360`), someone must be able to say what the Short is about. If not, change the hook text or the opening frame.
- The Director's uniqueness rules apply inside each Short; pace is faster (new visual every 2-4 s).
- Captions always burned in (8b, Shorts layout); labels and numbers resized for phone reading (≥ 56 px).
- Audio: the same voice segment and music/SFX mix, normalized to −14 LUFS; music fades in the last 0.5 s. End on the payoff line, or loop cleanly back to the hook; optional final 1 s card "Full video on the channel" in brand style (no third-party logos).
- Output: `renders/final/<name>_short1.mp4`, `<name>_short2.mp4` (H.264, 1080×1920, `-crf 18`, AAC), plus `exports/<name>_short1.srt`/`short2.srt` and a suggested title + 3 hashtags for each in `exports/<name>_shorts.txt`.

### 8b. Captions (always on: long video and Shorts)
Beautiful animated captions are burned into **every** long video and **every** Short automatically. This is the user's standing instruction and overrides any older setting or channel-bible line that turns captions off (for example "captions off in long videos"; keep exporting the `.srt` too).
- **Source text:** Whisper word times from `transcript.json`, with the **wording corrected against the script** (names, numbers, spelling, punctuation), so captions read exactly as written while staying in sync with the voice. Numbers appear as the narration says them and must match any on-screen number.
- **Build:** a `Captions.tsx` component (in `src/lib/`, reused by `Documentary` and `Short`) using `@remotion/captions` `createTikTokStyleCaptions` to group words into pages, rendered frame by frame from `useCurrentFrame()`.
- **Look (beautiful, on-brand, never neon):**
  - Font: Inter SemiBold/Bold for the words; the active word may use the channel display font (Outfit ExtraBold) or simply bold.
  - Words in cream `#F6F1EA` on a rounded translucent ink pill (`rgba(12,10,14,0.72)`, radius ≈ 0.4 × font size, soft offset shadow, no hard outline); the **active word** highlighted with the story theme's accent (or the chapter accent from `look.json` when a scene palette needs it), as text colour or a soft rounded highlight behind the word.
  - Motion: each page fades/slides up 6-8 px in 4-6 frames; the active word scales 1.00 → 1.06 and back; no bouncing, no shaking, no colour flashing.
- **Size and layout:**
  - Long video (16:9 design canvas): 44-52 px, max 2 lines, max ~7 words per page; centred in the lower area, bottom of the pill ≥ 10% above the frame bottom (clear of YouTube's player controls) and inside the 5% safe margin.
  - Shorts (9:16): 64-76 px, 1-2 lines, 2-4 words per page; placed around 62-70% of the frame height (above YouTube's title/description area and away from the right-hand button column, so keep ≥ 140 px clear on the right); bigger active-word emphasis.
- **Never collide:** captions must not cover labels, formulas, Big Numbers, chapter cards, faces or the key action. If something important sits in the caption zone, move the caption pill up (long video: to the top area; Shorts: to ~25-30% height) for that page; no caption during the intro or the outro (they carry their own text) (move them to the left half there, or hide during silent stretches).
- **Timing:** pages change on natural phrase breaks and pauses (voice_pauses.json), never mid-phrase if avoidable; a page stays at least 0.6 s; words light up within ±2 frames of being spoken.
- **Check:** in the quality stills, captions are spelled exactly like the script, readable on every background, never overlapping graphics, and inside safe areas.

## Quality checks (before showing any render)
Render stills at each scene's start, middle, end and at every beat (`remotion still --frame=N`; for finals, also at the final scale) and look at them:
- **Text sizes (on the 1920×1080 design canvas; measure the rendered size after any 3D scale or zoom):** the main message of a frame (Big Number, chapter title, the question) ≥ 56 px; labels, captions and secondary text ≥ 32 px (36 px preferred); formulas ≥ 48 px; **nothing meant to be read below 24 px** (anything smaller is texture, so make it clearly decorative or remove it). Inside a 5% safe margin, never overlapping, spelled correctly. Small all-caps letter-spaced "eyebrow" labels are banned (Rules' cliché list); use sentence case.
- **Reading time:** every piece of text holds **completely still** for at least max(1.5 s, 1.0 s + 0.3 s × words), counted from the moment it has fully arrived until it starts to leave; chapter and title cards 2.5-4 s; the channel lock-up or wordmark ≥ 2 s with ≥ 1 s fully still; comparison items ≥ 2.5 s each before the verdict; any information-bearing element ≥ 1 s still before a cut. Text that types on counts from its last character. Swapped text never overprints: the old line leaves before the new one lands. When unsure, hold longer (every reviewer's pacing note goes one way: slower).
- Labels point at the right things; maps, charts, formulas and 3D models match the storyboard's sources; chart axes honest.
- No black/empty 3D frames, flicker, blank frames, missing KaTeX glyphs, or elements frozen mid-animation at scene ends.
- 3D and textures sharp at the final resolution; no visible banding after the grade.
- Blender frames: colours match the palette (Standard view transform), no noise or fireflies, no missing frames in the sequence, and their camera matches the label positions from `camera_S##.json`.
- Colours and lighting consistent with the theme; readable contrast; `check_palette.py` passes (no neon unless the script asked for it).
- `check_shotlist.py` passes and every shot on screen matches its shotlist entry (movement, angle, size, timing on the beat).
- No flat-looking environment: every scene showing a place has real depth (3D or 2.5D), visible atmospheric perspective (fog/haze), and a camera that moves through space; the storyboard's depth choice is implemented.
- Animation lands within ~0.2 s of the spoken word; sound effects land on their beats.
- Captions present on the long video and every Short, spelled like the script, synced within ±2 frames, inside safe areas and never covering graphics (8b).
- Videos over 5 minutes have exactly 2 Shorts, each 30-60 s, vertical-native, from different chapters, starting with a hook (8a).
- **Frame colour check (measured):** `python3 <skill>/scripts/check_frames.py anim/out/style_S*.png` flags grey/washed-out, flat-contrast, oversaturated and neon frames. When `anim/public/style_reference.png` exists, add `--ref anim/public/style_reference.png --sheets anim/out/compare` to also compare each frame's brightness and saturation with the reference and write side-by-side PNGs (reference left, render right). Pass `--neon-ok S07,...` for scenes where the script asks for neon. Without a reference, an all-grey frame is only a warning (it can be a deliberate look such as newsprint).
- **Fresh-eyes critic (idea from Leonxlnx/cook):** models rate their own work too highly, so after your own checks, start one subagent that has **not** seen the build. Give it only: the style-frame contact sheet (or the side-by-side PNGs), the narration line for each scene, `theme.ts` palette values, and this rubric. Ask it to score each scene 1–10 on: (1) one clear focus, (2) composition and depth, (3) colour vs the theme/reference, (4) text readability, (5) does the picture explain the narration line, (6) cliché check against the Rules' avoid-list. It names the weakest scene and the single change that would help most. Fix every scene scoring below 7 (one round; don't loop), then show the user. Tell the user the critic's scores next to your own.
- **Say what was measured.** In every report to the user, mark each check as **measured** (a command or script produced the result) or **eyeballed** (you looked at a still). Never say a check passed if you didn't run it.
Fix and re-render the affected scene before showing the user.

## Credits for borrowed methods
Ideas adapted (no code copied unless noted) from: **stazdev/cutaway** (MIT): corrections ledger, hero checklists, beat sheets, camera track, three.js traps; **Leonxlnx/cook** (MIT): cliché ban list, frame colour check, fresh-eyes critic, measured vs eyeballed, sub-frame accumulation; **win4r/video-director** (MIT): render-scan checks, text size and reading-time rules, the muted first-3-seconds test, science terms said and shown; **rossark0/rossark-motion-skill** (MIT): living-motion recipes, flow, follow-through by delay, no scale-from-0 and no empty-frame transitions, colour sampling and element tracking for references; **NiazMorshed2007/reanimate** (MIT): reference matching method (motion spec, activity-curve comparison, easing fitting, ±0.08 s pass mark); **Lemo-Opuscar**: look library (5a-3).

## When done
Tell the user briefly: final video path, resolution and fps, runtime, number of scenes (3D / 2.5D / 2D, and map / chart / formula), captions/chapters/thumbnail files, the 2 Shorts (when the video is over 5 minutes) with which moments they use and why, and how to preview in Remotion Studio. Mention they can ask for changes like "S04: make the vents glow more", "turn S02 into a 3D globe", "add a chart to S05", or "render the final in 4K".