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


## Post-render review: 2026-10-16

Native Blender 5.2.1 run 38970547784 passed, source commit 9fb54842128d0f436e083815d07105a78eaebce2. Generated model/evidence commit c400becd8e4fcc0694e18e1f3168a04e5388a5da. This numerical success does not establish visual acceptance.

At the owner's exact marked full-press frame (135.625 degrees, t=0.625), measured stretched-triangle count (>2x neutral area) is **81 R34 → 66 R37**. R36 was 11, so R37 gives back some of that local improvement to preserve the rest of the motion. R37 rear contour corner peaks are left 9.0535/right 10.0042 degrees; three-quarter peaks are left 16.3636/right 52.7357. Both rear silhouettes are visibly rounder than R34 in the exact native-camera comparisons added here as R34_R37_marked_angle_left.jpg and R34_R37_marked_angle_right.jpg.

**Remaining visual concern:** the front closeups still show an abrupt crease near 130 degrees, especially on the right. Do not call this finished from passing the numerical crease threshold. Top-of-press stretch stays 80, unchanged from R34; the shoulder-press benchmark still has two collapsed triangles at its worst frame. Those are unresolved.

The broader changed target also fits the old R33 whole-surface target less closely: at 120 degrees max error 8.371→24.585mm and at 145 degrees 9.135→22.044mm. Protected anterior sentinel errors remain exactly 0.0782/0.0912mm. Do not present the sentinel as a measurement of the entire front patch.

An additional offline solver diagnostic found face normals rotated >90 degrees relative to the initial R36-derived mid shape in 19 of 82 predicted poses, up to 18 faces (2 faces at the marked full-press pose). This is not by itself proof of inversion, since the reference is another deformed surface, but it warrants investigation with the front crease. The diagnostic uses the saved linear response and solved deltas, not a new native saved-model test; it does not replace or weaken any existing check. Counts and method are recorded in r37_normal_rotation_diagnostic.json.

Status remains **owner visual review pending; front-crease concern open**. Canonical/protected assets and existing tests remain unchanged.
