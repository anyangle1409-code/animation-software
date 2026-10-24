# R121 surface candidate: finishing the R120 clean rebuild

Branch: `claude/r120-surface-candidate-20261023`. Candidate only: nothing is merged or deployed. The W8, V14 and R120
originals and the production skeleton are untouched. Model-only review images are in git; reference photos and .blend
files are not.

## Why

The owner judged the standing body "terrible" and chose "Rebuild clean". R120 (`scripts/body_v2/rebuild_v2_blender.py`,
SDF + marching cubes + stitch + inverse LBS) gave the torso, arms, shoulders and hips an even surface. However:

- its stitch left open edges and folded triangles (thigh seams, neck);
- the seams between the rebuilt and kept skin read as thin lines;
- the 6 mm blur that removed the old lumps also removed the muscle definition.

R121 (`scripts/body_v2/r120_finish_blender.py`) is a post-step on the R120 blend that addresses all three.

## Build

```
# R120 input: $S/RB2/body_v2_rebuilt.blend  (rebuild_v2_blender.py at d5141ad3, 3-axis parity)
V2_R121_FINAL_UNFOLD=6 V2_R121_SPINE_SOFT=1 V2_R121_AX_SOFT=0.006 V2_R121_ARM_HC=30 V2_R121_SLIM_SMOOTH=10 \
  python3.13 scripts/body_v2/r120_finish_blender.py -- body_v2_rebuilt.blend <out>
python3.13 scripts/body_v2/render_v2_blender.py -- <out>/body_v2_r121.blend <r57src> <out>
```

Every stage moves the basis and all shape keys together. Each new behaviour is behind an env flag and is off by default,
so earlier candidates (R121b–d) rebuild unchanged.

## Stages

| Stage | What it does | Flag(s) |
|---|---|---|
| 0 repair | Fills R120's open thigh-seam edges (9 faces), deletes wire edges, then unfolds folded triangle pairs (normals > 120 deg apart) by local averaging. Folded vertices per round: 2400 → 86 → 46 → 19 → 3. | `V2_R121_UNFOLD_ROUNDS` |
| 1 seams | HC-Laplacian (shrink-free) over 14 rings either side of every rebuilt/kept boundary, fading with ring distance; never into the hands. | `V2_R121_SEAM_RINGS`, `V2_R121_SEAM_STEPS` |
| 2 torso relief | The reference-measured `torso_front` / `torso_back` of `legs_v2_blender.py`, unchanged, along smoothed normals, rebuilt skin only. | `V2_R121_TORSO` |
| 2a soft spine | Replaces the spine groove (−6 mm, σ ≈ 8 mm) with −4 mm, σ ≈ 16 mm. | `V2_R121_SPINE_SOFT=1` |
| 2b soft midline | Uses √(x² + 6 mm²) for \|x\|. | `V2_R121_AX_SOFT=0.006` |
| 3 arms | Slims the arms towards their bone axes (15 % upper arm, 12 % forearm, faded at the shoulder and wrist), HC-smooths the slimmed arm, then adds the R115 bone-local muscles at 0.6. | `V2_R121_SLIM_UPPER`, `V2_R121_SLIM_FORE`, `V2_R121_ARM_HC`, `V2_R121_ARM_AMP` |
| 4 final unfold | Runs the stage-0 unfold again on the finished shape. Folded vertices per round: 195 → 70 → 17 → 7 → 11 → 7 → 6. | `V2_R121_FINAL_UNFOLD=6` |

## Defects found and fixed in this round (measured)

- **Rings round the forearm (R121d).**
  - Cause: `forearm_*` ends mid-forearm, because twist bones carry the lower half (146 mm of a 293 mm forearm). The
    bone-local relief and slimming therefore stopped half-way and drew rings.
  - Fix: the forearm frame now runs elbow → wrist (`hand_*` head), as the builder's R77 `bone()` does.
  - Note: the builder's own R115 block uses the short bone too. That is unchanged here and is worth checking
    separately.
