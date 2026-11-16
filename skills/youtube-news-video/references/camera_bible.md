# Camera bible: 130 movements, angles, shot sizes and compositions

Entries 001-100 follow the user's "Filmmaker's Camera Playbook". Entries 101-130 are additions for animated explainers.
Every shot in a video is described with codes from this file (see `director.md`).

**Engines:** 2D = Remotion SVG/HTML with the CameraRig and parallax layers; 3D = Three.js (`@remotion/three`); BL = Blender (not used by this skill; ignore that column).
✓ = native; ~ = approximated (2.5D trick described); ✗ = not available in that engine.
**Units:** times in seconds; 3D distances relative to subject size S (S = the subject's bounding-sphere radius); 2D scales are camera-group scales.
**Families** (used by the uniqueness rules): `push` (toward), `pull` (away), `travel` (lateral/along), `orbit`, `vertical`, `aerial`, `fast`, `lens`, `focus`, `reveal`, `roll`, `pov`, `static`.

## 1. Movements (M)

| ID | Name | Family | Use for (motivation) | 2D | 3D | BL | Recipe |
|---|---|---|---|---|---|---|---|
| M001 | Dolly In | push | focus, intimacy, "look closer" | ✓ | ✓ | ✓ | 3D: camera moves 25-40% of its distance toward target over 2-4 s, inOutCubic, fov fixed. 2D: scale 1.00→1.10, layers by depth factor |
| M002 | Dolly Out | pull | release, context, ending a thought | ✓ | ✓ | ✓ | reverse of M001; end wider than start by 30-60% |
| M003 | Push In | push | build intensity toward a key word | ✓ | ✓ | ✓ | slower than M001: 4-8% (2D) / 15% distance (3D) over the whole shot, linear-ish (inOutSine) |
| M004 | Pull Back Reveal | pull | detail → big picture, surprise of scale | ✓ | ✓ | ✓ | start tight (2D scale 1.6-3; 3D 1.2 S away) and ease out to wide over 2.5-4 s, outCubic; reveal lands on the beat |
| M005 | Tracking Shot | travel | journeys, processes in motion | ✓ | ✓ | ✓ | camera position = subject position + fixed offset; subject stays at a third line |
| M006 | Side Tracking | travel | timelines, conveyor processes, side-by-side comparison | ✓ | ✓ | ✓ | camera moves parallel to subject path, 90° to direction of travel; 2D parallax truck |
| M007 | Follow Shot | travel | following a drop/particle/animal | ~ | ✓ | ✓ | behind subject on its spline with 0.15-0.3 s lag and look-ahead 5% of path |
| M008 | Lead Shot | travel | something advancing toward us (wave, lava, crowd) | ~ | ✓ | ✓ | camera ahead of subject, moving backward at its speed, looking back at it |
| M009 | Orbit Shot | orbit | showing an object's shape (organ, crystal, machine) | ~ | ✓ | ✓ | 20-90° around target, radius constant, lookAt target; 2D ~ rotate 3/4 illustration layers |
| M010 | 360-Degree Orbit | orbit | hero object fully explained, "all sides" | ✗ | ✓ | ✓ | full turn in 8-12 s, slight elevation 10-20°; max once per video |
| M011 | Crane Up | vertical | rising: from ground to sky, from detail to setting | ✓ | ✓ | ✓ | camera Y rises 2-6 S with slight pitch-down to keep subject; parallax by layer |
| M012 | Crane Down | vertical | arriving, settling into a place, sinking | ✓ | ✓ | ✓ | reverse of M011; good scene opener |
| M013 | Jib Shot | vertical | graceful arc over a scene | ~ | ✓ | ✓ | camera on an arc (rise + lateral 20-40°) around a pivot |
| M014 | Pedestal Up | vertical | measuring height (towers, layers, sea level) | ✓ | ✓ | ✓ | pure vertical move, no pitch change |
| M015 | Pedestal Down | vertical | descending through layers (strata, ocean depth) | ✓ | ✓ | ✓ | pure vertical move down; pair with depth gauge |
| M016 | Aerial Flyover | aerial | landscapes, rivers, coastlines | ~ | ✓ | ✓ | high (20-60 S), slow forward glide, pitch -20 to -45° |
| M017 | Top-Down Descent | aerial | maps to ground, "here is where" | ✓ | ✓ | ✓ | camera looks straight down and descends; 2D = scale up a top-down map |
| M018 | Fly-Through | aerial | travelling through an environment | ~ | ✓ | ✓ | spline through the space 1-3 S above terrain, banking ≤ 10° on turns |
| M019 | FPV Fly-Through | fast | adrenaline, speed, energetic hooks | ✗ | ✓ | ✓ | low and fast (2-3× M018 speed), bank 15-30°, fov 70-90; ≤ 3 s; never in calm videos |
| M020 | Sweeping Reveal | reveal | grand openings, chapter openers | ~ | ✓ | ✓ | wide lateral arc + rise that ends on the hero composition |
| M021 | Handheld Movement | fast | tension, urgency, "being there" | ✓ | ✓ | ✓ | add noise offset 2-6 px (2D) / 0.5-1% S (3D) at 0.6-1.2 Hz, rotation ±0.5°; seeded |
| M022 | Steadicam Tracking | travel | smooth walk-through of a space | ~ | ✓ | ✓ | M005 with tiny vertical bob 0.3% S at walking rate |
| M023 | Whip Pan | fast | jump between two places, transition | ✓ | ✓ | ✓ | 8-12 frames horizontal, motion blur, land with tiny overshoot |
| M024 | Whip Tilt | fast | sky ↔ ground, surface ↔ depth | ✓ | ✓ | ✓ | vertical version of M023 |
| M025 | Dutch Roll | roll | disorientation, something goes wrong | ✓ | ✓ | ✓ | roll 5-15° over 1-2 s around lens axis |
| M026 | Crash Zoom | lens | shock, sudden revelation | ✓ | ✓ | ✓ | fov narrows 50% (3D) / scale ×1.6 (2D) in 6-8 frames, outExpo, no settle |
| M027 | Slow Zoom In | lens | quiet attention, documentary feel | ✓ | ✓ | ✓ | fov -10 to -20% over the whole shot; camera still |
| M028 | Slow Zoom Out | lens | reflection, context | ✓ | ✓ | ✓ | fov +10 to +20% over the shot |
| M029 | Dolly Zoom (Vertigo) | lens | "wait, what?!" twist | ✓ | ✓ | ✓ | camera distance d and fov change so d·tan(fov/2) stays constant; 2D: background scales up while subject counter-scales; max once per video |
| M030 | Snap Zoom | lens | emphasis on a key word / Big Number | ✓ | ✓ | ✓ | 8-12 frames to ×1.3-1.5, outExpo, hold, settle 0.5 s |

## 2. Creative and advanced movements (M)

| ID | Name | Family | Use for | 2D | 3D | BL | Recipe |
|---|---|---|---|---|---|---|---|
| M031 | Rack Focus | focus | shift attention label ↔ object, cause ↔ effect | ✓ | ✓ | ✓ | 15-25 frames; 2D blur fore/back layers; 3D DepthOfField focusDistance; BL camera DoF |
| M032 | Focus Pull | focus | follow a subject moving in depth | ✓ | ✓ | ✓ | focus distance tracks subject distance each frame |
| M033 | Parallax Movement | travel | depth in illustrated/2.5D scenes | ✓ | ✓ | ✓ | lateral move; layers far 0.3 / mid 0.6 / near 1.0 / fg 1.4 |
| M034 | Arc Shot | orbit | following a conversation/process around a point | ~ | ✓ | ✓ | 30-120° arc on a radius, keeps subject centred |
| M035 | Spiral Movement | orbit | diving in or rising out (deep sea, into the ground) | ~ | ✓ | ✓ | descend/ascend + rotate ≤ 20° + push-in |
| M036 | Boom Sweep | vertical | big environment reveal with energy | ~ | ✓ | ✓ | rise or fall while moving laterally 1-2 S/s |
| M037 | Counter Orbit | orbit | dynamic hero object (model turns one way, camera the other) | ✗ | ✓ | ✓ | object rotY +θ, camera orbit −θ/2 |
| M038 | Reverse Tracking | travel | subject advancing toward viewer | ~ | ✓ | ✓ | as M008 but camera keeps more distance, slower |
| M039 | Reveal Behind Object | reveal | discovering something hidden | ✓ | ✓ | ✓ | start with foreground object covering 60-90% of frame, slide out laterally |
| M040 | Foreground Wipe | reveal | cut or reveal masked by a passing object | ✓ | ✓ | ✓ | near object crosses lens; cut happens while it covers the frame |
| M041 | Low-to-High Reveal | reveal | awe, scale (mountains, towers, volcano) | ✓ | ✓ | ✓ | start near ground looking up, rise to reveal |
| M042 | High-to-Low Reveal | reveal | uncovering a detail on the ground | ✓ | ✓ | ✓ | start high, descend to the detail |
| M043 | Under-Object Tracking | travel | moving beneath bridges, waves, roots | ✗ | ✓ | ✓ | camera passes under a structure, light changes |
| M044 | Over-the-Shoulder Push-In | push | character looking at something we explain | ~ | ✓ | ✓ | start behind character's shoulder, push toward what they see |
| M045 | POV Movement | pov | "imagine you are…", being the particle/animal | ✓ | ✓ | ✓ | camera = subject's eyes, gentle bob, fov 70-80 |
| M046 | Snorricam Shot | pov | disorientation, being carried along | ✗ | ✓ | ✓ | camera locked to subject, world swings around |
| M047 | Dutch Tilt Movement | roll | creeping unease | ✓ | ✓ | ✓ | slow roll 0→5° over the shot |
| M048 | Roll Shot | roll | weightlessness, space, spinning | ✓ | ✓ | ✓ | continuous roll 30-180° |
| M049 | One-Take Continuous Movement | travel | a whole process in one shot | ~ | ✓ | ✓ | one spline through several stations with beat-timed stops; ≤ 1 per video |
| M050 | Transition Through Aperture | reveal | entering: window, cave, cell membrane, mouth of a river | ✓ | ✓ | ✓ | push through an opening; next scene starts inside (zoom-through) |

## 3. Angles and perspectives (A)

| ID | Name | Use for | Recipe (3D camera height / pitch; 2D horizon) |
|---|---|---|---|
| A051 | Extreme Low Angle | power, threat, majesty | camera at 2-5% subject height, pitch +25-45°; 2D horizon low (80-90% down), subject scaled tall |
| A052 | High Angle | vulnerability, overview | camera above, pitch -25 to -45° |
| A053 | Bird's-Eye View | maps, layouts, patterns | pitch -80 to -90° |
| A054 | Worm's-Eye View | towering scale (trees, rockets, waves) | at ground, pitch +60-80°, wide fov 60-80 |
| A055 | Eye-Level Angle | neutral, explanatory default | camera at subject mid-height, pitch 0±5° |
| A056 | Dutch Angle | instability, error, danger | roll 8-20° held |
| A057 | Over-the-Shoulder (OTS) | relationship between observer and subject | foreground shoulder/silhouette 20-35% of frame |
| A058 | POV Angle | immersion | camera at the subject's eye position |
| A059 | Profile Angle | shape, silhouette, side process | subject 90° to camera |
| A060 | Three-Quarter Angle | most informative view of an object | subject turned ~45°; default for 3D hero objects |
| A061 | Front-Facing Angle | direct address, symmetry, data | subject faces lens |
| A062 | Rear Angle | following, journeys, anticipation | camera behind subject |
| A063 | Back Three-Quarter Angle | journey with context ahead | behind and 30-45° to one side |
| A064 | Side Low Angle | heroic profile, dynamic movement | low and from the side, pitch +10-20° |
| A065 | Side High Angle | process overview from the side | high and from the side, pitch -20-35° |
| A066 | Ground-Level Angle | small worlds (insects, raindrops, sand) | lens a few % above ground |
| A067 | Shoulder-Level Angle | conversational, human scale | ~1.5 m equivalent |
| A068 | Waist-Level Angle | observational | ~1 m equivalent |
| A069 | Knee-Level Angle | playful, child's view | ~0.5 m equivalent |
| A070 | Hip-Level Angle | casual action | ~0.9 m equivalent |
| A071 | Canted Perspective | off-balance, surreal | roll 5-10° + asymmetric framing |
| A072 | Through-the-Legs Angle | playful framing of a scene beyond | foreground arch (legs, rock arch, table legs) |
| A073 | Reflection Angle | duality, water, glass | 3D: mirrored copy under a water plane / reflective material; 2D: flipped layer at 30-50% opacity |
| A074 | Through-Glass Angle | lab, aquarium, window, microscope | glass layer with subtle reflections/streaks in front |
| A075 | Obstructed Foreground Angle | discovery, voyeur, depth | foreground leaves/rocks partly covering 15-40% of frame |

## 4. Shot sizes and framing (S)

| ID | Name | Use for | Recipe (subject height as % of frame height) |
|---|---|---|---|
| S076 | Extreme Close-Up (ECU) | texture, a single detail | detail fills 80-100% |
| S077 | Close-Up (CU) | key subject detail | 60-80% |
| S078 | Medium Close-Up (MCU) | character head+shoulders / object top half | 45-60% |
| S079 | Medium Shot (MS) | character waist up / object with some context | 35-50% |
| S080 | Medium Long Shot | character knees up / object + surroundings | 30-40% |
| S081 | Full Shot (FS) | whole subject | 70-85% (whole body/object visible) |
| S082 | Wide Shot (WS) | subject in its environment | 20-35% |
| S083 | Extreme Wide Shot (EWS) | scale, establishing, landscapes | < 10% |
| S084 | Cowboy Shot | character mid-thigh up | 40-50% |
| S085 | Knee Shot | character knees up | 35-45% |
| S086 | Two-Shot | two subjects compared | both in frame, rule of thirds |
| S087 | Three-Shot | three items/steps | triangle composition |
| S088 | Group Shot | many items (ions, cells, people) | cluster with one focal element |
| S089 | Insert Shot | an important object/action detail | brief 1-2 s |
| S090 | Cutaway Shot | related detail away from main action | brief, returns to main |

## 5. Composition and specialty shots (C)

| ID | Name | Use for | Recipe |
|---|---|---|---|
| C091 | Silhouette Shot | mood, dawn/dusk, mystery | subject dark against bright sky/back light; rim light only |
| C092 | Symmetrical Shot | order, science, calm authority | subject on centre axis; mirror-balanced elements |
| C093 | Asymmetrical Composition | energy, tension | subject on a third; weight balanced by negative space |
| C094 | Negative Space Shot | loneliness, scale, room for text | subject ≤ 20% of frame, large empty area (good for Big Numbers) |
| C095 | Leading Lines Shot | guide the eye (rivers, roads, rays) | lines converge on the subject |
| C096 | Frame Within a Frame | focus through arches, windows, lenses | foreground frame shape around subject |
| C097 | Deep Focus Shot | everything matters (systems, landscapes) | no DoF blur |
| C098 | Shallow Depth of Field Shot | isolate subject | strong DoF; background blur 6-12 px (2D) |
| C099 | Split Diopter Shot | two depths both sharp (cause + effect) | two layers sharp, middle blurred; or split frame |
| C100 | Forced Perspective Shot | playful scale comparisons | near small object aligned with far big one |

## 6. Additions for animated explainers (X)

| ID | Name | Family | Use for | 2D | 3D | BL | Recipe |
|---|---|---|---|---|---|---|---|
| X101 | Continuous Scale Zoom (Powers of Ten) | push | rock → mineral → atom; city → cell | ✓ | ✓ | ✓ | exponential zoom scale = e^(k·t) through nested levels, cross-fade levels as each fills the frame; signature move |
| X102 | Zoom-Through Transition | push | into a droplet/cell/window → next scene | ✓ | ✓ | ✓ | push until a shape fills the frame; next scene starts inside it |
| X103 | Cut-Away Slice | reveal | showing inside (Earth layers, volcano, organ) | ✓ | ✓ | ✓ | clipping plane / mask sweeps across the object on the beat |
| X104 | Exploded-View Orbit | orbit | how a device works | ~ | ✓ | ✓ | parts separate along one axis while camera orbits 30-60° |
| X105 | Time-Lapse Orbit | orbit | change over time (day/night, seasons, erosion) | ~ | ✓ | ✓ | slow orbit while sun/sky/geometry animate fast |
| X106 | Bullet-Time Freeze Orbit | orbit | freezing a fast event (splash, eruption) | ✗ | ✓ | ✓ | scene time stops, camera orbits 60-120°, time resumes |
| X107 | Hyperlapse Forward | travel | long journeys compressed | ~ | ✓ | ✓ | fast forward travel with stabilised horizon, periodic small jumps |
| X108 | Macro Slider | travel | tiny worlds: salt crystals, insects, sand | ~ | ✓ | ✓ | slow lateral 2-5% S/s at ground level with shallow DoF |
| X109 | Tilt-Shift Miniature | aerial | everyday places as tiny worlds | ~ | ✓ | ✓ | high angle, strong DoF bands top/bottom, slightly sped-up motion |
| X110 | Ghost Glide | travel | passing through solid matter (into rock, through a wall) | ✗ | ✓ | ✓ | camera moves through a surface with a cut-away clip sphere around the lens |
| X111 | Map Flight | aerial | travelling between places on a map | ✓ | ✓ | ✓ | top-down camera travels A→B along a route line that draws on |
| X112 | Globe Fly-To | aerial | "here on Earth": globe → region | ✓ | ✓ | ✓ | orbit globe, then descend and tilt toward the region; hand off to terrain |
| X113 | Satellite Zoom-Down | aerial | space to street in one move | ~ | ✓ | ✓ | continuous descent through cloud layer, map → terrain → ground |
| X114 | Underwater Surfacing | vertical | leaving the deep, coming up for air | ~ | ✓ | ✓ | rise through the water surface; split-level frame at the crossing |
| X115 | Dive Under Surface | vertical | entering the ocean/lake | ~ | ✓ | ✓ | descend through the surface; colour/fog changes at the crossing |
| X116 | Ride the Beam | travel | following light, a signal, a current | ~ | ✓ | ✓ | camera follows a moving light/energy pulse along its path |
| X117 | Particle POV | pov | being a molecule, ion, blood cell | ~ | ✓ | ✓ | M045 at micro scale with surrounding particles flowing past |
| X118 | Microscope Drift | focus | cells, crystals under a lens | ✓ | ✓ | ✓ | circular vignette, slow drift + occasional focus breathing |
| X119 | Multi-Plane Rack | focus | moving attention across 3+ depth planes | ✓ | ✓ | ✓ | sequential rack focus through layered planes on beats |
| X120 | Sun Flare Reveal | reveal | warmth, hope, payoff | ✓ | ✓ | ✓ | camera moves until sun peeks past an edge; soft flare/glow (no lens-flare clichés) |
| X121 | Silhouette Pass | reveal | dramatic transition | ✓ | ✓ | ✓ | dark foreground silhouette passes across a bright background |
| X122 | Impact Shake | fast | eruptions, lightning, collisions | ✓ | ✓ | ✓ | decaying noise offset ≤ 12 px / ≤ 0.5 s |
| X123 | Breathing Drift | static | idle default on otherwise still shots | ✓ | ✓ | ✓ | 1-2% noise wander of position/scale |
| X124 | Snap-and-Settle | fast | lists, step reveals | ✓ | ✓ | ✓ | quick reframe to each item with overshoot 3-5% |
| X125 | Pendulum Swing | orbit | balance, comparison, back-and-forth | ~ | ✓ | ✓ | camera swings ±15-25° around a pivot, decaying |
| X126 | Parallax Panorama | travel | wide illustrated panoramas (2.5D) | ✓ | ✓ | ✓ | long lateral move across a 3-4× wide layered world |
| X127 | Vertical Scroll | vertical | tall infographics, depth/height scales | ✓ | ✓ | ✓ | camera scrolls down/up a tall composition with labelled stops |
| X128 | Spline Chase | travel | chasing a fast subject (bird, drop, ion) | ~ | ✓ | ✓ | camera chases on the subject's spline with variable lag for tension |
| X129 | Macro-to-World Reverse | pull | from a tiny detail out to the whole planet | ✓ | ✓ | ✓ | inverse of X101 |
| X130 | Split-Screen Dual Move | travel | before/after, two places at once | ✓ | ✓ | ✓ | two panels, each with its own complementary move (one push, one pull) |

## Lens guide (3D fov vertical / Blender mm on full-frame)
| Look | fov | mm | Use |
|---|---|---|---|
| Ultra-wide | 70-90° | 14-18 | FPV, worm's-eye, cramped spaces |
| Wide | 50-65° | 24-28 | environments, establishing |
| Normal | 35-45° | 35-50 | explanation default |
| Portrait | 20-30° | 85-100 | hero objects, compression, shallow DoF |
| Telephoto | 8-15° | 135-300 | stacked layers, heat haze, vertigo endpoints |

## Signature moves (each at most once per video)
M010 360-Degree Orbit, M019 FPV Fly-Through, M026 Crash Zoom, M029 Dolly Zoom, M049 One-Take, X101 Powers of Ten, X106 Bullet-Time, X110 Ghost Glide, X113 Satellite Zoom-Down.
