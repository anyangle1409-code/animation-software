# ORIGINAL_v1 R35: broader arm-to-side skin transition

**REJECTED_NUMERIC_CHECKS. Owner visual approval: pending.**

The owner approved a broader local skin transition rebuild on 16 October 2026 after rejecting R34's arm-root shelf. The frozen skeleton, skin weights, basis, topology and all non-S7 keys are required to remain identical. No HGPT_SHOULDER key is edited. R34 and all earlier assets are immutable.

R35 uses an anchored thin-plate surface target over a broader shoulder/upper-arm/side patch. The support ellipsoid is 19/20/22 cm; its outer 35% fades to a fixed boundary. A 15mm front-sentinel neighborhood is protected, with a 30mm blend. Position-anchor coefficient is 0.001. Gains are 1 at 120/130/145 degrees, 0.4 at 156 and 0 at 166. Targets are inverse-baked into existing S7 keys; the original guards run unchanged at 41 samples on each of two paths. The exact offsets and guard history are in r35_build.json. No new key family or mesh topology is introduced.

## Tests and measured results

The new rear contour test was fixed before the rebuild. At the owner's exact 135.625-degree frame, both rear outlines must have less than 12.5 degrees of tangent change over adjacent 10mm spans (sampled at 2mm, 15-80mm below GH). R34 fails twice: left 17.5147, right 16.9866. Three-quarter peaks must not worsen from R34 (left 35.407937, right 53.426476 degrees). These outline checks do not measure every visible surface ridge and never substitute for owner review.

The R34 front tests run unchanged on R35; they retain the 10mm front-fit and 100-degree dihedral limits. Every old test remains intact. New reporting tests reject truncated or mismatched frame lists before comparison; this strengthens reporting only. Final guard checks compare against no-S7 at 82 samples; the strict original 2.5% lockout-volume rule and zero pairs/collapses above 95 degrees remain intact. Every actual frame of 13 benchmarks and 41 full-press samples is compared with R34. Any count increase rejects the numerical candidate. Identity compares to R33, whose protected data R34 already exactly matches.

Acceptance checks:

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

All regressions (including worse results):

```json
[
  {
    "path": "press",
    "t": 0.35,
    "metric": "stretch",
    "r34": 103,
    "r35": 114
  },
  {
    "path": "press",
    "t": 0.375,
    "metric": "stretch",
    "r34": 88,
    "r35": 142
  },
  {
    "path": "press",
    "t": 0.4,
    "metric": "stretch",
    "r34": 81,
    "r35": 180
  },
  {
    "path": "press",
    "t": 0.425,
    "metric": "stretch",
    "r34": 86,
    "r35": 247
  },
  {
    "path": "press",
    "t": 0.45,
    "metric": "stretch",
    "r34": 88,
    "r35": 365
  },
  {
    "path": "press",
    "t": 0.475,
    "metric": "stretch",
    "r34": 85,
    "r35": 490
  },
  {
    "path": "press",
    "t": 0.5,
    "metric": "stretch",
    "r34": 91,
    "r35": 631
  },
  {
    "path": "press",
    "t": 0.525,
    "metric": "stretch",
    "r34": 91,
    "r35": 705
  },
  {
    "path": "press",
    "t": 0.55,
    "metric": "stretch",
    "r34": 83,
    "r35": 710
  },
  {
    "path": "press",
    "t": 0.575,
    "metric": "stretch",
    "r34": 88,
    "r35": 717
  },
  {
    "path": "press",
    "t": 0.6,
    "metric": "stretch",
    "r34": 79,
    "r35": 714
  },
  {
    "path": "press",
    "t": 0.625,
    "metric": "stretch",
    "r34": 81,
    "r35": 701
  },
  {
    "path": "press",
    "t": 0.65,
    "metric": "stretch",
    "r34": 81,
    "r35": 696
  },
  {
    "path": "press",
    "t": 0.675,
    "metric": "stretch",
    "r34": 82,
    "r35": 672
  },
  {
    "path": "press",
    "t": 0.7,
    "metric": "stretch",
    "r34": 92,
    "r35": 663
  },
  {
    "path": "press",
    "t": 0.725,
    "metric": "stretch",
    "r34": 66,
    "r35": 523
  },
  {
    "path": "press",
    "t": 0.75,
    "metric": "stretch",
    "r34": 45,
    "r35": 412
  },
  {
    "path": "press",
    "t": 0.775,
    "metric": "stretch",
    "r34": 36,
    "r35": 295
  },
  {
    "path": "press",
    "t": 0.8,
    "metric": "stretch",
    "r34": 50,
    "r35": 202
  },
  {
    "path": "press",
    "t": 0.825,
    "metric": "stretch",
    "r34": 53,
    "r35": 149
  },
  {
    "path": "press",
    "t": 0.85,
    "metric": "stretch",
    "r34": 58,
    "r35": 127
  },
  {
    "path": "press",
    "t": 0.875,
    "metric": "stretch",
    "r34": 65,
    "r35": 87
  },
  {
    "path": "press",
    "t": 0.975,
    "metric": "stretch",
    "r34": 78,
    "r35": 80
  },
  {
    "path": "shoulder_press",
    "t": 0.25,
    "metric": "stretch_gt_2",
    "r34": 83,
    "r35": 127
  },
  {
    "path": "shoulder_press",
    "t": 0.375,
    "metric": "stretch_gt_2",
    "r34": 80,
    "r35": 397
  },
  {
    "path": "shoulder_press",
    "t": 0.5,
    "metric": "stretch_gt_2",
    "r34": 86,
    "r35": 712
  },
  {
    "path": "shoulder_press",
    "t": 0.625,
    "metric": "stretch_gt_2",
    "r34": 76,
    "r35": 653
  },
  {
    "path": "shoulder_press",
    "t": 0.75,
    "metric": "stretch_gt_2",
    "r34": 46,
    "r35": 428
  },
  {
    "path": "shoulder_press",
    "t": 0.875,
    "metric": "stretch_gt_2",
    "r34": 38,
    "r35": 120
  },
  {
    "path": "shoulder_press",
    "t": 1.0,
    "metric": "stretch_gt_2",
    "r34": 49,
    "r35": 96
  }
]
```

Front tests: exit 0; contour tests: exit 0. Full logs, fit distributions, benchmark frames and guard measurements accompany the model. A numerically rejected candidate is retained as evidence and never presented as accepted.

## Review and reproduction

- r34_r35_junction_l_closeups.jpg and r34_r35_junction_r_closeups.jpg: exact 120/130/135.625/145/156-degree rear and three-quarter details.
- r34_r35_front_closeups.jpg: bilateral front-boundary inspection.
- r34_r35_same_angle_comparison.jpg: matched full views.
- shoulder_press_r35_three_views.mp4: complete up/down press, raw review skin.
- r35_review.json and r35_build.json: status, all metrics and exact settings.
- probe/r35_contour_surfaces.npz: fresh saved-model geometry for reproducible contour checks.

Workflow: .github/workflows/original-review-r35.yml; pinned Blender 5.2.1. Build: export posed parent; run fair_original_review_r35_targets.py; build_original_review_candidate_r35_blender.py -- build; run unchanged measurements/tests; render both versions in clean Blender processes; package evidence. No owner reference images are stored. No merge or force push.