- **Ladder down the spine.**
  - Cause: on the midline the geometry is smooth (high-pass profile 0.2–0.3 mm). The ladder was facet shading: the
    relief groove bent the skin about 16 deg per 3 mm edge. Mean adjacent-face angle in the spine band (|x| < 10 mm,
    0.55–0.80 H):

    | Mesh | Mean angle |
    |---|---|
    | RB2 | 1.1 deg |
    | R121 as before | 4.4 deg |
    | + more normal smoothing (30 or 100 steps) | 5.0 deg (no help) |
    | + soft \|x\| | 4.2 deg |
    | + soft spine groove | 2.6 deg |

  - Fix: the soft spine groove and soft midline flags above.
- **Pleats in the rear armpit crease.**

  | Mesh | Edges > 35 deg | Edges > 90 deg | Edges > 120 deg |
  |---|---|---|---|
  | RB2 | 683 | 58 | 28 |
  | Stage 0 only | 667 | 20 | 0 |
  | + seams | 667 | 20 | 0 |
  | + torso relief | 962 | 160 | 85 |
  | R121k (all stages) | 510 | 155 | 84 |
  | R121p (+ final unfold) | 327 | 41 | 2 |

  - Cause: the relief along the normals folds the narrow crease.
  - Tried and rejected:
    - fading the relief smoothly towards the arm (`V2_R121_ARMFADE=1`): 85 → 57 only;
    - HC or plain Laplacian smoothing of the crinkle: the inverted patch does not untangle (10 rings × 150 steps
      still left 73 sharp edges);
    - local delete-and-refill: left holes (117 boundary edges) and the fills folded again. Not committed.
  - Fix: the final unfold.

## Motion check (R121p vs its R120 input)

The check uses `scripts/body_v2/r121_motion_check_blender.py`, which is read-only and saves nothing. It poses the rig
with the correctives driven (the r57 drives), then counts edges whose faces differ by more than 90 / 120 deg on the
deformed mesh. Hands and feet are excluded. "Band" means the arm root: 0.70–0.82 H, \|x\| > 0.12 m.

| Pose | RB2 >90 / >120 (band) | R121p >90 / >120 (band) |
|---|---|---|
| rest | 2583 / 1147 (58 / 28) | 43 / 2 (41 / 2) |
| arm abduction 90 | 2998 / 1256 (527 / 253) | 584 / 281 (528 / 268) |
| arm abduction 150 | 6365 / 3080 (3532 / 1746) | 4005 / 2001 (3261 / 1624) |
| elbow 120 | 2709 / 1218 (13 / 5) | 142 / 89 (4 / 3) |
| squat (benchmark t = 1) | 2534 / 1174 (51 / 25) | 736 / 342 (13 / 5) |

For comparison, V14 (the pre-rebuild mesh, 238k vertices against R120's 347k, so raw counts are not directly
comparable) gives:

| Pose | V14 >90 / >120 (band) |
|---|---|
| rest | 259 / 146 (217 / 122) |
| arm abduction 90 | 583 / 242 (364 / 180) |
| arm abduction 150 | 2471 / 1422 (1368 / 730) |
| elbow 120 | 296 / 178 (184 / 101) |
| squat | 937 / 515 (210 / 122) |

R121 removes most folds in every pose. Raising the arm is still bad at the arm root, about equally in RB2 and R121p.
That comes from the R120 rebuild: its shoulder correctives were authored on the old surface and carried across by
transfer. At 150 deg the arm-root band has about 2.4 times V14's folds.

This is the largest open problem for movement. The fix is new abduction correctives authored on the rebuilt surface
(the R30 recipe: relax the posed arm root, invert through LBS, store as keys). That changes the r57 corrective drives
(`original_v1_review_candidate_drives.py`), so it is left for the owner to approve rather than done here. JSON: `review-assets/body_v2/draft_r121p_candidate/motion_check_*.json`.

## Tried, not adopted

- **Back gain** (`V2_R121_BACK_GAIN`, back relief above 0.60 H only).
  - At 1.4 (R121r) the scapula region reads a little more, but it adds a lump at mid-back and brings armpit folds back:
    the final unfold leaves 50 folded vertices instead of 6.
  - At 1.7 on the whole back (R121q) the glutes grew a shelf at the hips.
  - Default stays 1.0.

## Remaining (honest)

- **Back:** reads flatter than the reference. The scapula/infraspinatus/teres relief is faint, and there is a
  horizontal shadow under the lats (the lat lower edge).
