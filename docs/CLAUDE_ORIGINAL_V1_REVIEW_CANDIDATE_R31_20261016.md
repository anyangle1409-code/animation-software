# ORIGINAL_v1 review candidate R31: the upper arm follows the bone into the shoulder (Claude, 16 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

## Why

Owner, on R29/R30 press frames (t = 0.40 / 0.50 / 0.80): "These photos show that there looks like there is a join here but there isn't. The only joint will be the elbow. That bone should continue on into the shoulder not bend there." They chose option 1: re-bind the upper arm and rebuild the shoulder correctives on the new binding. Earlier requests carried into R31:
- "the back looks too bulky" (R30 recipe: lighter back fill);
- the crease at the arm root should fade in gradually (R30 recipe: S7 fades in from 95°, with an extra key at 120°);
- the press movement is fine (lockout stays at 166°).

## What was measured

On R29, rigid-humerus lag by fraction of the shoulder-to-elbow length (scratch tool, keys off): the skin of the upper half of the upper arm was weighted mostly to:
- the shoulder-cap helper;
- the upper spine (spine_02/03, 17 % over 25–55 % of the arm);
- the pec / lat muscle-line helpers (9 %).

It was not weighted to the humerus. Upper-arm weight was 0.23 / 0.39 / 0.59 / 0.79 over the 20–30 / 30–40 / 40–50 / 50–60 % bands. At every press elevation that skin lagged 8–10 cm behind the bone, so the arm bent where the weighting changed, a third of the way down the upper arm. That is the "join" the owner saw.

## What R31 is

Lineage: **R18 → R18Wg5 → B5 → R31.** The stage reports are in `stages/`. The R18Wg5 and B5 blends are not committed; their sha256 values are recorded and checked as a chain by the test.

**1. Upper-arm follow weights (R18Wg5), `scripts/build_original_upperarm_follow_weights_blender.py`.**
- **Donors:** shoulder_cap, clavicle and scapula. Their share of upper-arm skin is handed to `upperarm_<s>`.
- **Along the arm (`FOLLOW_T` 0, 0.08 m on the rest arm axis):** the hand-over starts at the shoulder pivot and is complete 8 cm down (smoothstep).
- **Round the arm (`FOLLOW_MEDIAL_RAMP` −0.3, 0.5):** none on the inner (armpit) face, full on the outer face.
- **Torso skin excluded:** skin medial of the axis whose normal faces outwards is left alone.
- **Limits:** radius 8.5 cm; total weight per vertex kept; 4 influences; positions, faces and shape keys untouched (checked).
- **Changed:** 750 vertices per side, mean moved weight 0.25.
- **Variants tried and rejected** (all keys-off benchmarks):
  - Full re-bind, including the inner arm: walk pairs 0 → 10, grip 18 → 126, push-up 0 → 172.
  - Cap only at full radius: also broke the benchmarks.
  - Outer only with a hard cut: push-up stretch 79 → 207.
  - **The gradual ramp (g5)** leaves the keys-off benchmarks unchanged apart from the press (stretch 531 → 593 with no correctives).

**2. S5 bake rebuilt on the new binding (B5).**
- The old S5 keys were removed (`stages/drop_s5_s7_keys.py.txt`).
- The rebuild uses `build_original_review_candidate_r15_blender.py` with the R15 recipe: `--make-target`, `--dump`, then `--bake` with S5_MASK_RINGS=0, S5_RESOLVE=0, S5_SMOOTH_GUARD=1, S5_POST_SMOOTH=0.
- Commands: `stages/b5_run.sh.txt`.

**3. S7 lockout corrective, R30 recipe (`r31_targets_recipe.json`, commands in `stages/r31_run.sh.txt`).**

Unchanged from R29:
- lockout 166°;
- the arm-column tube;
- the deltoid swell;
- the hook / front-fold rebuilds;
- the automatic clean-up.

Changed:
- **Lighter back fill:** `LAT_WEB` 0.35 (R29 0.6).
- **Gradual fade-in of the arm-root shaping:**
  - S7 fades in from 95° (`S7_START`, stored as `rig["hgpt_s7_angles_start"]`), not from 130°;
  - an extra key at 120° carries no arm or back shaping (the elbow is still bent there);
  - keys are 120/145/156/166.

## Results

**Press path** (`r31_build.json`):
- above 95°: crossing pairs 0 all the way to lockout;
- lockout stretch: 385 (B5 without S7) → **47** (R29 83);
- lockout collapse 0;
- lockout volume **+1.58 %** (R29 +4.41 %): the lighter back;
- mid-press stretch: 1–46 over 118–151° (R29 42–112).

**Not yet as good:**
- At 156° the stretch is 169 (R29 113). This is the same spike R29 had at its 156° key.
- At 85–91° there are 6 crossing pairs, and at 91° collapse 2. These come from the re-bound base: B5 without S7 shows the same, and S7 does not act there.

**Targets:**
- crossing pairs 0 at every key;
- at **156°, 4 crushed triangles remain** after the clean-up, by the trapezius next to the neck and on the shoulder cap. Recorded, not hidden; the test allows ≤ 4;
- 145° and 166° have no crushed triangles over the whole body after the clean-up.

**Bake:** p99 error 0.1–1.3 mm across the keys. **Sharp folds at lockout:** 50 (R29 58).

**Benchmarks vs R29** (`r31_validation.json`):
- no new crossing pairs or collapse in any of the 13;
- shoulder_press collapse 1 → 0;
- stretch is slightly higher in three, recorded:

  | Benchmark | R29 stretch | R31 stretch |
  |---|---|---|
  | shoulder_press | 118 | 130 |
  | push_up | 91 | 101 |
  | bent_over_row | 11 | 13 |

**Visual** (`renders/strip_r29_r31.jpg`, `renders/upperarm_follow_r29_r31.jpg`, `press/shoulder_press_r31_views.mp4`): through the press, R31's upper arm runs straight into the shoulder, with no bend a third of the way down and no ring. The reference photo stays outside the repo.

**Tests:** `test_original_review_candidate_r31.py` passes 3/3:
- the lineage sha chain;
- lockout, follow flag, S5/S7 keys and the 95° start;
- upper-arm weight raised (re-measured R18 vs R31);
- press path and benchmarks vs R29.

R29 and R28 tests still pass.

## Defect found while testing (script fixed, R31 not rebuilt)

On 22 vertices per side at the top of the shoulder (6 influences in R18), the follow script's 4-influence trim dropped the small upper-arm weight it had just raised: by at most 0.032, handed back to the shoulder cap. The script now always keeps the upper-arm influence when it trims. R31 was built before the fix. The effect is at the very top of the shoulder, where the hand-over is close to zero anyway, so R31 was not rebuilt. The test records the 22 vertices and the 0.032 bound instead of claiming "only ever increased".

## Still to watch

- **The 156° key:** stretch spike (169) and 4 crushed triangles.
- **The early press (85–91°):** 6 crossing pairs from the re-bound base.
- **Stretch:** slightly higher in shoulder_press, push_up and bent_over_row.
- **The owner's eye:** the owner should confirm the arm now reads as one bone from shoulder to elbow, and that the back is light enough.
