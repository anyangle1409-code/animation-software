# ORIGINAL_v1 R34: bounded front-armpit experiment (16 October 2026)

**NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW. NOT ACCEPTED.** This is a separate candidate, not a production asset.

## Change and rationale

R33's inverse bake matches the front target, but guard cutbacks at full-press t=0.60 and benchmark t=0.55 damage the front patch. Cutbacks can themselves create new intersections and collapsed faces, causing further cutbacks.

R34 starts from R33 and restores inverse-bake detail at 120/145 only inside a symmetric front geodesic patch (full inside 2 cm, smoothly fading to zero at 5 cm). It adds an intermediate S7 key at 130 degrees, with 30 small Taubin fairing passes inside that same patch. Outside the patch the intermediate key initially reproduces the existing 120/145 interpolation exactly.

The original smooth and final guards run on the resulting candidate with 41 samples, containing every old guard sample and every nine-frame benchmark sample. Their source and thresholds are unchanged. An unguarded inverse reference is generated in memory solely as input; it is never saved as a candidate.

No canonical bones, basis mesh, skin weights or non-S7 shape keys are intentionally changed. All HGPT_SHOULDER keys are checked as part of the non-S7 identity comparison.

## Fixed regression goals, established before implementation

- Front sentinel vertex 18633: under 10 mm from the unchanged R33 target at both 120 and 145 degrees.
- Front-patch maximum dihedral at 130 degrees: under 100 degrees (R33 measured 132.393).
- Lockout absolute volume change remains strictly below 2.5%, matching the existing R33 requirement.
- Both original guard baselines are rechecked at 82 path/time combinations on the final saved model.
- These new tests failed on unchanged R33 with exactly three assertion failures. No pre-existing test or tolerance was changed.
- Numerical comparison uses clean Blender processes for each model/path, avoiding inherited module hooks.

Front test passed: **True** (process exit 0).

Acceptance checks:

{
  "front_test_process": true,
  "original_lockout_volume": true,
  "original_guards_rechecked": true,
  "original_post95_collision_rule": true,
  "preservation": true,
  "no_frame_count_regressions": true
}

Reporting was strengthened after independent code review: retain the original volume limit, require exit zero, and remeasure the guards against their own no-S7 baseline. No deformation test was weakened.

## Target-fit measurement at the front sentinel

| Elevation | R33 error (mm) | R34 error (mm) |
|---|---:|---:|
| 120 | 20.979 | 0.078 |
| 145 | 23.443 | 0.091 |
| 156 | 4.878 | 4.878 |
| 166 | 0.106 | 0.106 |

Full distributions remain in r33_press.json and r34_press.json.

## Preservation checks

{
  "bones": true,
  "basis": true,
  "polygons": true,
  "weights": true,
  "non_s7": true
}

The skeleton matrices/parents/deform flags, basis, topology, all weights and every non-S7 key must match R33 exactly.

## Regressions (all retained)

0 increases were measured across the 41-frame full press and all 13 benchmark movements, comparing each actual frame with R33.

```json
[]
```

A failed front goal, nonzero test exit, preservation failure, original lockout-volume failure, residual guard violation or any recorded increase rejects the numerical experiment. Visual review is still required even if numerical checks pass. The tests do not establish anatomical correctness or medical approval.

## Review files and reproduction

- r33_r34_front_closeups_120_130_145.jpg: same-camera closeups at exact 120/130/145-degree elevations.
- r33_r34_same_angle_comparison.jpg: identical 118/132/145/156-degree vicinity press times, back/front/three-quarter views.
- shoulder_press_r34_three_views.mp4: raw skin views along the complete up/down press.
- front_test.txt: unchanged R34 regression test output.
- r34_build.json: exact candidate settings and guard history.
- r33/r34_benchmarks.json: all 13 movement results.
- r34_review.json: status, fit and all numerical regressions.

Build and render commands are recorded in .github/workflows/original-review-front-regression.yml. Python scripts run through pinned Blender 5.2.1. Each measurement/render invocation uses a fresh process.

No owner reference photos are included. No merge or force-push is part of this workflow.
