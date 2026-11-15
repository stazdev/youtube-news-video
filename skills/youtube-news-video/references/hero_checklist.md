# Hero-shot checklist (method adapted from stazdev/cutaway, MIT)

Write one for every **Blender hero shot**, every scene matched to a **reference image** (`anim/public/style_reference.png` or a user picture), and any scene the user has corrected before. Write it **before the first line of code**, save it as `anim/direction/checklist_<scene>.md`, and grade the style frame against it.

## Rules for writing one
- **10 to 12 numbered lines.** Fewer misses features; more turns into a spec nobody grades.
- **Order:** silhouette and camera view → the signature feature (what a viewer remembers) → the narration's key objects → materials and light → the story-theme accent → density and readability.
- **Every vague word gets a number.** "Tall peaks" becomes "peaks rise 0.35-0.5 of frame height, ridges at 35-60°". "Bright vents" becomes "the vent plume is the brightest thing in frame (luma ≥ 1.4× the scene median)".
- **Write "NEVER …" next to the default you're fighting.** "Sharp ⛰️ peaks with ridges, NEVER round lumps." Without it the default comes back.
- **Every object the narration names in this scene has a line**, with when it must be visible (channel lesson #5).
- **Proportions measured off the reference** when there is one: subject height and width as shares of the frame, horizon height.
- **The last line is always readability:** at 50% size (960 px wide) the key object still reads, and the frame colour check (`scripts/check_frames.py`) passes.
- Pull every relevant row of `channel_lessons.md` into the checklist as its own line.

## Grading
1. Render the still with the shot's fixed camera preset.
2. Stack reference | still (and the still again at 960 px wide) side by side.
3. Grade **every** line **yes / partial / no** against the picture, not against what you remember building. Mark each grade **measured** (a script produced it) or **eyeballed**.
4. Fix every "no" and "partial". **Stop after round 2** and show the user with the checklist and the grades; the fresh-eyes critic scores it too (Quality checks).
5. Lines added because of a user correction also go into `channel_lessons.md`.

## Template
```
Scene S__ · <what it shows> · reference: <file or "none">
1. Silhouette and view: <subject, what it sits on, camera height/angle/lens>. Measured off the reference: <height/width shares, horizon at __% of frame>.
2. Signature feature: <the one thing a viewer remembers>, <size in numbers>.
3. <Second feature>. NEVER <the default that kills it>.
4. Named in the narration: <object> visible from <word/beat>; <object> visible from <word/beat>.
5. Process shown happening: <what moves, which way, how fast>. NEVER a still object.
6. Materials: <how water/rock/glass/skin takes light>.
7. Light: <key direction and colour>, <atmosphere/haze>, one light temperature.
8. Colour: chapter palette <name>; accent <story theme> on <exactly where>, ≤ 10% of the frame. No neon.
9. Detail near and far: <what the far distance must still show>; no copy-pasted repeats.
10. Labels/text: never cover the thing they name; ≥ 4.5:1 contrast.
11. Readability: at 960 px wide <key object> still reads; check_frames.py passes.
```

## Example: hydrothermal vent hero (written from the ocean video's corrections)
```
Scene S08 · hydrothermal vents on the dark seafloor · reference: none
1. Low camera 1.2 m above the seafloor, 35 mm, looking slightly up at 3 chimneys; horizon above frame.
2. Signature: black-smoker plumes billowing UP from the chimney tops, rising 0.6-0.8 of frame height.
3. Chimneys are rough mineral towers 4-6x taller than wide. NEVER smooth cones or cylinders.
4. Named: "vents" visible from the first word of the scene; "minerals" glints appear on the beat "loaded with".
5. Plumes rise and spread continuously (0.3-0.5 frame heights per second), turbulent edges. NEVER a static cloud shape.
6. Chimney rock wet and dark with warm mineral streaks; plume semi-transparent, lit from inside at the base.
7. Warm amber glow at each vent mouth (the only warm light) against cool deep-sea blue; drifting particles.
8. deep-sea palette; accent ocean teal only on labels; glow amber ≤ 10% of the frame.
9. Far: 2-3 dimmer chimneys fading into haze; seafloor rocks vary in size and colour.
10. Labels sit beside chimneys on pills, never over the plume.
11. At 960 px the plumes are the brightest thing in frame (measured: luma ≥ 1.4× scene median).
```
