# Composition decider: how the video will look

Runs **first**, before timing and before the Director. It reads the **title**, the **script** and the **voice**, and decides
the video's format, every scene's depth (2D / 2.5D / 3D / Blender), environment, characters, colour and energy.
Output: `anim/direction/look.json` + a short human summary `anim/direction/look.md` shown to the user with the style frames.

## 1. Read the inputs
- **Title:** the promise of the video ("Why is the ocean salty?" → Earth science, places, water).
- **Script:** subject, settings mentioned, scale (micro / human / planetary / cosmic), time period, emotional arc,
  explicit art directions (`VISUALS:`, `LOOK:`, `CAMERA:`, colour words). Explicit directions always win.
- **Voice** (from step 1b; run a quick librosa pass first if needed): words per second, pause density, loudness
  variation, emphasis words. Calm narration (≤ 2.3 words/s, long pauses, low variation) → calm energy; brisk
  (≥ 2.8 words/s, frequent emphasis) → high energy; otherwise medium.
- **Channel bible**, if present: its brand pieces (sting, outro, cards, labels, Big Numbers, fonts, brand colours) stay
  fixed; this decider chooses everything else inside its rules.

## 2. Decide the format (whole video)
| Subject type (from title + script) | Default format |
|---|---|
| Places, nature, Earth science, geography, weather, oceans, space | **3D-led**: 3D environments, 2D graphics on top |
| Objects and machines ("how does X work") | **3D-led** with exploded views / cut-aways (X103, X104), isometric 3D for systems |
| Biology, chemistry, physics at micro scale | **3D-led** micro worlds (X117, X118) + 2D diagrams and formulas |
| History, culture, people's stories | **2.5D-led**: illustrated layers in depth + maps (D3) + archive-paper textures; 3D for key places |
| Abstract ideas, economics, statistics, psychology | **2D-led**: motion graphics, charts, kinetic type, over subtle 2.5D backdrops; 3D only for metaphors |
| Mixed | Hybrid: decide per scene with section 3 |
Then pick 1-3 **Blender hero shots** (the twist, the payoff, and/or the thumbnail) if the machine budget allows (see SKILL.md machine profile).

## 3. Decide each scene's depth
Use the Depth decision in SKILL.md: places and physical things → 3D (Blender if it is a hero shot), heavy illustration → 2.5D,
pure information → 2D on top of a 3D/2.5D setting when the scene has one. Record one reason per scene.

## 4. Decide the environment and characters (per scene)
- **Environment:** location, scale, time of day, weather, season, light direction, atmosphere (fog/haze density),
  taken from the script; if the script is silent, choose what best shows the idea, and keep continuity between
  neighbouring scenes (same coast, same sky, same time of day unless the story moves on).
- **Time of day and weather follow the story arc:** opening = clear, inviting light; tension/twist = deeper, darker,
  more contrast; payoff = warm golden light; reflection = soft dusk.
- **Characters:** only when a human (or animal) perspective helps understanding or warmth. Original, simple, consistent
  design across the video (same proportions, colours, outfit); low-poly 3D or 2D figures placed in 3D; never real
  people's likeness. One recurring character at most per video unless the script has several.
- **Recurring visual motif:** pick one object that travels through the story (e.g. a raindrop, a salt crystal) and use it
  in transitions and match cuts.

