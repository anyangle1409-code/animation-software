# ORIGINAL_v1 review candidate R9: R8 + mid-range shoulder shape keys (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

**Owner, on R8's remaining issues:** "Go ahead yes". The issues were:
- front-armpit stretch;
- a lump behind the armpit in the side view;
- a squarer "shoulder pad" at 90°.

**Outcome:**
- **Shoulder pad:** fixed.
- **Armpit:** four approaches were measured and rendered. None looked better than R8, so none is in R9 (details below).

## What R9 is

**Parent:** R8. R9 is R8 plus 8 shape keys, `HGPT_S3_SHAPE_<s>_{45,75,100,125}`. The 125 key is an empty closing key. Weights, bones,
the basis mesh and every R8 key are unchanged, and the file is still a 67-bone rig.

**Cause of the shoulder pad:** R8's helper keeps the skin above the shoulder pivot with the girdle and helper. At 45–100° that skin
therefore sits up to 45 mm proud of R5's surface: measured +45 mm at 90°, with body volume +1.4 % against R5's +0.2 %. R5 looked
right in that range; its fold only began above 120°.

**S3 shape-target keys** (`scripts/build_original_shape_target_corrective_blender.py`):
- **Target:** at 45°, 75° and 100°, each side's skin above the pivot (within 20 cm, from 3 cm below the pivot upward) is pulled to R5's posed surface.
- **Mapping:** the change is tapered over 4 rings, mapped to rest through the blended LBS matrices, and capped at 40 mm.
- **Drive:** the keys are driven on elevation from 20° (a new third, optional field per family in `drives.S1_FAMILIES`), and they are fully off from 125°.
- **Reference:** the R5 surfaces are dumped in a separate process (`--reference`), and their SHA is recorded in `r9_build.json`.

Builder: `scripts/build_original_review_candidate_r9_blender.py`.

## Results

**Coupled sweep, R8 → R9** (collapse / stretch > 2× / pairs / volume %):

| HT | R8 | R9 |
|---|---|---|
| 30 | 0 / 0 / 0 / +0.71 | 0 / 0 / 0 / +0.44 |
| 60 | 0 / 18 / 0 / +1.34 | 0 / 16 / 0 / **+0.54** |
| 80 | 0 / 30 / 0 / +1.46 | 2 / 32 / 0 / **+0.41** |
| 90 | 0 / 48 / 0 / +1.38 | 0 / 50 / 0 / **+0.19** |
| 100 | 0 / 60 / 0 / +1.19 | 0 / 58 / 0 / −0.08 |
| 120 | 0 / 80 / 0 / +0.64 | 0 / 80 / 0 / +0.37 |
| 125–160 | — | identical to R8 (160°: 4 / 124 / 0) |

- **Benchmarks** (`r9_validation.json`): every worst frame is identical to R8.
- **Volume:** the volume ranges return to R5's level. For example, press max +0.97 → +0.31 %. R8's apparent volume gain was the shoulder-pad inflation.
- **Visual** (`shoulder/shoulder_r5_r8_r9_{60,90,120,145,160}.jpg`, R5 / R8 / R9):
  - at 60–90° the shoulder has R5's shape again;
  - from 120° it is R8 (no top-of-shoulder fold).
- **Recorded cost:** 2 crushed faces at 80°.

## The armpit: measured, not fixed

| Attempt | Result | Verdict |
|---|---|---|
| Laplacian smoothing of the armpit weights | stretch at 160°: 124 → 160–236; pairs return | rejected (it blurred the cap chain) |
| Second helper joint `axilla_<s>` (trunk-parented, 15–45 % of arm-vs-thorax rotation, takes armpit trunk weight) | max face stretch 7.3× → 5.1–5.5×, but the count is unchanged, +26 faces at 90°, and a new notch on the side of the chest (`shoulder/rejected_armpit_helper_{145,160}.jpg`) | rejected |
| Keep the arm's underside on the arm in the cap weights | no visible change; +4 pairs at 160° | rejected |
| Taubin smoothing / pull-relax keys on the armpit (on the armpit-helper base) | stretch 126 → 110 at best; the shape barely changes | not worth it alone |

**Where the stretch is:** the skin is weighted 30–50 % to `spine_03`, which stays still, and the rest to the arm or cap.
- **Front fold** (pec): up to 7×.
- **Back fold** (lat): 3–5×.

**The side-view lump:** largely the posterior axillary fold (lat/teres), which does bulge in a real raised arm. R5 and R7 show it too.
The defect is the pinched crease above it.

**What would fix it:**
- authored corrective shapes for the armpit at 130/160° (sculpted targets: an artist task or an owner-supplied reference);
- denser armpit topology;
- or a physically based skin-sliding pass.

Each of these is a scope decision for the owner. The joint and weight tools in `scripts/original_v1_shoulder_cap_helper.py`
(`assign_axilla_weights`, `CAP_MEDIAL`) stay available, inactive in R9.

## Tests

`scripts/blender_tests/test_original_review_candidate_r9.py`, 6 native tests (CI: `original-review-candidate-r1.yml`):
- **Identity:** includes the R5 reference SHA.
- **Contents:** R9 = R8 + the 8 S3 keys only, and the closing keys are empty.
- **Deltas:** bounded at 40 mm, local to the shoulder, and mirror-symmetric.
- **Sweep:** volume at 60–90° is below +0.6 %; 125–160° is exactly R8; the 80° cost is asserted.
- **Live drive:** the 75° key is on at 75°, and every S3 key is off at 160°.
- **Benchmarks vs R8:** no benchmark gains pairs.

R1–R8 tests still pass.
