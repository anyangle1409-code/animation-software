# Gym shorts candidate — review

A clothing layer, not an anatomy or animation change. The shorts are a separate
skinned mesh added alongside the character's own; the body mesh, its weights and
the skeleton are untouched, and no exercise definition, curl motion, grip closure
or corrective was changed to accommodate them.

**Promoted 2026-09-15**, after a waistband defect found in the deepest rear squat
was fixed (below). The garment ships over the promoted hand/wrist baseline.

## Assets

| File | Body | SHA-256 | Role |
|---|---|---|---|
| `HomeGymPT_Male_BASELINE_v6_SHORTS.glb` | baseline v6 | `0761fb048510a80ce4aa8835f05a0007697086dcc60cd46a1ddb6e8ccc47b0d6` | **shipped default** |
| `HomeGymPT_Male_BASELINE_v6.glb` | baseline v6 | `46180b5741216f823e4f1e0030a06d65fff0f10bd1d7b132e4c36a0814a410ed` | body alone, for deformation review |
| `HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` | proven v5 | `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f` | retained fallback, untouched |

Review copies built on v5 during the review, kept for reference:
`HomeGymPT_Male_SHORTS_CANDIDATE.glb` and
`HomeGymPT_Male_SHORTS_ON_HAND_WRIST_DEMO.glb`. The garment was reviewed on
**v5** deliberately, so it could be judged without the then-unapproved hand
repair in the picture; the two changes stayed independently reviewable because
the garment is its own mesh and the hand repair is only skin weights.

## How it is shipped

The two production binaries are large and stay out of the repository. They live
in `public/characters/`, which carries a `.gitignore` for `*.glb`, and
`src/character/bundled.ts` probes for them at startup and registers what it
finds: the dressed body as the default, the bare body alongside it so a
deformation review can still see the skin. Find neither and the studio keeps its
built-in procedural character, so a fresh clone still runs.

The probe asks for one byte with a `Range` header rather than issuing a `HEAD`:
static file middleware does not reliably answer `HEAD` for files served out of a
public directory, and the first version of this probe reported both present
assets as missing. It also checks the content type, because a dev server answers
a missing path with `index.html` and a 200 rather than a 404.

One further wrinkle, recorded because it is not obvious: registering the source
is not enough to select it. The character store captures the default source id
when its module is first evaluated, which happens before any asset probe can
finish, so `main.tsx` sets the choice explicitly once registration resolves.

## Construction

The garment is a shell lifted off the character's own surface:

1. Body triangles are taken as the covered region unless a corner carries more
   than 5% of its weight on an arm bone. Excluding the arms is necessary — the
   character binds in an A-pose with the hands beside the hips, so a purely
   vertical band would sweep the fingers into the garment — and excluding
   anything more is harmful: see the waistband defect below.
2. That patch is clipped to a waistband at y = 1.175 and a hem at y = 0.82 in
   model units — mid-thigh on a 2.02 m model. Clipping cuts the triangles rather
   than selecting whole ones, so the waistband and both leg openings are clean
   edges instead of a staircase of triangle boundaries.
3. The patch is pushed out along the body's own normals, smoothed, and closed
   with a lining and a rim, so it reads as cloth with an edge rather than as a
   sheet of paper.

**Skin weights are inherited from the body surface each garment vertex was
lifted from.** That is the whole reason no cloth simulation is needed: linear
blend skinning is linear, so a vertex sitting at `body + offset` with the body's
own weights lands at `skinned body + M·offset` in every pose. The standoff is
preserved by construction, in a deep squat exactly as in the bind pose. No new
bone was added and no existing weight was altered.

Three regions are treated differently, because a garment does:

| Region | Standoff | Minimum clearance | Treatment |
|---|---|---|---|
| Hips, seat, thighs | 11 mm | 6 mm | follows the body |
| Front panel | 19 mm | 13 mm | hangs clear, flattened |
| Inseam | 3.5 mm | 3.5 mm | follows the body between the legs |

The front panel is flattened by a relaxation pass that **only ever accepts a move
taking a vertex further from the skin**. The apex of any protrusion therefore
stays put while the surface around it rises to meet it: the panel flattens into
something a garment would do, and the pass cannot introduce a poke-through even
in principle. The inseam is deliberately excluded from that pass, so the cloth
drops between the legs instead of being pulled up into a flat bridge — an
earlier version did bridge, and left the perineum measurably outside the cloth.

Colour is carried as vertex colour, not as a material base colour, because the
viewport sets every material's colour to white; a `baseColorFactor` is
overwritten before it reaches the screen. Linear RGB (0.075, 0.079, 0.090) with
roughness 0.94 and zero metalness — a matte dark charcoal, no logo, no branding.

