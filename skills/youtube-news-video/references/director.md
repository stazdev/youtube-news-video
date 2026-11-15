# The Director: shot design for every scene

The Director runs after the composition decision (`composition_decider.md`) and timing (step 1/1b), before the storyboard.
It turns every scene into one or more **shots**, each fully specified with codes from `camera_bible.md`, so that every
scene in every video looks deliberate, professional and different from the others.

## 1. Inputs it reads
- `anim/direction/look.json` (format, per-scene depth and environment, palettes, energy) from the composition decider.
- `anim/src/data/timeline.json` (scene times and beats), `voice_emphasis.json`, `voice_pauses.json` (from librosa).
- The script's narration and `VISUALS:`/`CAMERA:` lines (a camera the user writes in the script always wins).
- `direction/camera_history.json` in the project root (the last videos' choices), if it exists.

## 2. The shot formula (from the user's playbook)
Every shot = **one primary movement + one angle + one shot size + lens/focus + composition**, plus timing.
Never stack two primary movements in one shot (secondary: breathing drift X123 or handheld M021 only).
Write it as a code line in the storyboard, for example:
`S04.1  M012 Crane Down · A052 High Angle · S083 EWS · 35 mm · C095 Leading Lines · 0.0-3.2 s · on "rain"`.

## 3. How it chooses (per scene)
1. **Read the moment.** What is the narration doing here? Classify the scene's beat as one of:
   *establish* (new place/idea), *explain* (process, how), *reveal* (surprise, scale), *detail* (zoom into a thing),
   *journey* (movement from A to B), *compare* (two things), *list* (several items), *twist* (counter-intuitive fact),
   *payoff* (the answer), *breather* (calm moment after density), *transition* (bridge to next chapter).
2. **Pick candidates from the emotion map** (section 4), filtered by the scene's engine (2D / 3D / Blender) using the
   bible's ✓/~/✗ columns. `~` is allowed only with the 2.5D recipe described.
3. **Apply the uniqueness rules** (section 5) against everything already chosen in this video and in camera history.
4. **Score the remaining candidates** and take the best: +3 strongest emotional match, +2 serves the spoken beat
   (the move's key moment lands on the beat word), +2 new family compared with the previous shot, +1 shot-size
   contrast with the previous shot, +1 unused in the last 3 videos, −3 needs an engine the scene doesn't use,
   −2 hard to read with the scene's text/labels.
5. **Time it to the voice.** The move's decisive moment (reveal, end of push, snap) lands within ±3 frames of the
   beat word. Calm narration (≤ 2.3 words/s or long pauses) → slower, longer moves; fast or emphatic narration
   (emphasis words from librosa) → snap/crash/whip family, only on those words.
6. **Write the reason.** One line per shot: why this camera for this moment. No reason, no shot.

## 4. Emotion → camera map (first choices; any bible entry with the right family may be used)
| Moment | Movements | Angles | Sizes | Compositions |
|---|---|---|---|---|
| establish | M012, M016, M020, M011, X112, X113, M041 | A053, A052, A055 | S083, S082 | C095, C092, C097 |
| explain | M003, M006, M033, M009, M034, X104, X126 | A060, A055, A065 | S079, S081, S082 | C097, C093 |
| reveal | M004, M039, M041, M042, X103, M050, X120 | A051, A054, A052 | S083→S082 | C094, C096, C091 |
| detail | M001, M027, X108, X118, M031, X101 | A066, A060, A055 | S076, S077, S089 | C098, C096 |
| journey | M005, M007, M018, X128, X116, M038, X111 | A062, A063, A064 | S082, S080 | C095, C093 |
| compare | M006, X130, X125, M031, C099 recipe | A061, A059 | S086, S087 | C092, C099, C100 |
| list | X124, M006, X127 | A061, A055 | S079, S088 | C092 |
| twist | M029, M026, M025, M047, X106 | A056, A051, A054 | S077→S083 | C093, C094 |
| payoff | M004, X129, M020, M010, X120 | A052, A053 | S083 | C091, C094, C092 |
| breather | X123, M027, M028, M003 | A055 | S082, S083 | C094, C092 |
| transition | X102, M023, M040, X121, M050, M024 | any | any | — |
| danger / tension | M021, M047, M008, X122 | A056, A051 | S077, S079 | C093 |
| awe / scale | M041, M004, M016, M020 | A054, A051, A053 | S083 | C094, C091 |
| micro worlds | X108, X117, X118, X101, M045 | A066, A058 | S076, S077 | C098 |

## 5. Uniqueness rules (hard rules: checked by `scripts/check_shotlist.py`)
1. **No repeated combination:** within a video, no two shots share the same (movement, angle, size) triple.
2. **No back-to-back repeats:** consecutive shots never use the same movement ID, and differ in at least **two** of:
   movement family, angle, shot size, lens band.
3. **Families rotate:** the same movement family is not used more than twice in a row; across a video, no single
   family covers more than 30% of shots.
4. **Signature moves** (list at the end of `camera_bible.md`) at most once per video, and no two signature moves in
   consecutive scenes.
5. **Chapter openers differ:** each chapter's first shot uses a different movement family from every other chapter opener.
6. **Shot-size rhythm:** no more than 3 shots in a row of the same size class (wide: S082-S083, medium: S078-S085,
   close: S076-S077/S089); sequences generally move wide → medium → close or the reverse, with intent.
7. **Across videos:** read `direction/camera_history.json`; a scene-opening (movement, angle) pair used in the last
   3 videos is not reused for a scene of the same type; the cold-open first shot never repeats the previous video's.
8. **Motivated only:** every shot has a reason; decorative movement without a reason is rejected.
9. **Readable:** one primary movement per shot; labels appear after the move settles and are counter-scaled; no move
   faster than ~30% of frame width per second except fast-family moves.
10. **Screen direction:** journeys keep one direction of travel (e.g. rain → river → sea always left-to-right) unless a
    reversal is the point.
11. **Coverage:** a scene longer than ~7 s gets 2-3 shots (cuts or a continuous move with distinct phases), each meeting
    rules 1-10.
12. **User overrides:** a `CAMERA:` line in the script or a user request beats these rules; note it as an override.

## 6. Output files
`anim/direction/shotlist.json` (machine-readable), and the shot lines in `storyboard.md`. Schema:
```json
{ "video": "<slug>", "fps": 30, "shots": [
  { "id": "S04.1", "scene": "S04", "chapter": 1, "opener": true, "moment": "establish", "engine": "3d",
    "from": 0.0, "to": 3.2, "beat": "rain",
    "movement": "M012", "angle": "A052", "size": "S083", "lens_mm": 35, "composition": "C095",
    "focus": "deep", "transition_in": "X102", "reason": "Arrive in the storm from above before following one drop." } ] }
```
After the video is approved, append its shots (video slug, scene type, movement, angle, size) to
`direction/camera_history.json` in the project root.

## 7. Director self-check (before showing a draft)
Run `python3 <skill>/scripts/check_shotlist.py anim/direction/shotlist.json [direction/camera_history.json]` and fix
every error. Then watch the draft: does every move land on its word, is there one clear focus per shot, does every
chapter open differently, is anything static for more than ~4 s, is any move hard to read?
