# Mesh coordination report — current exercise library against the high-detail candidates

2026-09-25. Read-only measurement; no asset, grip, retargeting or production change was made to produce it.

**Why.** Before any future grip or production-character change, work is to be coordinated against the latest accepted mesh candidate and the full current exercise library. This records where the library stands against both today.

## What was measured

- **Runtime:** `chatgpt/absolute-retarget-imports` at `6537905`: 28 exercises, frozen 63-bone `hgpt_canonical_v3`.
- **Meshes:** the production character (`review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb`) as the reference, and two high-detail candidates taken from `codex-high-detail-candidate-v14-finger-body-review-20260924`. Both hashes match GPT's `CANDIDATE_BASELINE_MANIFEST.json`:
  - **V8**, the accepted body and knee baseline (`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb`, `a7655f68…`);
  - **V13e**, the last hand review candidate (`…v13e_fingertip_retopology.glb`, `08c56bec…`).
- **Gates:** every test that switches character through `REAL_CHARACTER_GLB`:
  - self-collision (arm against trunk);
  - equipment clearance, including bench-pad support;
  - the floor tests (Russian twist, crunch, sit-up);
  - the production-character feet for the split squat and both lunges;
  - hand roll, palm mapping, unmapped bones and the importer diagnostic.

## Result

| Mesh | Result |
|---|---|
| Production | All pass. |
| V8 | Everything passes except the arm-to-chest distances and one incline-curl graze below. |
| V13e | Identical to V8 on every body measurement, as it should be, since only the hands changed. |

Also, for both candidates:

- Floor and bench contact, both lunges' feet, hand roll and palm mapping pass.
- The importer diagnostic crashed on V13e, and only there. The cause was the harness (`Math.max(...ratios)` over one ratio per edge exceeds the argument limit on the denser hand), not the mesh. It is fixed in the same commit as this report and now passes on both.

### Arm against chest (self-collision), closest distance in mm

These are gaps, not penetrations. Nothing is inside on any mesh. "Below baseline" means more than the gate's 1 mm slack under the production character's recorded value, which is how the gate fails. On V8 and V13e, **19 of 28 exercises fall below baseline**. The rest pass only on the slack, the tightest being the front raise at 0.14 mm.

| Exercise | Production | V8 | V13e | V8 vs baseline |
|---|---:|---:|---:|---|
| `dumbbell_front_raise` | 1.12 | 0.14 | 0.14 | within baseline |
| `cable_pallof_press` | 1.85 | 0.42 | 0.42 | below baseline |
| `russian_twist` | 1.84 | 0.47 | 0.47 | below baseline |
| `cable_woodchop` | 0.98 | 0.49 | 0.49 | within baseline |
| `dumbbell_romanian_deadlift` | 1.17 | 0.51 | 0.51 | within baseline |
| `dumbbell_bicep_curl` | 4.73 | 0.65 | 0.65 | below baseline |
| `dumbbell_bent_over_row` | 1.52 | 0.66 | 0.66 | within baseline |
| `dumbbell_reverse_curl` | 2.59 | 0.67 | 0.67 | below baseline |
| `air_squat` | 1.36 | 0.73 | 0.73 | within baseline |
| `pull_up` | 2.02 | 0.74 | 0.74 | below baseline |
| `sit_up` | 1.59 | 0.78 | 0.78 | within baseline |
| `dumbbell_shoulder_press` | 1.95 | 0.81 | 0.81 | below baseline |
| `seated_dumbbell_shoulder_press` | 1.95 | 0.81 | 0.81 | below baseline |
| `cable_triceps_pushdown` | 4.64 | 0.81 | 0.81 | below baseline |
| `dumbbell_overhead_triceps_extension` | 2.89 | 1.25 | 1.25 | below baseline |
| `dumbbell_calf_raise` | 5.59 | 1.53 | 1.53 | below baseline |
| `crunch` | 1.94 | 2.23 | 2.23 | within baseline |
| `incline_dumbbell_curl` | 1.79 | 2.33 | 2.33 | within baseline |
| `split_squat` | 4.22 | 2.55 | 2.55 | below baseline |
| `dumbbell_lateral_raise` | 4.14 | 2.55 | 2.55 | below baseline |
| `forward_lunge` | 4.22 | 2.55 | 2.55 | below baseline |
| `reverse_lunge` | 4.22 | 2.55 | 2.55 | below baseline |
| `standing_calf_raise` | 5.10 | 2.69 | 2.69 | below baseline |
| `dumbbell_hammer_curl` | 5.02 | 2.72 | 2.72 | below baseline |
| `farmers_walk` | 5.70 | 2.87 | 2.87 | below baseline |
| `dumbbell_bench_press` | 8.63 | 3.83 | 3.83 | below baseline |
| `push_up` | 7.89 | 4.00 | 4.00 | below baseline |
| `dumbbell_fly` | 10.28 | 5.21 | 5.21 | below baseline |