## The waistband defect, found at the last check

The deepest squat seen from behind was the one view not explicitly reviewed
before approval, and it was worth the look. The waistband came out as a **hard
sawtooth** — roughly eight triangle-sized teeth of bare skin biting down into the
garment across the lower back, plainly visible once the figure was lit from
behind on the rim-lit `void` backdrop. Every earlier rear capture had been shot
on a front-keyed backdrop, where the seat is in shadow and the edge cannot be
read at all.

It was not what it looked like. The waistband was not collapsing onto the body:
measured through the squat, the outer shell keeps 7.4 to 9.5 mm of standoff at
every frame. The cause was in the cut. A triangle is only usable when all three
of its corners pass the region test, and the original test demanded that a vertex
carry at least 90% of its weight on the hip and thigh bones. A triangle straddling
the waistband has its third corner further up the back, where the weights belong
to a higher spine bone — so that triangle failed and was dropped whole, and the
clean line the clip would have cut came out as a row of missing triangles instead.

The fix inverts the test: the region now excludes only what must be excluded,
which is the arms — the character binds in an A-pose with the hands beside the
hips, squarely inside the band the shorts are cut from — and keeps the torso
surface continuous. The waistband is a clean line at the deepest squat from
behind, from a rear three-quarter, and from above and behind.

Two smaller things were corrected in the same pass: the rim closing the hem and
waistband was wound from index-sorted edge keys, so half of it faced inwards and
was culled by single-sided rendering, and the lining floor was raised from 0.45×
to 0.7× of the local clearance.

## The garment

- 1,410 vertices, 2,824 triangles (705 on the outer shell, 705 on the lining).
- Spans y 0.818 to 1.177 in model units: waistband just above the hip crest,
  hem at mid-thigh.
- Influenced only by hip and thigh bones, in this proportion:

| Bone | Share of total weight |
|---|---|
| `DEF-thigh.L` / `DEF-thigh.R` | 391.2 / 390.3 |
| `DEF-pelvis.R` / `DEF-pelvis.L` | 203.0 / 202.2 |
| `DEF-spine` | 74.1 |
| `DEF-thigh.R.001` / `DEF-thigh.L.001` | 48.4 / 48.4 |
| `DEF-spine.001` | 46.7 |
| `DEF-spine.002` | 5.6 |

No spine bone above `DEF-spine.002`, no knee, no arm, no new bone.

## What the body did not do

Verified by direct comparison of the two files rather than by inspection:
`POSITION`, `NORMAL`, `TEXCOORD_0`, `TEXCOORD_1`, `COLOR_0`, `JOINTS_0`,
`JOINTS_1`, `JOINTS_2`, `WEIGHTS_0`, `WEIGHTS_1`, `WEIGHTS_2` and the index
buffer of the body mesh are **byte-identical**; 0 of 10,839 body vertices have
changed influences; the inverse bind matrices are identical; the skin's joint
list is identical; and of 162 nodes exactly one changed — the armature root,
which gained the garment as a hundredth child. No bone node was touched.

## Deformation validation

For every piece of skin the garment covers, the closest point on the garment's
outer surface is found — point to triangle, not point to vertex, because the
garment's vertices are 15-25 mm apart and a thigh can push between two of them —
and the side of the cloth that skin is on is recorded. Positive means the skin is
behind the cloth. Skin within 8 mm of the waistband or the hems is excluded: it
is outside the garment by design.

505 skin vertices, 14 frames per exercise, in studio millimetres:

| Exercise | Worst depth | At | Tightest gap | Samples behind the cloth |
|---|---|---|---|---|
| Bodyweight squat | −15.13 mm | 2.03 s (deepest) | 0.01 mm | 6,471 / 7,070 |
| Dumbbell curl | −2.65 mm | 0.00 s | 2.09 mm | 6,930 / 7,070 |
| Shoulder press | −2.66 mm | 0.00 s | 2.08 mm | 6,930 / 7,070 |
| Push-up | −2.33 mm | 2.42 s | 0.02 mm | 6,783 / 7,070 |
| Pull-up | −3.10 mm | 2.37 s | 0.04 mm | 6,815 / 7,070 |

Read honestly, that says: outside the squat, the worst the skin ever gets is
2–3 mm proud of the cloth, always in the gluteal cleft or at the perineum, where
the garment's triangles are far larger than the crease they span — a
discretisation reading rather than a visible hole, and nothing is visible at
those points in any render. The deepest squat reaches −15 mm at the front of the
pelvis (`v5654`, `v5464`), which is a real local excursion; it is likewise not
visible in the deep-squat front, side or hip renders, but it is the first thing
to check in review.

