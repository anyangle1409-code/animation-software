# ORIGINAL_v1 review candidate R13: hip-crease helper joint and baked hip delta mush (Claude, 15 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

**Owner:** "Yes. Continue" (fix the hip fold the same way as the shoulder).

**Starting point:** at peak pose in R12, the groin crease is the worst fold left on the body:
- squat: 227 self-intersecting pairs, 28 collapsed faces;
- deadlift: 313 pairs, 38 collapsed faces.

## What R13 is

R13 is R12 plus two changes, both following the shoulder recipe (R8 helper joint, R12 bake).

**1. Hip-crease helper joint, one per side** (`scripts/original_v1_hip_crease_helper.py`), as for the shoulder cap:
- `hip_crease_<s>` sits at the hip-joint centre, in the thigh's rest frame, parented to the pelvis.
- It is driven to 0.45 of the thigh's rotation relative to the pelvis.
- **Chain weights:** around the joint, each vertex's trunk + thigh share (trunk = pelvis + spine_01) is redistributed by position along the rest thigh axis, from 14 cm above to 20 cm below the joint:
  - the trunk share moves first to the helper, then to the thigh;
  - thigh weight is only ever reduced;
  - the change fades back to the original weights between 14 and 20 cm from the joint;
  - a 4-influence limit is applied over deform groups only, and only on vertices that carry a hip-helper weight.
- The saved blend keeps the vertex groups and the `hgpt_hip_*` rig properties. `drives.setup` recreates the bones in memory, so the file stays at 67 bones.

