# MPFB experimental male benchmark M9 (3 Nov 2026)

**Status:** an experimental reference. It is **not approved** and **not production**.

- W12c, ST_a and M9 are all unapproved.
- Production, `PT_MODEL_VERSION` 1.0, the canonical skeleton and PT-App are unchanged.
- Work is on branch `claude/mpfb-athletic-male-20261103`.
- Next step: **the owner's visual approval gate** (see the end).

## Where this ran

It ran in the Claude cloud session. Your Windows laptop could not be reached from this session: no Remote Control folders were available. The tools were:

- Blender 5.2.1 LTS (`bpy` module);
- MPFB 2.0.18, installed as a Blender extension (`bl_ext.user_default.mpfb`) from `makehumancommunity/mpfb2` at commit `6ff1eb35`. It is enabled and generates humans through `HumanService` / `TargetService` / `HumanObjectProperties`.

`static.makehumancommunity.org` and `download.blender.org` were refused by this environment's proxy. The base mesh, targets, rigs and weights MPFB needs are bundled in its git repository, so no download was required.

## Files

| File | What |
|---|---|
| `comparison_W12c_STa_M9_no_photos.jpg` | W12c / ST_a / M9; front, 3/4, side (mirrored to face like the photos) and back. All in the same relaxed stance, camera, light and material. The photo column is left out of git (your rule: no reference photos in git, and this repo is public); the full four-column sheet with the photos was sent directly in the conversation |
| `renders_M9/` | Standalone M9 renders: four full-body views and four upper-body close-ups, 720×1280 |
| `DIMENSIONS_WORKSHEET_filled.csv` | Your worksheet. `current_rig_mm` / `current_mesh_mm` = W12c, `new_candidate_mm` = M9; ST_a is in the notes |
| `measurements/*.json` | Per model: every measure, the blend's SHA-256 and the pose. `image_silhouette_widths_low_confidence.txt` holds the photo silhouette ratios |
| `mpfb_M9_params.json` | The exact MPFB settings. Rebuild with `scripts/mpfb_experimental/build_mpfb_candidate.py -- mpfb_M9_params.json <out>` |

The `.blend` files stay out of git, under your earlier rule of no `.blend` files in git. M9 is fully reproducible from the parameters file plus MPFB `6ff1eb35`. The blend's SHA-256 is in `measurements/MPFB_M9.json`.

## Measurements (mm, from the models; not from the photographs)

**Method:** `scripts/mpfb_experimental/measure_worksheet.py`.

- Horizontal sections of the evaluated mesh. Circumference is a convex hull, which approximates a tape measure.
- W12c and ST_a are measured in their bind pose, MPFB in the stand pose. Bideltoid breadth and wrist height depend on the arm pose.
- **UNKNOWN:** biacromial breadth (there is no acromion landmark; GH-centre spacing is given instead) and head height.
- `scripts/body_v2/fit/proportions.py` (the ANSUR II script named in the pack) **is not on this branch**, so no ANSUR comparison was run. It needs locating, perhaps on `work/phone-blender-workbench-20261023`.

| Measure | W12c | ST_a | MPFB M9 |
|---|---|---|---|
| Stature (sole to vertex) | 1856 | 1856 | 1863 |
| Bideltoid breadth | 604 | 600 | 553 |
| Chest breadth / depth / circumference (0.72 H) | 363 / 274 / 1121 | same | 348 / 266 / 1014 |
| Waist breadth / depth / circumference | 304 / 230 / 870 | same | 277 / 252 / 858 |
| Hip breadth | 412 | 412 | 349 |
| Bideltoid / waist (3D) | 1.99 | 1.98 | 2.00 |
| GH-centre spacing | 438 | 438 | 384 |
| Upper arm / forearm (rig) | 300 / 293 | same | 272 / 274 |
| Thigh / lower leg (rig) | 415 / 430 | same | 470 / 451 |
| Thigh circumference, upper / lower | 698 / 562 | 699 / 594 | 565 / 504 |
| Calf, maximum circumference | 471 | 471 | 428 |
| Foot length | 295 | 295 | 272 |

**Stature (1820 vs about 1857):**

- The current Body v2 mesh (W12c) measures **1856 mm** from sole to vertex, which matches the historical 1857–1858 reports.
- The app's canonical rig declares `RIG_HEIGHT = 1.75` (`src/rig/humanoid.ts`).
- 1820 mm is not met by either. It stays **PROVISIONAL**. Choosing between them is **your decision**, and nothing was rescaled. M9 was scaled to 1856 mm so the comparison is like for like.

**Skeleton:** MPFB's own skeleton has a longer thigh (470 vs 415 mm) and a shorter upper arm (272 vs 300 mm) than the canonical rig. An independent production body has to be fitted to the **canonical** skeleton, not MPFB's. Its proportions will therefore differ from M9 in the limbs unless you approve a skeleton revision.

## Photo comparison (low confidence: image ratios only, not mm)

