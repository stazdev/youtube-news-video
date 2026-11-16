# Matching a reference animation ("make it move like this")

When the user gives a reference video or GIF and wants part of the episode to move like it. `SKILL.md` asks for one
at the end of Phase 1. Typical targets in a news episode: the intro sting, the paper-plane transition, the headline
type-on, the hero-word trail, the keyword ticks, a big-number count-up, a chart build, the outro, or a Short's hook. Methods adapted from NiazMorshed2007/reanimate and
rossark0/rossark-motion-skill (both MIT); the scripts are our own. All scripts run with the project venv:
`.venv/bin/python -I <skill>/scripts/<script>.py`.

## 0. Scope (write it before measuring)
Top of `anim/ref/<name>/spec.md`:
- **Target:** file + time range (+ crop) exactly as the user said it ("the first 3 s", "the orb part").
- **Fidelity:** **motion-faithful** (default): order, timing (±0.08 s), easing family, overshoot, travel relative to the
  element's size, stagger. Our art, the Cinematic Desk world, the brand palette and category accents, and our fonts stay ours.
  **Pixel-faithful** only for a private test, never for a published video: someone else's design is theirs.
- **Destination:** which component gets the motion (`TitleSting`, `PaperPlaneFold`, `KineticHeadline`, `TrailWord`,
  `CheckTick`, `BigNumber`, `Outro`, …). The match goes into that reusable component, so every later episode keeps it.
A YouTube or other link: download it only with the user's OK, into its own folder; never publish the reference.

## 1. Break it down: `ref_frames.py`
`ref_frames.py REF.mp4 --out anim/ref/<name> [--start --end --crop x:y:w:h]` → every frame at the source fps,
`sheets/timing_NN.png` (every frame, ~2 s per sheet) and `sheets/poses.png` (2 per second). Read **every** sheet:
the poses sheet shows *what* happens, the timing sheets show *how* (easing lives in the middle frames).

## 2. Measure: `track_motion.py` + `fit_easing.py` + `motion_compare.py` (self)
- **Cuts and sections:** `motion_compare.py anim/ref/<name> anim/ref/<name> --out .../self --no-align` lists the
  reference's cuts (scene changes) and moves with their times. References that never go still are split at their cuts.
- **Colours:** `track_motion.py <frames> --sample X,Y --at T` reads exact colours from pixels (for tracking; our
  palette stays our own unless the user asks for theirs).
- **Each moving element:** `track_motion.py <frames> --name orb --colors HEX,HEX --tol 35 --region x,y,w,h`
  (or `--not-bg HEX`). On glowing or busy references, **always give a `--region`** and colours unique to the element,
  otherwise glows, borders and text get mixed in. Check the printed visible-frame range makes sense.
- **Each move:** `fit_easing.py track_orb.json --prop cy --from A --to B` (one move per window, never across a cut)
  → start, end, duration in frames, easing family, overshoot, settle time and the Remotion `interpolate(...Easing.bezier(...))`
  line. Props: `cx cy` position, `w h` size/scale, `aspect` squash and stretch, `presence` fades/growth.
  Error ≤ 0.03 = a close fit; "no single ease fits" = split the window or it's a chain of poses (use `flow()` from
  `references/living_motion.md`).
- Small motion (a 2% squash, a 5 px float) is invisible on sheets but shows in the track numbers: read them.

## 3. Write the motion spec (one row per element per property; every row becomes a check)
```markdown
| # | element | property | from → to | start s | dur s (frames) | easing | overshoot | stagger / notes | source |
| 1 | sentence | width (zoom out) | 464 → 329 px | 0.80 | 0.40 (12) | easeInSine | 0% | after the last word lands | track_text + fit_easing |
| 2 | orb B | cy (drop) | 730 → 835 | 2.40 | 0.40 (12) | easeOutQuad | 0.5% | starts on cut 2 | track_orb_in + fit_easing |
| c | — | cuts | — | 1.77, 2.33, 2.90 | — | — | — | squeeze flashes | motion_compare self |
```
A "?" in a row means the frames haven't been read yet. Note what does **not** move as well.

## 4. Build
In Remotion with our components and brand. The voice still sets the timing: a matched move keeps its measured
duration and easing, but its start lands on our spoken beat from `timeline.json`. Copy timings as frames, easings as `Easing.bezier(...)` from the fitter,
chains of poses with `flow()`. Map sizes relative to the element (travel as a share of its size or of the frame),
not raw pixels, when our layout differs.

## 5. Compare and fix (2-5 rounds)
1. Render the same window (a draft at the same fps is fine).
2. `ref_frames.py OUR.mp4 --out anim/ours/<name> --like anim/ref/<name>/frames.json` (same window, crop, fps, size).
3. `motion_compare.py anim/ref/<name> anim/ours/<name> --out anim/ref/<name>/compare-N` → offset, every cut and move
   with start/end/duration/peak errors, PASS within ±0.08 s, `activity.png` (both curves) and
   `sheets/compare_NN.png` (reference | ours | difference). Read the sheets every round: numbers say *that* it's off,
   sheets say *what*.
4. For each spec row: track ours the same way and `fit_easing.py REF_TRACK --prop P --from A --to B --vs OUR_TRACK`
   → per-move timing PASS/FAIL and easing family match.
5. Fix the smallest thing the evidence points at, re-render, repeat. Write the final spec rows into that component's
   hero checklist (`references/hero_checklist.md`) so later episodes are checked against them too. After 5 rounds, report any row still failing with
   its numbers and reason; never loosen the tolerance silently.

| Symptom | Usual cause | Fix |
|---|---|---|
| everything shifted by the same offset | start delay | adjust the first beat's frame |
| ours shorter and front-loaded | easing too strong (expo vs cubic) | use the fitted bezier |
| reference overshoots, ours doesn't | spring/back vs plain ease | easeOutBack / a spring with the measured overshoot |
| an extra move or cut in ours | something animates that is still in the reference | remove or delay it |
| cut late or early | scene boundary on the wrong frame | move the transition to the reference's cut frame |

## 6. Report to the user
Fidelity, what was matched and what is ours, the last compare table (cuts and moves with errors, PASS/FAIL),
paths to `activity.png` and the compare sheets, and every remaining difference with its number and reason.

## Limits
- From a video we match **motion** of 3D references (camera timing, easing, object moves), not their models or materials.
- Colour tracking needs an element with distinct colours; on busy live-action footage rely on the activity curve,
  cuts and the sheets, and say the per-element numbers are less reliable.
- Fades of small text sit near the noise floor of the activity curve; measure them with `track_motion` (presence, w)
  instead.
