# Hero-shot checklist (method adapted from stazdev/cutaway, MIT)

A short numbered checklist that turns "make it look great" into things you can measure. Write one **before the first line of code** for:
- every **signature piece**: `TitleSting`, `PaperPlaneFold` (fold, flight, landing), each `CategoryWorld` (WORLD, TECH, BUSINESS, SPORTS), `Outro`, the **thumbnail**, and each Short's **first 3 seconds**
- every piece matched to a **reference animation** (`references/reference_matching.md`): its spec rows become checklist lines
- every shot the user has **corrected before** (rows in `channel_lessons.md`)

Save it as `anim/direction/checklist_<piece>.md`. Signature pieces are built once and reused, so their checklists are kept and re-graded whenever the piece changes.

## Rules for writing one
- **8 to 12 numbered lines.** Fewer misses features; more turns into a spec nobody grades.
- **Order:** camera view and framing → the signature moment (what a viewer remembers) → timing against the voice → light and materials → colour → readability.
- **Every vague word gets a number.** "Big headline" becomes "headline cap height ≥ 64 px, fills 55-70% of the brief's width". "Fast flight" becomes "plane crosses the frame in 0.8-1.2 s".
- **Write "NEVER …" next to the default you're fighting.** "The plane banks 15-30° into the turn, NEVER flies flat like a sticker."
- **Every word the narration names in this shot has a line**, with the frame it must be visible from.
- **Measured off the reference** when there is one: timings, easings and overshoot from the motion spec.
- **The last line is always readability:** at 50% size (960 px wide; 540 px for Shorts) the key text still reads, and `scripts/check_frames.py` passes.
- Pull every relevant row of `channel_lessons.md` in as its own line.

## Grading
1. Render the still (or the beat sheet for a moving piece) with the shot's fixed camera.
2. Put reference | ours side by side when there is a reference, and ours again at 960 px wide.
3. Grade **every** line **yes / partial / no** against the picture, not against what you remember building. Mark each grade **measured** (a script produced it) or **eyeballed**.
4. Fix every "no" and "partial". **Stop after round 2** and show the user the still with the checklist and grades; the fresh-eyes critic (engine section 10) scores it too.
5. Lines added because of a user correction also go into `channel_lessons.md`.

## Template
```
Piece <name> · <what it shows> · reference: <file or "none">
1. Camera and framing: <lens/fov, height, angle, where the subject sits in frame (shares of width/height)>.
2. Signature moment: <the one thing a viewer remembers>, <size and timing in numbers>.
3. <Second feature>. NEVER <the default that kills it>.
4. On the voice: <element> lands within ±3 frames of "<word>"; <element> by "<word>".
5. Motion: <what moves, which way, how fast, easing>. Nothing static for more than ~4 s.
6. Light: warm key through the blind gobo from <direction>, cool fill, gobo drifting <speed>.
7. Materials: paper roughness ~0.9, <other materials>.
8. Colour: brand palette; accent <category> only on <exactly where>, ≤ 10% of the frame. No neon.
9. Text: <sizes>, inside the safe area, never covering <what>.
10. Readability: at 960 px wide <key text> still reads; check_frames.py passes.
```

## Example: the paper-plane transition
```
Piece PaperPlaneFold · brief folds into a plane, flies through the TECH world, lands as the next brief · reference: none
1. Starts on the same camera as the brief's last shot (no cut); pulls back to see the whole sheet in the first 6 frames.
2. Signature: the fold reads as paper: 3 visible creases, each fold 6-8 frames, sheet keeps its printed headline until the last fold.
3. Plane banks 15-30° into its turns. NEVER flies flat like a sticker, NEVER rotates around its centre like a logo.
4. On the voice: fold starts on the last word of the story clip; landing finishes before the next clip's first word.
5. Flight 2-3 s in total; crosses the TECH grid's giant letters with ≥ 1 near pass (letters fill ≥ 40% of the frame); motion blur only during the fast pass.
6. Light changes from the desk's warm key to the category world's light during the flight, never through a dark or empty frame.
7. Plane keeps the paper material and printed texture; giant letters are extruded with a bevel and catch the light.
8. TECH purple only on the grid lines and letter edges, ≤ 10% of the frame.
9. No captions during the transition; category name readable for ≥ 1 s.
10. Readability: at 960 px wide the category word reads; render_scan.py shows no empty frames in the transition.
```
