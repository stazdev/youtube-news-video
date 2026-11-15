# Living motion: worlds that feel alive, moves that never stop dead

Numbers and rules adapted from rossark0/rossark-motion-skill (MIT); code below is our own. Use with
`channel_lessons.md` row 6 ("processes are shown happening, not as still objects").

## Rules
1. **A process is always visibly happening** while it's on screen: smoke rises, water flows, plumes billow, clouds drift. Use the recipes below; never a frozen prop in a "living" place.
2. **Never pass through an empty or dark frame.** A transition between two states or scenes overlaps them (the outgoing one is still ≥ 30-50% visible when the incoming one reaches 50%). `scripts/render_scan.py` fails any run of empty frames.
3. **Nothing appears from scale 0.** Entrances start at 0.6-0.9 scale (or from off-frame, already moving) with a fade; scale-from-0 pops read as cheap. Exception: liquid droplets born inside a gooey filter.
4. **Chains of poses flow; they don't stop at every key.** For a camera path or a character with several key poses, use `flow()` below (passes through every key with continuous speed and never overshoots). Plain `interpolate` with easing per segment stops dead at each key and reads robotic; Catmull-Rom splines can overshoot a key (camera dips below terrain, a value goes past its target).
5. **Follow-through by delay, not springs.** A child part reads its parent's value a little earlier: `child(t) += k · (parent(t − Δ) − parent(t))`, Δ = 60-150 ms (2-4 frames at 30 fps), k = 0.3-0.6. Tails, hair, leaves on a swaying stem, labels trailing a moving object, the second line of a title.
6. **Moving holds.** While something is held on screen it keeps a tiny idle layer (breathing ±1-1.5%, sway of a few degrees), except text being read and the title lock-up (held completely still, row 12).
7. **Variety without chaos.** Repeated items (raindrops, particles, trees, fish) get a seeded phase, period and size (`random('seed-'+i)`); nothing moves in sync and nothing is random per frame.
8. **One main action per shot, plus two or three quiet idle loops.** Side elements stay small in amplitude ("when unsure, halve it").
9. **Easing by role:** things that travel ease in-out `bezier(0.77, 0, 0.175, 1)`; things that arrive or open ease out `bezier(0.23, 1, 0.32, 1)`; only things leaving ease in, and exits are about half as long as entrances; endless loops (gears, conveyors, falling rain) are linear.

## Recipes (amplitudes and periods)
| Subject | Recipe |
|---|---|
| Plants, trees, kelp | sway 1.5-4° around the base over 3-6 s; leaves/fronds on seeded phases; tips lag the base (rule 5) |
| Smoke, steam, vent plumes | rise 8-14% of frame height per cycle, widen as they rise, fade in and out with a bell curve; 3-5 overlapping puffs on seeded phases |
| Fire, lava glow | lean 2-4° and stretch 3-6% on two waves of different periods (e.g. 0.7 s and 1.1 s); glow ±2-5% |
| Water surface | ripples grow and fade; floating things bob 1-2% and rock ±2°; river flow = scrolling UVs, linear |
| Rain, snow, bubbles | seeded linear `loop`s; snow sways sideways ±3%; bubbles wobble ±2% while rising and speed up slightly |
| Clouds, sky | drift across over 20-60 s with parallax (far slower); sun rays rotate one turn per 30-60 s |
| Lights, stars, screens | glow ±2-5% over 2-4 s; stars twinkle at seeded times |
| Machines, gears | turn linearly by gear ratio; a hand or pointer steps with ease-out |
| Cloth, flags | a wave travelling along the length, growing away from the fixed edge |
| Characters (simple) | breathing 1-2% over 3-5 s; a blink every 3-4 s (close ~110 ms, open ~190 ms); head tilt 3-6°; left and right never mirror each other |
| Icon or logo | plays once on appear, then rests (no endless spin during a read) |
| Chart | one-shot draw-on; bars staggered 40-80 ms |

## `flow()`: smooth, no-overshoot track through key poses
Copy into `anim/src/lib/flow.ts`. Keys are `[frame, value]` sorted by frame; hold a pose by repeating its value.
Monotone cubic (Fritsch-Carlson): continuous speed through every key, never past a key's value.

```ts
export type FlowKey = readonly [number, number];
export function flow(t: number, k: readonly FlowKey[]): number {
  const n = k.length;
  if (t <= k[0][0]) return k[0][1];
  if (t >= k[n - 1][0]) return k[n - 1][1];
  const d = (j: number) => (k[j + 1][1] - k[j][1]) / (k[j + 1][0] - k[j][0]);
  const m = (j: number) => {
    if (j === 0 || j === n - 1) return 0;                 // start and end at rest
    const a = d(j - 1), b = d(j);
    if (a * b <= 0) return 0;                             // local peak/valley or hold: flat tangent, no overshoot
    const h0 = k[j][0] - k[j - 1][0], h1 = k[j + 1][0] - k[j][0];
    const w1 = 2 * h1 + h0, w2 = h1 + 2 * h0;
    return (w1 + w2) / (w1 / a + w2 / b);                 // weighted harmonic mean keeps it monotone
  };
  let i = 0;
  while (k[i + 1][0] < t) i++;
  const h = k[i + 1][0] - k[i][0], s = (t - k[i][0]) / h;
  const h00 = 2 * s ** 3 - 3 * s ** 2 + 1, h10 = s ** 3 - 2 * s ** 2 + s, h01 = -2 * s ** 3 + 3 * s ** 2, h11 = s ** 3 - s ** 2;
  return h00 * k[i][1] + h10 * h * m(i) + h01 * k[i + 1][1] + h11 * h * m(i + 1);
}
// camera example: x, y, z each get their own flow(frame, keys) with the same key frames
```
Use it per channel (camera x/y/z, target x/y/z, fov, a character's lean, head, arm angle), then layer idle and follow-through on top:
`value = flow(f, KEYS) + idle(f) + k * (flow(f - D, PARENT) - flow(f, PARENT))`.