## 5. Colour (beautiful, story-matched, never neon)
### Hard rules
1. **No neon colours, ever,** unless the script explicitly asks for them (words such as "neon", "fluorescent",
   "glow-in-the-dark", "blacklight", "cyberpunk", "synthwave", "rave"); then neon is allowed **only** in the scenes that ask.
   *Neon* = any colour with OKLCH chroma ≥ 0.20 and lightness ≥ 0.62, or HSV saturation ≥ 0.90 with value ≥ 0.95
   (pure #00FF00, #FF00FF, #00FFFF, electric pink, acid yellow-green, laser blue). `scripts/check_palette.py` enforces it.
2. **Large areas** (sky, ground, water, backgrounds): OKLCH chroma ≤ 0.16. **Accents**: chroma ≤ 0.19, ≤ 10% of the frame.
3. **60-30-10:** dominant colour ~60%, secondary ~30%, accent ~10% of each frame.
4. **Max 5 colours plus neutrals per scene**; neutrals are tints/shades of the palette's own navy, white or warm grey.
5. **Text contrast** ≥ 4.5:1 against what it sits on (labels sit on pills to guarantee it).
6. **Natural light logic:** warm key light + cool shadows (or the reverse at night); one light temperature per scene.
7. **Brand pieces** (intro, outro, chapter cards, labels, captions, Big Numbers) use the Midnight Rose ground plus the video's **story theme** (5b);
   scene palettes are built to sit well next to them (shared ink/cream neutrals).

### Colour script (how colour follows the story)
Assign each chapter a mood from the library below and blend from one to the next over the transition. Typical arc:
inviting (clear day) → exploring (natural greens/blues) → mystery or danger (deep, desaturated, low-key) →
twist (strongest contrast of the video, still non-neon) → payoff (golden/warm) → outro (brand navy).
Match colour to what is happening: water = teals/blues, heat = ambers/terracotta, life = greens, age/history =
desaturated warm paper tones, space = deep indigo with soft lavender and gold, danger = deep red-browns, calm = dusk blues.

### Mood palette library (all pass `check_palette.py`; hex: dominant, secondary, tertiary, light, accent)
| Mood | Palette |
|---|---|
| ocean-day | #0E3B5C #1F7FB0 #7FC8E8 #F5F7FA #F2C14E |
| deep-sea | #071A2C #10324F #1E5B7A #A9D3E0 #E8A86A |
| golden-payoff | #2B2E4A #C8553D #E8955A #F7E6CC #F2C14E |
| forest | #1E3D2F #3F7448 #7FA65A #F3F0E6 #D9C38A |
| desert | #5A3D2B #B9713F #D9A15B #EFD9A7 #2E4A62 |
| volcanic | #2A1E1E #6B3A2E #C2502E #F2D6B8 #E8A33D |
| arctic | #1C3349 #4F7FA3 #A9D3E8 #E8F3F7 #D98F6B |
| storm | #1F2B38 #3C5166 #7D93A6 #C9D6E0 #E0B04F |
| archive-history | #3B3127 #7A6248 #B79E7E #E6D8BF #8C3B2E |
| cosmos | #0B1026 #1F2A55 #4A5A9A #C9B6E4 #F2C14E |
| body-biology | #3A1F2B #9C3D4A #D9817A #F2C2A8 #3F7F8C |
| clean-lab | #1F3A5F #3E7CB1 #9CC5E0 #F4F6F8 #E07A5F |
| technology | #15202B #2E4057 #4F7CAC #A7C4DE #E8A33D |
| farmland | #3E2F1F #7A5C3A #A8B45A #DCCB8E #4F8F5A |
| night-city | #141B2D #2C3A5A #5B6C99 #E7C07A #D9875F |
| dawn-hope | #2E3A59 #7F8FBF #E8A9A0 #F6D7A7 #FFF4E6 |
Adjust a library palette to the specific scene (e.g. sample a style reference image) but re-run the checker after any change.

## 5b. Story theme for the brand pieces (one per video)
Pick the theme that matches what the video is about and write it to `look.json` as `"story_theme"`. It colours the intro, outro, captions' active word, chapter cards, label dots, Big Numbers and Fact Badges on the shared Midnight Rose ground (ink `#0C0A0E`, plum `#1A1320`, cream `#F6F1EA`).
| Theme | Use for | deep · mid · light · cream · accent |
|---|---|---|
| ocean | seas, water, rain, rivers, ice melting | #0E4A52 #1E6E6E #A8E3D9 #F6F1EA #3FB0A2 |
| blood | heart, blood, body, medicine, animals' insides | #5E1A24 #8E2A34 #F2B0A8 #F6F1EA #C8464F |
| plants | plants, forests, food crops, ecosystems | #23472A #3F7448 #C5E3A5 #F6F1EA #6DAE5E |
| sand | deserts, sand, rocks, soil, archaeology | #5A3D2B #8A5E3C #EFD3A3 #F6F1EA #C98A4B |
| space | space, stars, planets, physics of the cosmos | #1F1A3A #3A3270 #CFC4F0 #F6F1EA #9C8CE0 |
| fire | fire, heat, volcanoes, energy, engines | #4A1E14 #7A3420 #F6C9A0 #F6F1EA #D9733A |
If a video spans several subjects, choose the one in the title. A new theme may be added when no row fits (e.g. "ice", "metal"): five colours in the same order, checked with `check_palette.py --hex`, then added to this table and to `STORY_THEMES` in `references/brand/IntroFluid.tsx`.

## 6. Energy and texture
- **Energy** (calm / medium / high) sets default move speeds, cut frequency (calm: new shot every 5-8 s; high: 2-4 s),
  and how often fast-family moves are allowed (calm: only on emphasis words, max 2 per video).
- **Texture:** channel grain on everything; history videos may add a subtle paper texture; space may add a fine star field.

## 7. look.json schema
```json
{ "title": "...", "story_theme": "ocean", "format": "3d-led", "energy": "calm", "words_per_second": 2.4,
  "neon_allowed_scenes": [],
  "motif": "raindrop",
  "chapters": [{ "n": 1, "mood": "storm", "palette": ["#1F2B38","#3C5166","#7D93A6","#C9D6E0","#E0B04F"] }],
  "scenes": [{ "id": "S04", "depth": "3d", "engine": "three", "hero_blender": false, "reason": "storm over sea cliffs is a place",
               "environment": "sea cliffs in rain", "time": "overcast day", "light": "cool key from upper left",
               "characters": [], "mood": "storm" }] }
```
Run `python3 <skill>/scripts/check_palette.py anim/direction/look.json` before style frames; fix every failure.
Show `look.md` (format, chapter moods with swatches, Blender hero shots, characters) to the user at the storyboard gate.
