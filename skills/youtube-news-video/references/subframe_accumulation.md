# Sub-frame accumulation: film-quality blur on a weak GPU (idea from Leonxlnx/cook, MIT)

Integrated GPUs often can't run postprocessing depth of field (it gave blank frames) and real-time
motion blur is fake. Instead, render **N sub-frames per output frame** and **average them** offline.
Each sub-frame is an ordinary, cheap Three.js frame, so it always works; quality comes from the averaging.

| Effect | What changes between the N sub-frames |
|---|---|
| **Motion blur** | time: each sub-frame samples a slightly later moment inside the shutter |
| **Depth of field** | the camera position moves on a small disc around its path while **looking at the same focus point**; things at the focus point stay sharp, everything else blurs |
| **Soft shadows / soft light** | the key light position moves on a small disc |
| **Anti-aliasing** | a sub-pixel camera offset (`camera.setViewOffset`) |

Use it **only on hero moments** (fast camera moves, close-ups with depth, Blender-like quality in Three.js):
render time is multiplied by N. Measure one second first and tell the user the estimate.

## 1. A sub-frame composition
Register a second composition for the hero stretch at `fps × N` (N = 8 is a good default; 4 for drafts):

```tsx
// src/lib/subframe.ts
export const SUB = 8;                                 // sub-frames per output frame
export const SHUTTER = 0.5;                           // 180° shutter: blur over half the frame interval
// Halton(2,3) points: evenly spread, deterministic (no Math.random)
const halton = (i: number, b: number) => { let f = 1, r = 0; while (i > 0) { f /= b; r += f * (i % b); i = Math.floor(i / b); } return r; };
export function subSample(subFrame: number, baseFps: number) {
  const out = Math.floor(subFrame / SUB), k = subFrame % SUB;             // output frame, sub-frame index
  const t = (out + (k / SUB) * SHUTTER) / baseFps;                        // scene time in seconds
  const a = 2 * Math.PI * halton(k + 1, 2), r = Math.sqrt(halton(k + 1, 3));
  return { out, k, t, frame: t * baseFps, disc: [Math.cos(a) * r, Math.sin(a) * r] as [number, number] };
}
```

In the hero scene, read time from `subSample(useCurrentFrame(), 30)` instead of the plain frame:
- **Motion blur:** drive every animation and the camera path with `s.frame` (a fractional frame).
- **Depth of field:** `camera.position += right * s.disc[0] * aperture + up * s.disc[1] * aperture`, then
  `camera.lookAt(focusPoint)`. `aperture` ≈ 0.02-0.08 scene units; larger = blurrier background.
- **Soft shadows:** `keyLight.position += (s.disc[0], 0, s.disc[1]) * lightRadius`.
- **Anti-aliasing:** `camera.setViewOffset(w, h, s.disc[0] * 0.5, s.disc[1] * 0.5, w, h)`.

Never use `Math.random()`; the Halton points keep every render identical.

## 2. Render and average
```bash
# render the hero stretch at 240 fps (30 x 8)
npx remotion render src/index.ts S07_hero_sub out/S07_sub.mp4 --crf=10
# average each group of 8 sub-frames into one 30 fps frame
ffmpeg -i out/S07_sub.mp4 -vf "tmix=frames=8:weights='1 1 1 1 1 1 1 1',framestep=8,setpts=N/30/TB" -r 30 \
  -c:v libx264 -crf 14 -pix_fmt yuv420p out/S07_hero.mp4
```
Change both 8s for another N. Then drop `S07_hero.mp4` into the master with `<OffthreadVideo>` in place of the live scene.
(Tested: a dot moving across the frame at 240 fps → `tmix` + `framestep` → a smooth 30 fps streak.)

## 3. Checks
- One-second test first: seconds per output frame × frames = estimate; tell the user before the full render.
- Beat sheet on the averaged clip (`scripts/beat_sheet.py`): the focus subject must stay sharp; only
  the background (DoF) or the moving parts (motion blur) soften.
- Text and labels are **never** rendered in the sub-frame composition (they'd smear); overlay them afterwards.
- Blender hero shots don't need this: Blender has its own motion blur and depth of field.
