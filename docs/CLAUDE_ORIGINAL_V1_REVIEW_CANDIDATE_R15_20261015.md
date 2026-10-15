# ORIGINAL_v1 review candidate R15: the skeleton fixed for the press lockout (Claude, 15 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

## Why

Owner, on R14's lockout:
- "The shoulder should move with the arm. If you show me the skeleton in this pose I want to work out what is causing this. I think maybe the shoulder is coming over too far."
- "In this pose it should basically end up like a Y shape."
- "I want to [fix] the skeleton first."

The full skeleton diagnosis is in `docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R14_20261015.md` (two sections at the end), with the renders in `.../claude_review_r14_20261015/diagnosis/`. That folder also holds the skeleton-only press video `skeleton_press_v4.mp4`.

## What R15 is

R15 is R14's recipe (`build_original_review_candidate_r14_blender.py`: base from R13, S4 ×5 target, delta mush, S5 bake with the benchmark-path guard) re-run on **press path v4** (`build_original_review_candidate_r15_blender.py`).

**1. Clavicle axial turn applied first** (v3). `coupled.clavicle_basis` (Work's module) applied the axial turn after the elevation. That swung the raised clavicle around a cone, about 15° forward at lockout.

| At lockout | Before (v2) | v3 / v4 |
|---|---|---|
| Clavicle retraction | 7° | 22° |
| Glenohumeral joint vs rest | 5 cm forward | under 1 cm |

**2. Scapula aligned with the arm at lockout** (v4). This is Saha's zero position, the Y from behind.
- Added: +15° of scapular upward rotation over 120 → 172°.
- Result: the humerus is within 8° of the scapular spine; it was 20°.

## Results

**Press path v4** (`r15_build.json`), at lockout: 4 collapsed faces, stretch 981 → 300 with S5, 0 self-intersecting pairs.

**Benchmarks** (`r15_validation.json`, worst frame; self-intersecting pairs / collapse):

| Benchmark | R13 | R14 | R15 |
|---|---|---|---|
| shoulder_press | 0 / 4 | 0 / 18 | 0 / 16 |
| bent_over_row | 4 / 2 | 0 / 0 | 0 / 0 |
| push_up | 2 / 3 | 0 / 3 | 0 / 3 |
| grip | 20 / 0 | 18 / 0 | 18 / 0 |
| deadlift | 293 / 4 | 293 / 4 | 293 / 4 |
| all others | equal | equal | equal |

- The deadlift is unchanged; it waits on the DL1 owner decision.

**Tests:** `test_original_review_candidate_r15.py` 5/5. This includes the lockout skeleton check: arm vs scapular spine < 10°, and the clavicle retracting by more than 5°.

**Video:** the R15 mesh press video `mesh_press_r15.mp4`. It was rendered in the session but is not committed with this candidate.

## Still wrong: the lump behind the shoulder at lockout

Owner: "I'm not sure the deforming is in the right place here".

**Cause.** The deformation is not in the right place.
- About two-thirds of the deltoid skin is moved by the `shoulder_cap` helper.
- That helper follows half of the arm-vs-scapula rotation, so the deltoid skin is left at about arm-out-sideways.
- At lockout it bunches behind and below the joint.

**R16 (rejected): a cap fraction that rises with elevation** (`original_v1_shoulder_cap_helper.fraction_at`, opt-in rig prop `hgpt_cap_fraction_ramp`, kept for the record). Every end fraction above 0.5 adds collapsed and crossing skin at the inner top of the shoulder. Measured on R15 at lockout, S5 off:

| End fraction | 0.5 | 0.6 | 0.65 | 0.7 | 0.75 | 0.8 |
|---|---|---|---|---|---|---|
| Collapse | 8 | 68 | 94 | 108 | 103 | 99 |
| Pairs | 0 | 2 | 60 | 130 | 164 | 206 |

- The full R16 bake (ramp to 0.8) ended at 88 collapse / 199 pairs.
- Handing the inner cap weight back to the clavicle and scapula did not help: 26–99 collapse, 4–262 pairs.
- At 0.8 the skin would have to hinge about 88° within a few centimetres around the cap's edge.

**Next: R17**, a lockout deltoid corrective (option 1, approved by the owner). `build_original_review_candidate_r17_blender.py`