**2. H1 baked delta-mush keys** (`scripts/build_original_hip_bake_corrective_blender.py`):
- **Keys:** `HGPT_H1_BAKE_<s>_{45,70,90,110,135}`, 10 in total.
- **Drive:** sagittal hip flexion (`hip_flexion_deg`: the thigh's direction in the pelvis frame), piecewise linear from 20°.
- **Target:** the candidate plus a Corrective Smooth (delta mush) modifier: 60 iterations, factor 1.0, full within 14 cm of each hip joint, fading out by 22 cm.
- **Key poses:** the squat path up to 110°; the deadlift path at 135°.
- **Bake:** each vertex's posed offset is mapped to rest through the blended LBS matrices (damped, capped at 50 mm). Midline vertices (|x| < 0.1 mm) take half the offset in each side's key.
- **Guard:** the S5 smooth guard, mirror-symmetric, run over squat, deadlift, lunge, single-leg stance, walk and bent-over row (17 frames each). It needed one frame cut back on its first pass, and none on the second.
- **No new deformer at runtime.**

**Builder:** `scripts/build_original_review_candidate_r13_blender.py` runs four steps (`--weights`, `--make-target`, `--dump`, `--bake`), each in its own process.

## Variants measured

"Pairs" means self-intersecting pairs.

| Variant | Squat (pairs / collapsed / stretched) | Deadlift | Lunge, single-leg |
|---|---|---|---|
| R12 | 227 / 28 / 12 | 313 / 38 / 26 | 0 pairs |
| Helper alone, axial band −0.10…0.16 m (×0.45) | 251 / 22 / 284 | 503 / 74 / 376 | 6 pairs |
| Helper alone, −0.14…0.20 m (×0.45, **selected weights**) | 120 / 4 / 178 | 411 / 74 / 274 | 0 pairs, stretch ×2 |
| Helper alone, other bands and fractions (0.35–0.5) | 140–208 | 323–473 | 0–72 pairs |
| Delta mush live on R12, 30 iterations | 140 | 265 / 12 | 5 pairs |
| Selected helper + delta mush live, 60 iterations | 124 / 2 / 12 | 283 / 2 / 26 | 16 / 9 pairs; and it is a runtime deformer |
| **Selected helper + H1 bake (R13)** | **120 / 2 / 12** | **295 / 4 / 38** | **0 pairs** |

**Why the helper alone fails on the deadlift:** at 135° the helper band folds onto itself.

**A bug found and fixed on the way:** the shoulder helper's influence limit counts every vertex group, mask groups included. For the hip, that rewrote about 1,900 vertices body-wide. The hip helper therefore has its own limit, restricted to deform groups and helper vertices. R8–R12, which were built with the shoulder helper's limit, are unchanged.

## Results (`r13_validation.json`, all 13 benchmarks)

| Benchmark | R12 | R13 |
|---|---|---|
| Squat | 227 pairs / 28 collapsed / 12 stretched | **120 / 2 / 12** |
| Deadlift | 313 / 38 / 26 | **295 / 4 / 38** |
| Lunge | 0 / 0 / 37 | 0 / 0 / 34 |
| The other 10 | — | identical to R12 (the shoulder press included) |

**Recorded costs:**
- the deadlift has 12 more faces stretched beyond 2×;
- peak body volume rises from +0.2 % to +0.4–0.5 % in the squat and deadlift.

**What remains:** the deadlift's 295 pairs are the abdomen (spine_01) against the thigh. At 135° hip flexion with a 47° trunk lean, these two layers are in genuine contact, and fixing that needs a contact solve rather than skinning. In the squat, the remaining pairs sit at the pubic midline.

**Renders:**
- `hip/hip_crease_r12_vs_r13.jpg`: close-ups, overlapping faces in red;
- `sequences/`: filmstrips and GIFs of the six hip benchmarks.

In the squat, the sharp seam where thigh skin passed through the abdomen becomes a soft groin fold. The deadlift fold is softer, but a short overlap remains inside it.

## Tests

`scripts/blender_tests/test_original_review_candidate_r13.py`: 6 native tests, run in CI.
- **Identity.**
- **R12 + hip weights + 10 keys:** no new modifier, same basis, R12 keys unchanged, 67 bones.
- **Weights:** they change only within 20 cm of the hips; thigh weight never increases; at most 4 influences, summing to 1.
- **Deltas:** at most 50 mm, on the correct side, and mirror-symmetric within 1 mm.
- **Live drive:** at the squat peak, hip flexion reads 110° and the 110° key is fully on; a hip in extension during the walk gets no key.
- **Benchmarks vs R12:** squat and deadlift have fewer pairs and fewer collapsed faces; no other benchmark has more of either.

R8 and R12 tests still pass with the shared drives change (`hip.drive_h1` does nothing without H1 keys).

## Runtime contract (owner and Lane G, PR #26)

R13 adds two more in-memory joints (`hip_crease_l/r`) and 10 more pose-space keys driven by hip flexion. Like the shoulder helpers, these are contract items, not production.

## Push-up thumb: a fault in the exercise pose, not in the body (15 Oct, after R13)

**Owner:** "Yes" (do the push-up next).

**Where the overlaps were:** after R13 the push-up was the next worst benchmark, at 44 self-intersecting pairs. Every pair was in the **thumb web**: the thumb metacarpal against the index metacarpal, on every frame from the top to the bottom of the push-up. The elbow, chest and wrist had none.

**Cause:** the benchmark pose. To keep the thumb from hanging below the flat palm, the pose extends the thumb's base joint (CMC) by 40°, and that pressed the thumb metacarpal into the index.

**Fix, in the benchmark** (`build_original_movement_benchmarks_blender.PUSHUP["thumb_axial"]`):
- the thumb metacarpal also turns 10° about its own axis (+ on `_r`, − on `_l`, measured);
- this turns the thumb's bending plane about 6° away from the index (away from opposition), so the thumb lies flat beside the index;
- 10° is the smallest value tested (10–30°) that clears the overlap over the whole path on both hands;
- the thumb stays 0.4 mm above the floor.

**No body asset changed:** R13 is unchanged.

**Re-measured** (`r13_validation_pushup_thumb_20261015.json`; only the push-up differs):

| Push-up, worst frame (pairs / collapsed / stretched) | Old pose | Corrected pose |
|---|---|---|
| a003 | 196 / 12 / 64 | 170 / 12 / 68 |
| R13 | 44 / 3 / 71 | **2 / 3 / 75** |

**What remains in R13's push-up:**
- the 2 pairs are single faces on the shoulder cap;
- the stretched faces (about 35 per side) are in the thumb web (the thumb pulled back), the palm side of the wrist (67–98° extension) and the shoulder cap — places where skin genuinely stretches in this pose.

**Close-up:** `pushup/pushup_thumb_r13_old_vs_new_pose.jpg`.

**Test:** `test_original_movement_benchmarks.py` gains `test_push_up_thumb_lies_beside_the_index_without_web_intersection` (live on a003; 14/14 pass).

**Branch note:** the benchmark change is on the review branch only. The movement branch (PR #113) still has the old pose.

## Squat and deadlift: hands in the thighs, also a fault in the pose (15 Oct, after R13)

**Owner:** "Continue".

**What the per-frame view showed:**
- **Squat:** all 120 of R13's remaining pairs were **hand against thigh** (t = 0.125–0.5). The squat never posed the arms, so as the hips flexed, the rising thighs met the hanging thumbs. The groin crease itself is at 0 pairs on every frame.
- **Deadlift:** the frames at t = 0–0.625 had 44–116 thumb/thigh pairs. The arms are solved to hang vertically for the bar, which put the hands on the thighs.

**Fix** (`build_original_movement_benchmarks_blender._carry_arms`):
- each upper arm is abducted about the thorax's front-to-back axis through its shoulder, by the existing H1 natural arm carriage (`ARM_ABDUCTION_DEG`, 4°);
- **squat:** ramped in over the first quarter of the descent, so t = 0 is still the exact rest pose;
- **deadlift:** applied throughout, so the grip sits just outside the legs, as in a real deadlift;
- 4° is the smallest value tested (4–16°) that clears every frame on both a003 and R13.

**Test change, made openly:**
- `test_first_frame_is_rest_and_unapproved` now checks the deadlift's start the way it already checks the lunge, trunk rotation and single-leg stance: 0 pairs, volume change within ±0.5 % (it is 0.25 %);
- it no longer requires an exact rest volume for the deadlift;
- new: `test_squat_and_deadlift_hands_clear_of_thighs`.

**Tests:**
- movement benchmarks: 15/15 pass;
- knee contact (8) and shoulder-helper reference (4): pass;
- R13: 6/6 pass.

**Re-measured** (`r13_validation_corrected_poses_20261015.json`, which supersedes the push-up-only file; no body asset changed):

| Worst frame, self-intersecting pairs | a003 | R13 |
|---|---|---|
| Squat | 371 → 371 (its groin crease) | **120 → 0** |
| Deadlift | 455 → 449 | 295 → 293 (the bottom position only) |
| Push-up | 196 → 170 | 44 → 2 |

**What is left in the deadlift:** only its bottom position (t = 0.875–1), where the abdomen meets the thigh. Penetration depth at t = 1 is 4 mm median, 11 mm at the 90th percentile and 25 mm maximum.
