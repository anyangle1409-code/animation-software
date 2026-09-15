# Gym shorts candidate — review

A clothing layer, not an anatomy or animation change. The shorts are a separate
skinned mesh added alongside the character's own; the body mesh, its weights and
the skeleton are untouched, and no exercise definition, curl motion, grip closure
or corrective was changed to accommodate them.

**Not promoted.** The bundled/default character is unchanged and both existing
GLBs are intact.

## Assets

| File | Body | SHA-256 |
|---|---|---|
| `HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` | proven v5, untouched | `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f` |
| `HomeGymPT_Male_SHORTS_CANDIDATE.glb` | proven v5 | `cdca3f3e3d05bf81181c2be8809ab2e62a03cdce33233082a245c4b275444dfa` |
| `HomeGymPT_Male_SHORTS_ON_HAND_WRIST_DEMO.glb` | hand/wrist weight candidate | `d0405ba7ec5a138ce466cd59071c5b27af467815e5a16dcc05335f8cf4e584ce` |

The primary shorts candidate is built on **proven v5**, so the garment can be
judged without the unapproved hand repair in the picture. The demo file is the
same garment over the hand/wrist candidate, for anyone who wants to see both at
once; the two changes stay independently reviewable because the garment is its
own mesh and the hand repair is only skin weights.

## Construction

The garment is a shell lifted off the character's own surface:

1. Body triangles whose vertices carry at least 90% of their weight on
   `DEF-spine`, `DEF-spine.001`, `DEF-pelvis.L/R`, `DEF-thigh.L/R` or
   `DEF-thigh.L/R.001` are taken as the covered region. The bone test matters:
   the character binds in an A-pose with the hands beside the hips, so a purely
   vertical band would have swept the fingers into the garment.
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

## The garment

- 1,380 vertices, 2,764 triangles (690 on the outer shell, 690 on the lining).
- Spans y 0.818 to 1.177 in model units: waistband just above the hip crest,
  hem at mid-thigh.
- Influenced only by hip and thigh bones, in this proportion:

| Bone | Share of total weight |
|---|---|
| `DEF-thigh.L` / `DEF-thigh.R` | 390.1 / 389.2 |
| `DEF-pelvis.R` / `DEF-pelvis.L` | 194.3 / 193.5 |
| `DEF-spine` | 72.4 |
| `DEF-thigh.R.001` / `DEF-thigh.L.001` | 48.4 / 48.4 |
| `DEF-spine.001` | 39.6 |
| `DEF-spine.002` | 4.1 |

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
close-ups at standing and deepest; and the curl bottom, shoulder press, push-up
bottom and pull-up. Observations:

- The waistband sits above the hip crest and stays there through the squat.
- The hem stays on the thigh and opens naturally as the knee comes forward; the
  leg openings do not collapse.
- Hip position, upper-thigh movement, squat depth, knee tracking and the quad
  silhouette all remain readable, which was the constraint the length and fit
  were chosen against.
- No floating cloth, no waistband distortion, no left/right asymmetry, and no
  contact with hands or equipment in any tested pose.
- The rear view on the `studio` backdrop is strongly backlit and is a poor
  surface for judging the seat; use `study` or `light` for that.

## Known issues and risks

- The −15 mm deep-squat reading at the front of the pelvis, above.
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