This is the high-detail body's arm and chest volume, not any exercise's motion. It matches what GPT's `NEXT_ACTION.md` reported for the first 14 exercises.

### Equipment against the body, mm (negative is into it)

Items within 10 mm, and every support pad:

| Exercise | Item | Measure | Production | V8 | V13e |
|---|---|---|---:|---:|---:|
| `dumbbell_bench_press` | bench | deepest | -13.69 | -14.30 | -14.30 |
| `dumbbell_bent_over_row` | dumbbell_l | closest | 10.93 | 6.77 | 6.77 |
| `dumbbell_bent_over_row` | dumbbell_r | closest | 10.93 | 6.75 | 6.75 |
| `dumbbell_bicep_curl` | dumbbell_l | closest | 11.86 | 7.92 | 7.92 |
| `dumbbell_bicep_curl` | dumbbell_r | closest | 12.01 | 7.98 | 7.98 |
| `dumbbell_calf_raise` | dumbbell_l | closest | 8.40 | 5.99 | 5.99 |
| `dumbbell_calf_raise` | dumbbell_r | closest | 8.43 | 5.95 | 5.95 |
| `dumbbell_fly` | bench | deepest | -13.69 | -14.30 | -14.30 |
| `incline_dumbbell_curl` | bench | deepest | -10.34 | -10.34 | -10.34 |
| `incline_dumbbell_curl` | dumbbell_l | closest | 3.39 | -0.76 (1 inside) | -0.76 (1 inside) |
| `incline_dumbbell_curl` | dumbbell_r | closest | 3.38 | -0.79 (1 inside) | -0.79 (1 inside) |
| `seated_dumbbell_shoulder_press` | bench | deepest | -8.95 | -10.30 | -10.30 |

- **Pads.** Support pads may be pressed into by up to 15 mm. The flat bench under the bench press and fly takes 14.3 mm on the candidates, against 13.7 mm on production: close to the limit.
- **The incline curl** grazes the thigh with one vertex per side (0.76 and 0.79 mm) at the end of the repetition.
- Every other item clears. The curls' and row's dumbbells sit about 4 mm nearer the thighs than on production.

## Items to settle before the high-detail body is bound for production

1. **Arm-to-chest baselines.** Either re-record the self-collision baselines against the accepted mesh once it is final, or give the arm/lat/chest region more clearance mesh-side. The tightest are:
   - front raise 0.14 mm;
   - Pallof press 0.42 mm;
   - Russian twist 0.47 mm;
   - woodchop 0.49 mm;
   - Romanian deadlift 0.51 mm.
2. **Incline curl against the thigh.** A mesh-side thigh adjustment, or an exercise-side tweak to the incline curl's end position. The latter needs your approval, since the incline curl is an existing exercise.
3. **Bench pad compression** is within 0.7 mm of the limit on the bench press and fly. Re-tune the lying height if the final body is any fuller in the back.

None of these block the hand work, and no grip refit or production change was made. Re-run this report against each newly accepted candidate: `scripts/mesh-coordination-report.sh OUT_DIR v8=…glb v13e=…glb` runs the gates and prints these tables (`scripts/mesh-coordination-report.py`).
