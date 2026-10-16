# ORIGINAL_v1 R37: coupled skin-transition constraints

**NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW. Owner visual approval pending.**

R36 softened the marked arm-to-side point and reduced full-press stretch at 135.625 degrees from81 to11, but failed17 comparisons elsewhere. A benchmark collision at t=0.975 caused the original guard to change the156/166-degree keys, raising lockout stretch80→111. R36 is preserved as rejected. Single-key full-press area constraints did not cover the second press path or transitions.

R37 starts from immutable R34. It takes R36's120/130/145 mid-press skin shape, introduces a110-degree S7 key whose base exactly interpolates R34, and solves material-coordinate adjustments across41 samples of each press path. Native skin-response matrices are checked against Blender evaluation before optimization (maximum allowed error0.01mm). Adjustments follow each key's local skin tangent and stay within15mm of the initial mid shape. The156/166-degree keys remain exactly R34's; if either original guard changes them, no model is saved. The original guards and every existing tolerance are unchanged.

## Measured checks

```json
{
  "front_test_process": true,
  "original_lockout_volume": true,
  "original_guards_rechecked": true,
  "original_post95_collision_rule": true,
  "preservation": true,
  "no_frame_count_regressions": true,
  "new_contour_goals": true
}
```

Front test exit: 0. Contour test exit: 0. Regressions versus R34: **0**; all are retained in r37_review.json. Any increase rejects the numerical candidate. The fixed contour requirements remain bilateral rear peak<12.5degrees at135.625 and three-quarter no worse than R34. Front fit<10mm, crease<100degrees, original strict lockout volume<2.5%, zero intersections/collapses above95degrees, and82 final guard comparisons remain intact. All41 full-press samples and actual frames of13 movements are compared. No test was weakened or deleted.

The skeleton, basis, topology, weights and every non-S7 coordinate (including HGPT_SHOULDER keys) must exactly match R33/R34. R34 baseline reports are copied after verifying its model hash. R37 is measured in fresh native processes. Linear response, solver history, exact settings, frozen-key verification and guard histories are in r37_build.json.

## Review files and reproduction

r36_r37_same_angle_comparison.jpg and bilateral junction/front closeups compare the preceding candidate at identical poses/cameras. shoulder_press_r37_three_views.mp4 is the full raw-skin press. Files are under codex_review_r37_20261016. Owner reference images stay out of the repo.

Workflow .github/workflows/original-review-r37.yml uses pinned Blender5.2.1: export_original_review_r37_blender.py → solve_original_review_r37.py → build_original_review_candidate_r37_blender.py -- build → unchanged native measurements/guards/front test → fixed contour test → renders/package. No production assets, merge or force push.
