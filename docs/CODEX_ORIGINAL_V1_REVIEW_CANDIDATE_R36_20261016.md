# ORIGINAL_v1 R36: arm-to-side transition with area constraints

**REJECTED_NUMERIC_CHECKS. Owner visual approval pending.**

The owner approved the broader local skin rebuild on 16 October 2026. R35 removed the rear point but expanded many small triangles: at the marked frame the stretch count rose from 81 to 701, so R35 is rejected and preserved. R36 starts from the unchanged R34 model, extends the broader fairing support down the side (vertical radius 28cm versus R35’s 22cm), then redistributes vertices tangentially over that target before inverse baking. R34 is the numerical baseline; R35 is the preceding visual comparison. No R35 geometry is silently replaced.

## Change

Area constraints target at most 1.85 times the neutral triangle area wherever vertices are movable; fixed parts retain their existing area. Existing R34 overstretched triangles are not exempted from the final non-regression test. A lower bound of 0.2 times neutral area prevents crushed triangles. Projection runs 450 Jacobi iterations, snapping to the target triangle surface every five iterations to retain the intended contour. The target generator rejects any face-normal inversion relative to the smooth target or a redistribution slide over 40mm, and records maximum displacement. Nearest-triangle projection is geometric rather than topology-local; final native guards and bilateral visual review remain necessary. This is an authored deformation experiment, not a claim of anatomical correctness. A 2mm posterolateral Gaussian fill (center75mm below GH, vertical sigma16mm, lateral sigma100mm, depth sigma150mm) blends the lower corner; it respects the same front-sentinel protection. Gains remain 1 at 120/130/145 degrees, 0.4 at 156 and zero at 166. The existing 15mm front-sentinel protection and broader support remain unchanged. The native source export records the evaluated neutral surface for area constraints.

Only S7 coordinates change. The same original smooth and final guards run at 41 samples on each of two paths. Protected skeleton, weights, basis, topology and all non-S7 keys are required to match R33 exactly; R34 already matches these. All HGPT_SHOULDER keys remain protected. The R36 build hash, target statistics and guard history are in r36_build.json.

## Tests and measurements

No test or tolerance is weakened. R36 has its own copy of the fixed R35 contour test with identical limits: bilateral rear peak below 12.5 degrees at the marked 135.625-degree frame; three-quarter outline no worse than R34. The unchanged R34 front tests retain the 10mm fit and 100-degree crease limits. The strict original lockout-volume limit remains <2.5%; no pairs or collapses are allowed above 95 degrees. The final saved model is rechecked against no-S7 at 82 samples. Forty-one full-press frames and every actual frame of the same 13 benchmark movements are compared with R34; every increase is retained and rejects the experiment.

```json
{
  "front_test_process": true,
  "original_lockout_volume": true,
  "original_guards_rechecked": true,
  "original_post95_collision_rule": true,
  "preservation": true,
  "no_frame_count_regressions": false,
  "new_contour_goals": true
}
```

All regressions versus R34:

```json
[
  {
    "path": "press",
    "t": 0.35,
    "metric": "stretch",
    "r34": 103,
    "r36": 104
  },
  {
    "path": "press",
    "t": 0.375,
    "metric": "stretch",
    "r34": 88,
    "r36": 96
  },
  {
    "path": "press",
    "t": 0.4,
    "metric": "stretch",
    "r34": 81,
    "r36": 83
  },
  {
    "path": "press",
    "t": 0.775,
    "metric": "stretch",
    "r34": 36,
    "r36": 38
  },
  {
    "path": "press",
    "t": 0.825,
    "metric": "stretch",
    "r34": 53,
    "r36": 58
  },
  {
    "path": "press",
    "t": 0.85,
    "metric": "stretch",
    "r34": 58,
    "r36": 70
  },
  {
    "path": "press",
    "t": 0.875,
    "metric": "stretch",
    "r34": 65,
    "r36": 79
  },
  {
    "path": "press",
    "t": 0.9,
    "metric": "stretch",
    "r34": 68,
    "r36": 92
  },
  {
    "path": "press",
    "t": 0.925,
    "metric": "stretch",
    "r34": 73,
    "r36": 102
  },
  {
    "path": "press",
    "t": 0.95,
    "metric": "stretch",
    "r34": 78,
    "r36": 108
  },
  {
    "path": "press",
    "t": 0.975,
    "metric": "stretch",
    "r34": 78,
    "r36": 110
  },
  {
    "path": "press",
    "t": 1.0,
    "metric": "stretch",
    "r34": 80,
    "r36": 111
  },
  {
    "path": "shoulder_press",
    "t": 0.5,
    "metric": "stretch_gt_2",
    "r34": 86,
    "r36": 118
  },
  {
    "path": "shoulder_press",
    "t": 0.625,
    "metric": "stretch_gt_2",
    "r34": 76,
    "r36": 106
  },
  {
    "path": "shoulder_press",
    "t": 0.75,
    "metric": "stretch_gt_2",
    "r34": 46,
    "r36": 86
  },
  {
    "path": "shoulder_press",
    "t": 0.875,
    "metric": "stretch_gt_2",
    "r34": 38,
    "r36": 66
  },
  {
    "path": "shoulder_press",
    "t": 1.0,
    "metric": "stretch_gt_2",
    "r34": 49,
    "r36": 65
  }
]
```

Front test exit: 0. Contour test exit: 0. Full logs and distributions accompany the candidate. R34's previously measured, immutable native reports are copied as the baseline, after verifying its saved model hash, avoiding redundant benchmark execution; R36 measurements run in fresh processes with unchanged measurement code.

## Review files and reproduction

- r35_r36_same_angle_comparison.jpg: previous candidate and R36 at matching press times/cameras.
- r35_r36_junction_l_closeups.jpg and r35_r36_junction_r_closeups.jpg: exact 120/130/135.625/145/156-degree details.
- r35_r36_front_closeups.jpg: both front transitions.
- shoulder_press_r36_three_views.mp4: complete raw-skin press.
- r36_review.json: all pass/fail checks, regressions and reference-fit measurements.

Workflow .github/workflows/original-review-r36.yml pins Blender 5.2.1. Run build_original_review_candidate_r36_blender.py -- export; project_original_review_r36_targets.py; then the build mode. It preserves R34/R35 and every production asset. No owner reference photos, third-party assets, merge or force push.
