# Phase 9 isolated movement run on the shoulder audit proposal c001 (run 002)

**Status:** verification of solver and follower implementation integrity on the c001 girdle geometry. This is not anatomical acceptance, not Gate 9, and not Phase 10. c001 remains `AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED`.

## Inputs

| Input | Detail |
|---|---|
| Source blend | `audit/candidates/shoulder_proposal_c001/HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_proposal_c001.blend`, sha256 `63ef703ef3a3b160…`. Unchanged before and after (recorded in `isolated_report.json`). |
| Record | A run-local copy of the c001 record, made by `scripts/anatomy_fit/prepare_candidate_movement_run.py`. Its only change is `provenance.out_blend_sha256`, set to the c001 blend. The c001 record itself is not edited. |
| Scripts | `run_isolated_tests_blender.py`, `isolated_tests.py`, `joint_solver.py`. Their hashes are in the report. |

## Result

- **135/135 integrity PASS.**
- **41/43 mirror pairs PASS.** The other two (`hip_rotation_at_0/90_flexion`) have genuinely side-specific source amplitudes and are covered by the solver mirror test.
- **Identical counts and identical non-PASS set to the a003 baseline:** run 014, and `isolated_bone_only_a003_mirror_fix_recheck_001`.

## Defect found and fixed

**Run 001** (`isolated_bone_only_c001_shoulder_proposal_001`, report kept) gave 38/43 mirror PASS with 5 SOLVER_TEST, because:
- the runner treated left/right commands as side-specific whenever they were not *exactly* equal;
- c001's mirrored translation leaves about 1e-14° float noise in the thumb CMC commands;
- so three thumb pairs silently skipped the Blender mirror comparison.

**Fix:** `isolated_tests.commands_match` (relative tolerance 1e-9, noise only), used by the runner.

**Regression:** `scripts/test_isolated_mirror_comparability.py`, using the fixture `../isolated_bone_only_c001_shoulder_proposal_001/mirror_comparability_fixture.json`. On the a003 recheck the counts are unchanged.

## Clips (`clips/`)

- **What they show:** labelled side-by-side GIFs (left a003, right c001; identical cameras and frames) of the solver-keyed tests, with keyframe sheets.
  - Tests: `shoulder_complex_scapular_plane_left`, `shoulder_complex_scapular_plane_right` (scapulothoracic rhythm plus clavicle followers) and `gh_elevation_plane_90_left` (GH only, scapula fixed).
  - Views: front and rear.
- **How they were made:** bone sticks are parented to the armature bones, so the keyed solver motion moves them. The body mesh is not skinned; it is a static scale reference.
- **What they are not:** illustrative of isolated tests only, not functional exercise movement.
- `clips/manifest.json` pins sha256 of every file.

## Not committed (regenerable; hashes in the reports)

- the test blends of runs 001 and 002 and of the a003 recheck;
- the samples of run 001 and of the a003 recheck.

Re-run with:

```
python3 scripts/anatomy_fit/prepare_candidate_movement_run.py --record <c001 record> --blend <c001 blend> --out <run>/inputs/record_for_run.json
python3.13 scripts/anatomy_fit/run_isolated_tests_blender.py --source-blend <c001 blend> --record <run input> --out-blend <new> --out-dir <new dir>
python3.13 scripts/anatomy_fit/render_movement_clips.py --blend <test blend> --record <record> --report <report> --tests ... --views front,rear --step 4 --out <dir>
python3 scripts/anatomy_fit/compose_movement_clips.py --a003 <dir> --c001 <dir> --out <dir>
```