The Lunge and Leg Raise named in the review brief are not in the exercise set;
the bodyweight squat's deepest position is the strongest hip-flexion pose the
studio currently has, and is used in its place.

## Visual review

Front, side and rear at standing, half depth and deepest squat; hip and groin
close-ups at standing and deepest; the curl bottom, shoulder press, push-up
bottom and pull-up; and — for the final check — the deepest squat from behind,
from a rear three-quarter and from above and behind, on the rim-lit `void`
backdrop. Observations:

- The waistband sits above the hip crest and stays there through the squat.
- The hem stays on the thigh and opens naturally as the knee comes forward; the
  leg openings do not collapse.
- Hip position, upper-thigh movement, squat depth, knee tracking and the quad
  silhouette all remain readable, which was the constraint the length and fit
  were chosen against.
- No floating cloth, no waistband distortion, no left/right asymmetry, and no
  contact with hands or equipment in any tested pose.
- The seat is covered through the whole squat, the gluteal cleft shows no break,
  and the waistband is a clean line after the fix above.
- **Judge the rear on the `void` backdrop.** All four backdrops key the figure
  from the front, so on `studio`, `light` and `study` alike the seat falls into
  shadow and a rear view shows almost nothing. `void` is rim-lit and is the only
  one that reaches the figure from behind. That cost this review a round.

## Front-crotch refinement candidates — awaiting review

The promoted garment's front still reads as too anatomical below the flattened
panel. Three shorts-only candidates address it; the body is byte-identical to
baseline v6 in all three, so this stays independently reviewable from the
shoulder work. **None is promoted.**

| Candidate | Midline prominence | Worst push-up containment | SHA-256 |
|---|---|---|---|
| promoted (current) | 8.26 mm | −2.33 mm | `0761fb04…b0d6` |
| F1 — mild | 6.64 mm | −12.29 mm | `b20237ca57a2b59227428d54e83267eba3d635e67d7fcd04f8009fde7216e2e8` |
| F2 — medium | 5.15 mm | −6.13 mm | `57145f8c2e7b058e6e1c5ee42ee41fbeecdc9283189b73924a5f5b758ef05dd4` |
| F3 — strong (**preferred**) | **5.10 mm** | **−2.33 mm** | `aedbe91fd957b865c81ee85b1e4858e1872b406814b190ecac76e130adcc917b` |

Prominence is how far the garment's front midline stands proud of a straight line
drawn from the waistband down to the inseam — the bulge as the eye reads it.

**The first three attempts went the wrong way.** Raising the front panel's
standoff and clearance from 19/13 mm to 31/22 mm made the prominence *worse*,
8.26 → 11.73 mm, because the clearance floor is enforced per vertex against that
vertex's own patch of skin: the floor is therefore a scaled copy of the anatomy,
and raising it inflates the shape rather than flattening it.

The real fault was in which region owned the lower front. The inseam was selected
by height and midline distance alone, so it claimed the front of the garment as
well as the part that runs between the legs — and the inseam is deliberately
tight, 3.5 mm, which shrink-wrapped exactly the area in question. Gating the
inseam on depth as well, so it only owns what is actually between the legs, and
letting the flattened front panel reach further down, fixes it with the standoff
left at the promoted values.

Containment is the reason F3 is preferred over F2 rather than the other way
round. Flattening further pushes the panel further off the body everywhere, so
the strong candidate is also the safest: F1 and F2 introduce push-up breaches of
−12.29 mm and −6.13 mm that the promoted garment does not have, while F3 matches
the promoted figure exactly. Squat, curl and press containment are unchanged
across all three, including the −15 mm deep-squat reading, which none of them
affects.

F3 was checked through curl peak, shoulder press, push-up bottom and the deepest
squat, front and side. The deep-squat result is unchanged.

## Known issues and risks

- The −15 mm deep-squat reading at the front of the pelvis, above. Unchanged by
  the waistband fix, and still not visible in the front, side or hip crops at the
  deepest squat — but it remains measured rather than explained, and a low
  front-three-quarter close-up at 2.20 s would settle it.
- The 2–3 mm readings in the gluteal cleft and at the perineum.
- The garment inherits the body's weights exactly, so it also inherits the body's
  behaviour: where the body self-intersects in a deep squat, the cloth follows.
- The hem is a horizontal cut in the bind pose, so it is a true horizontal line
  on a standing figure and tilts with the thigh, as a real hem does. It was not
  shaped to a curve; if a curved hem is wanted, that is a separate pass.

## Explicitly not addressed here

Kept documented and unchanged, per the review brief: the ~6 mm inner
dumbbell/thigh overlap at the curl bottom, the palm gap, weak thumb opposition,
85% global grip closure and the 0% elbow outer corrective. None of them was
touched, and the shorts were not used to conceal any of them.
