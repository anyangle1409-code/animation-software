# ORIGINAL_v1 review candidate R8: shoulder-cap helper joint (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

**Owner, on R7:** "From the photos it doesn't look fixed". Then: "Yes, build R8 with the helper joint".

R7's top-of-shoulder crease was unchanged at 140–160°. The skin above the shoulder pivot is weighted to the upper arm, so it
swings the full arm-vs-scapula rotation (about 119°) and folds 6–20 mm onto itself. Shape keys cannot unfold skin that deep.
R8 adds a joint.

## What R8 is

**Parent:** R5. R6's stretch keys and R7's fold keys were solved for skin without a helper, and on the helper base they
interfered (measured: 140° pairs 98 → 132–198).

1. **Helper joint `shoulder_cap_<s>`** (`scripts/original_v1_shoulder_cap_helper.py`):
   - its head is at the upper-arm pivot, in the upper arm's rest frame, parented like the upper arm;
   - it is driven statelessly to 45 % of the upper arm's rotation relative to the scapula.
2. **Chain weights** (`assign_weights_axial`):
   - **What is redistributed:** around the pivot, each vertex's girdle + upper-arm share.
   - **How:** by its position along the arm axis, from 14 cm above the pivot to 20 cm below it, giving girdle → helper → arm.
     Neighbouring influences are therefore never more than 55 % of the rotation apart, so there is no candy-wrapper collapse.
   - **Never more arm weight:** a vertex never gets more upper-arm weight than it had, which keeps the armpit and chest on the trunk.
   - **Fade-out:** the change fades back to R5's weights between 12 and 18 cm from the pivot.
   - **Scope:** 650 vertices per side, at most 4 influences, and the weights are mirror-symmetric.
3. **Stretch relax keys** `HGPT_S1_SHOULDER_<s>_{105,120,145,160}`: re-solved on the helper base with R6's method and parameters.

**The file is still a 67-bone rig.** It stores the helper's vertex groups and its parameters (`hgpt_cap_fraction`,
`hgpt_cap_params`), but not the bones. `drives.setup()` recreates the two bones in memory (69 joints while posing), and
`drives.drive()` turns them. Builder: `scripts/build_original_review_candidate_r8_blender.py` → `r8_build.json`.

**Variants measured** (on R5, with the pairs / stretch / crushed counts at 160°):

| Variant | Result | Verdict |
|---|---|---|
| Spherical cap weights (amount 0.6–0.9, radius 10–22 cm) | pairs 118–222; a new hard line across the arm at the cap edge | rejected |
| Axial chain, free arm weight | stretch 168–238 (armpit given to the arm) | rejected |
| Axial chain, arm weight only reduced, −0.12/+0.16, fraction 0.5 | pairs 20, stretch 156 | runner-up |
| Same, fraction 0.55–0.6 | pairs 76–82 return | rejected |
| **Axial chain, reduce-only, −0.14/+0.20 m, fraction 0.45** | **pairs 0, stretch 174 → 124 after relax keys** | **selected** |

## Results

**Coupled 0–160° sweep, R5 → R8** (collapse / stretch > 2× / pairs / volume %):

| HT | R5 | R8 |
|---|---|---|
| 60 | 0 / 14 / 0 / +0.69 | 0 / 18 / 0 / +1.34 |
| 90 | 2 / 48 / 0 / +0.18 | 0 / 48 / 0 / +1.38 |
| 120 | 10 / 72 / 10 / −0.99 | **0** / 80 / **0** / +0.64 |
| 130 | 26 / 80 / 84 / −1.45 | **0** / 88 / **0** / +0.27 |
| 140 | 14 / 88 / 98 / −1.91 | **0** / 98 / **0** / −0.15 |
| 150 | 14 / 92 / 156 / −2.34 | **0** / 112 / **0** / −0.59 |
| 160 | 26 / 100 / 216 / −2.73 | **4** / 124 / **0** / −1.03 |

R7, for comparison, at 160°: 26 / 60 / 216.

**All 13 benchmarks** (`r8_validation.json`), worst frame collapse / stretch / pairs, R5 → R8:

| Benchmark | R5 | R8 |
|---|---|---|
| Shoulder press | 28 / 100 / 216 | **4 / 124 / 0** |
| Push-up | 1 / 61 / 52 | 3 / 63 / 42 |
| Bent-over row | 2 / 4 / 32 | 2 / 5 / 26 |
| Grip | 0 / 6 / 26 | 0 / 6 / 18 |
| Deadlift | 38 / 22 / 319 | 38 / 22 / 311 |
| Others | — | identical, or within 1 |

**Visually** (`shoulder/shoulder_r7_r8_{60,90,130,145,160}.jpg`, front / back / side; red marks overlap, blue crushed, yellow stretch > 2×):
- **Fixed:** the hard crease on top of the shoulder. From behind, the arm now grows out of the shoulder in one curve at 130–160°.
- **At 60°:** the deltoid is rounder than R5's (no pinch).

**Costs and remaining issues, retained:**
1. **Front of the armpit:** stretched at 130–160° (the yellow band; 124 faces > 2× at 160° against R7's 60). R6/R7's extra stretch
   work is not in R8.
2. **Back of the armpit:** a lump forms there in the side view at 130–160°.
3. **Squarer shoulder at 90°:** the top of the shoulder is slightly squarer and higher. Body volume is +1.3–1.4 % at 60–90°,
   because the cap no longer collapses.
4. **Push-up:** crushed faces 1 → 3.

## Tests

`scripts/blender_tests/test_original_review_candidate_r8.py`, 6 native tests (CI: `original-review-candidate-r1.yml`):
- **Identity and flags.**
- **File contents:** still a 67-bone file; only the cap groups and the S1 keys are added; bones and basis are unchanged.
- **Weights:** they change only within 18 cm of a pivot, stay normalised with at most 4 influences, and mirror.
- **Live drive:** 69 joints in memory; the cap turns 45 % of the arm; the 160° row reproduces exactly.
- **Sweep:** 0 pairs at 120–160°, collapse ≤ 4, less volume loss; the stretch cost is asserted.
- **Benchmarks vs R5:** no benchmark gains pairs; the press reaches 0 pairs.

R1–R7 tests still pass.

## Next

1. **Armpit:** fix the front-armpit stretch and the rear-armpit lump. Options: an axillary weight rework, or a second, lower helper.
2. **Upstream:** shipping R8 needs a 69-joint runtime (two shoulder-cap joints driven from the upper arm). That is a
   runtime-contract change for the owner and Lane G (PR #26).