Measured from front-view silhouettes as fractions of figure height. The pack's own ratios are 1.67 front and 1.61 back.

| | Reference | W12c | ST_a | M9 |
|---|---|---|---|---|
| Outer shoulders ÷ bare waist | about 1.76 (pack: 1.67) | 2.02 | 2.02 | 1.99 |
| Width at 0.80 of height | 0.252 | 0.315 | 0.290 | 0.283 |
| Lower thigh, per leg | 0.080 | 0.082 | 0.091 | 0.079 |

## Assessment of M9 against the photographs

**Better than W12c / ST_a:**

- Shoulders are broad but sloping, with no "shoulder pad" top.
- The neck and trapezius are natural, and the head is a real head, not a mannequin.
- The arms hang naturally beside the thighs.
- Hips are slim and the pelvis-to-thigh line is natural.
- Knees, calves and ankles are believable.
- Its silhouette ratios are the closest of the three.

**Still short of the photographs:**

- **No surface definition.** There are no abdominal segments, serratus, pectoral or deltoid separation, or back relief. MakeHuman's targets shape volumes only. Definition needs sculpting, which belongs in the independent production mesh.
- **Less mass** in the arms, chest depth, deltoid caps and quadriceps.
- **Waist** is a little narrow for the shoulders (ratio 2.0 vs about 1.7–1.8).
- **Shoulder line** still starts slightly high.

**First-party note:** M9 is MakeHuman (CC0) geometry built with MPFB (GPL-3.0 code). It is a **benchmark only**. Per your rule, no MPFB mesh, topology, rig, weights or textures will go into the production model.

## Ledger

| State | Items |
|---|---|
| Done (evidence above) | Pack read; MPFB installed and verified; M1 to M9 built; worksheet measured; comparison renders; provenance |
| Awaiting the owner | **Visual approval of M9's shape** (or direction for M10); the stature choice (1856 / 1820 / 1750); whether limb lengths follow the canonical skeleton or a revision |
| Blocked | Laptop access (no Remote Control folder); `fit/proportions.py` not on this branch (no ANSUR run); `makehumancommunity.org` downloads blocked (not needed) |
| Not started, by instruction | Independent production mesh, rigging, exercises, shoulder press, female model |

## Update: M10, more muscle mass and definition (owner request, 3 Nov)

- **Mass:** MPFB muscle targets were pushed past MakeHuman's 1.0 maximum, to 1.4–1.6 on the pecs, lats, deltoids, arms, quads and calves (settings in `mpfb_M10_params.json`). Chest depth, upper arm, thigh and neck are also fuller.
- **Definition:** `scripts/mpfb_experimental/define_mpfb_candidate.py` (rendered at strength 1.4×). It is a procedural relief of up to about 6.5 mm on the posed, subdivided copy, displaced along the surface normals and placed from the rig's bones:
  - linea alba, three abdominal intersections and the outer ab borders;
  - inguinal lines;
  - sternal groove, lower pec border and pec mass;
  - pec–deltoid groove and deltoid insertion;
  - biceps–triceps grooves;
  - quad separations and the inner-knee teardrop;
  - calf heads and the soleus line;
  - spinal groove with the erector columns, lat and lower-trapezius borders.
- **Renders:** `renders_M10_defined/` (including `upper_closeups.jpg`) and `comparison_W12c_STa_M10_no_photos.jpg`.
- **Status:** it remains an MPFB benchmark, **not approved** and not production.

## Update: M11, wider and more defined (owner, 3 Nov: "better but still needs better definition; the reference is also wider")

- **Wider:**
  - original shoulder breadth restored (+0.1);
  - wider ribcage (`torso-scale-horiz` 0.25), lats 1.8, V-taper 0.4;
  - upper arm and deltoid fuller;
  - thighs fuller;
  - arms hanging 12° out.
- **Definition:** strength 2× (up to about 9 mm in), with serratus digitations, the external oblique border, grooves between the three deltoid heads and the infraspinatus/teres border added.
- **Renders:** `renders_M11_defined/` and `comparison_W12c_STa_M11_no_photos.jpg`. **Not approved.**

## Update: M13 (owner, 3 Nov: waist, legs, torso and pecs, definition, biceps-to-forearm, thigh gap)

- **Waist:** smaller V-taper (0.2) and wider waist (1.5).
- **Torso and pecs:** pecs 2.0; chest depth 0.6; bust 0.4; the lower pec border flatter and squarer, with more pec mass.
- **Arms:** forearm muscle 2.0 and wider/deeper. The relief adds brachioradialis/extensor mass and tapers the biceps into the elbow crease.
- **Legs:**
  - quads 2.0 and fuller thighs, without the upper-thigh flare M12 had;
  - narrower hips, less buttock volume;
  - ankles 0.15 m apart, which closes the gap between the thighs;
  - vastus lateralis mass and a patella outline added.
- **Definition:** strength 2.3×. Committed views are in `renders_M13_defined/` and `comparison_W12c_STa_M13_no_photos.jpg`; M12 was not committed. **Not approved.**
