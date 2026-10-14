# ORIGINAL_v1 review candidate R5 = R4 + corrected blade tilt + arm/chest contact (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production.**
- **Owner instruction:** "yes, fix the blade tilt and row contact".
- **Lineage:** R5 replaces R4 as the single review candidate; R4 stays unchanged and replays exactly. Built from C5 by `scripts/build_original_review_candidate_r4_blender.py --name R5 --c1` (report `r5_build.json`).

## 1. Blade tilt

**Measured on R4** (realised ISB angles at 160° vs the profile's 42° upward rotation / 17° posterior tilt / 8° internal rotation):
- upward rotation 36°;
- posterior tilt 28°;
- about 9.5° *external* rotation.

R4's contact solver had a free extra rotation that bought rib contact by turning the blade the wrong way about its vertical axis. That is the "hanging" blade in the x-ray.

**Fix** (`scripts/original_v1_shoulder_r4.py`, mode `isb`; R4 keeps mode `wrap`):
- the solver's variables are now the blade's three ISB angles themselves, plus small clavicle motion;
- upward rotation and tilt are held to the profile (penalty 1.0);
- internal rotation is free (0.01) to keep thorax contact;
- the clavicle is penalised (0.25, so no shrug).
- `original_v1_scapula_isb_drive._signed` now probes each axis's sign once, so negative angles work.

**Result** (realised at 160°):
- upward rotation 41.5° and tilt 17.1°, matching the profile;
- internal rotation about −9° (external), where the profile asks for +8°.

**Finding:** with this model's blade and thorax shapes, the profile's three angles cannot all hold with the blade on the ribs:

| Configuration | Inferior-angle lift-off at 160° |
|---|---|
| exact profile angles | 49 mm |
| selected setting | 47 mm |
| freer clavicle | 35 mm, but shrugs |

Because the scapula's skin influence is tapered, the lift-off does not show in the skin. It is a skeleton-geometry question for review: blade shape, or thorax-guide size.

| Sweep vs today, 160° (collapse / stretch / pairs / volume) | Today | R4 | R5 |
|---|---|---|---|
| | 42 / 400 / 444 / −5.0 % | 36 / 78 / 216 / −3.2 % | 26 / 100 / 216 / −2.7 % |

## 2. Row arm/chest contact: C1 keys (`scripts/build_original_arm_trunk_contact_corrective_blender.py`)

**Method:**
- **Contact:** at the row's two contact frames (shoulder extension 25° and 38°), upper-arm skin within 4 cm of the trunk skin that is closer than 4 mm, or inside, is pushed out to 4 mm along the trunk normal.
- **Taper and mapping:** harmonic taper over 4 rings, LBS-inverse to rest, capped at 30 mm.
- **Guard:** count-based against new collapsed faces over the row's pull.
- **Driving:** the measured shoulder extension (`drives.drive_c1`), off below 18°, so the walk stride's ~15° arm swing never triggers it.

| Gap tested | Row worst pairs | Verdict |
|---|---|---|
| 2 mm | 47 | — |
| 4 mm | 32 | **selected** |
| 6–8 mm | 50–56 (arm skin folds) | rejected |

## Results on all 13 benchmarks (`r5_validation.json`)

| Benchmark | a003 | R4 | R5 |
|---|---|---|---|
| Bent-over row | 2 / 0 / 156 | 2 / 2 / 116 | 2 / 4 / **32** |
| Shoulder press | 48 / 438 / 462 | 36 / 78 / 218 | **28** / 100 / 216 (volume −3.2 → −2.7 %) |
| Other 11 | — | — | identical to R4 |

**Remaining:**
- row end-frame contacts: 7 arm/chest pairs per side and 9 upper-arm skin folds;
- press: the posterior-axillary curl;
- mid-range collapsed faces: 4–10 at 80–120°, against 0–2 today;
- the inferior-angle lift-off above.

## Evidence

- `sequences/shoulder_press*`, `sequences/bent_over_row*`: a003 vs R5.
- **Other benchmarks:** R4's sequences (identical numbers).
- **Skeleton x-ray:** `skeleton_xray/` (today vs R5).

## Tests

`scripts/blender_tests/test_original_review_candidate_r5.py`, 7 native tests:
- **Identity and drive:** identity; "R5" drive mode.
- **Bones:** only the pivots moved, onto the GH landmark.
- **Weights:** at most 4 influences.
- **Live drive:** upward rotation and tilt within 2° of the profile, contact within 50 mm, no shrug, mirrored.
- **Sweep:** vs today.
- **C1 keys:** on their own upper arm; key angles above the walk's arm swing.
- **Benchmarks:** row pairs below half of R4's; the other benchmarks identical to R4.

The R4 tests still pass, since R4 replays exactly.