- **Rear upper arm:** still lumpier than the reference.
- **Thigh seam:** faint traces in the back view.
- **Head:** still the hood.
- **Movement:** see the motion check above. Arm raising folds the arm root (inherited from R120).
- **Determinism:** R121 itself is deterministic numpy on a fixed input. Its input (RB2) is the local R120 build, which
  matches the archive to within 1.14 mm on 5,210 / 347,917 vertices (see `docs/V14_RECOVERY_INVESTIGATION_20261023.md`).

Review images (model only): `review-assets/body_v2/draft_r121p_candidate/`.

## Arm-raise correctives (candidate, 24 Oct 2026)

These are candidate-only keys authored on the rebuilt surface. The r57 drives are not changed; the new keys are driven
by `scripts/body_v2/r121_drives.py`, called after the r57 `drives.drive`.

```
V2_R121_ARMKEY_CRUMPLE=6 V2_R121_ARMKEY_CRUMPLE_DEG=21 \
  python3.13 scripts/body_v2/r121_arm_correctives_blender.py -- body_v2_r121.blend <r57src> <A>
V2_R121_ARMKEY_CRUMPLE=6 V2_R121_ARMKEY_CRUMPLE_DEG=21 V2_R121_ARMKEY_MODE=flex \
  python3.13 scripts/body_v2/r121_arm_correctives_blender.py -- <A>/body_v2_r121_arms.blend <r57src> <B>
```

**Recipe.** For each key angle (60 / 90 / 120 / 150 deg):

1. Pose both arms with every existing drive active.
2. Relax the posed upper body (above 0.62 H; hands and feet held):
   - unfold rounds (local averaging over folded triangle pairs and 4 rings);
   - de-crumple rounds (shrink-free HC over edges past 21 deg, dilated).
3. Take the correction back to rest space through each vertex's measured deformation matrix. The matrix comes from
   three 1 mm unit test keys, which is exact for LBS plus additive keys. Two fixed-point passes follow; the fit residual
   is 0.000 mm.

**Keys.**

- `R121_ARM_<s>_<deg>`: authored in a sideways raise (abduction). Hats on the humerothoracic elevation, the measure
  `drive_s1` uses, from 25 deg.
- `R121_FLEX_<s>_<deg>`: authored in a forward raise as the residual on top of `R121_ARM_*`. It is weighted by
  `plane_factor`, the sin² of the plane of elevation measured from the arm's displacement off its rest direction. The
  factor is 0.000 for sideways raises and 0.97–1.0 for forward ones, so the sideways results are unaffected.

**Motion check** (`r121_motion_check_blender.py`, band = arm root). Mean edge angle in the band: 2.83 deg at rest.

| Pose | R121p band >35 / >90 / mean angle | + arm keys band >35 / >90 / mean angle |
|---|---|---|
| abduction 90 | 3718 / 528 / 7.31 | 34 / 0 / 3.49 |
| abduction 120 | 12890 / 2691 / 13.65 | 92 / 0 / 3.25 |
| abduction 135 (between keys) | 14792 / 3271 / 14.74 | 433 / 32 / 4.40 |
| abduction 150 | 14819 / 3261 / 14.79 | 138 / 0 / 3.44 |
| forward 90 | 3738 / 459 / 7.89 | 227 / 5 / 3.98 |
| forward 150 | 13673 / 2664 / 14.34 | 467 / 34 / 4.27 |
| rest, elbow 120, squat | unchanged | unchanged (keys at 0) |

Images: `review-assets/body_v2/draft_r121_armkeys_candidate/sheet_*.jpg`, workbench with cavity, upper body, front /
back / side / back-3/4. Top row is R121p; bottom row adds the keys.

**What is clean and what is not.**

- The tangled armpit and the rear-shoulder crumple are gone in the side, back and back-3/4 views.
- The front of the raised upper arm still shows fine wrinkle texture. That comes from the skinning itself (LBS on the
  rebuilt arm), which keys can only mask.
- Keys move vertices by up to 37 mm (150 deg, forward).

**Not tested:**

- Combined raise + elbow bend.
- Raises with axial rotation.
- The movement benchmarks (press, row, pull-up).

Adopting these keys is a runtime-contract change: new keys plus a drive call. That is the owner's decision.
