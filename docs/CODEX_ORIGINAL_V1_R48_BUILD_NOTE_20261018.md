# R48 surface repair plan

Owner confirmed the actual R47 overall arm-to-body outline on 18 October
2026: “Yes that looks good.” This approves the outline, not R47's failed
surface quality or movement. R47 remains an unsaved rejected study.

Root cause: R47's direct world-X displacement changes by about 24 mm over
the small patch next to fixed anchor 18633. At the marked press pose this
reverses 17 triangle normals. The anchor itself must remain fixed.

The repair must fit surface quality and motion together. Independent static
surface extension was investigated and rejected before a native build. The
new joint-pose fitter uses the existing area/contact/front/motion/normal-cone
feasibility machinery, the exact authorized R47 editable coordinates and the
actual R47 whole outline in both review views. It starts at the safe R41
zero increment; known R47 contact pairs are included as separation constraints.

- [x] Record a failing marked-pose orientation regression test on R47 (17).
- [x] Reject static extension probes after measuring all response poses.
- [x] Add a separate 1mm actual-R47 rear/three-quarter outline guard; it
  correctly rejects static surface extension (8.376mm maximum error).
- [x] Preserve every parent response array, including the old R42 target and
  full posterior coverage. Three preparation tests pass after reproducing
  an overwritten-target failure in the discarded preparation.
- [x] Verify the analytic silhouette derivative. Finite differences use
  float64, matching the fitter; the original float32 test input quantized
  0.1-micron perturbations. Assertion precision was not relaxed.
- [ ] Measure all 82 affine response poses, front response, unchanged motion
  and posterior crease tests, original source/dense 45 mm limits, fixed
  anchors and globally protected distal arm. Keep rejected experiments.
- [ ] If justified, build a separate R48 native study with pinned Blender
  5.2.1, all unchanged acceptance tests, identity verification, matched
  R47/R48 rear and three-quarter images, and a press comparison video.

No skeleton, weights, Basis, topology, non-S7 keys, HGPT_SHOULDER keys,
canonical or production assets may change. No test threshold is relaxed.
No private reference photo or traced outline enters repository inputs.
No model is accepted or saved on the basis of an outline-only approval.

## Discarded local research

These are affine diagnostics, not native Blender renders or saved models.

| Experiment | Marked reversals | Max posterior crease excess | Back motion excess | Other failure |
|---|---:|---:|---:|---|
| R47 native parent |17|179.213deg|3.557mm|468 new contact records|
| Static full-coordinate ARAP |8|178.524deg|4.277mm|8.376mm marked outline error|
| Static projected-coordinate ARAP |18|146.811deg|4.730mm|56.538mm dense displacement exceeds45mm|
| Single-key crease fit, reused through press |0|167.525deg|3.226mm|4.619mm marked outline error;45.138mm dense displacement|

The single-key probe reached about2.03deg posterior excess at its fitted
136deg pose, but nearby motion still folded. It is discarded, not promoted.
The tighter all-surface regularizer also lost the approved contour; it is
retained as a diagnostic, never counted as a passing repair.

## Bounded joint-pose native study

Workflow `.github/workflows/original-review-r48.yml` gives the corrected
joint fitter25minutes, then independently measures and renders its retained
state with pinned Blender5.2.1. A timeout is recorded explicitly. No saved
model or accepted state is inferred from workflow success. If no accepted
fit state exists, report the blocker and retain logs instead of claiming
new renders. The complete study remains in its own R48 folder.

The initial corrected local accepted state passes the unchanged motion test
(0.449197mm excess) and posterior crease test (1.837214deg excess). The
outline remains unresolved at this early stage.

The joint fitter's minimum-L1 tie-break proved expensive after the optimal
feasible contour step had already been found. R48's own LP helper returns
that first optimal feasibility solution directly. A new regression test
proves shape slack cannot relax a conflicting hard safety inequality; it
passes. All proposals still undergo the same nonlinear acceptance checks.
This changes an optimization preference, not any test or safety threshold.
All native outcomes, the five historical contour/front tests, new actual
outline test, unchanged R47 scope tests, and before/after media must be
reported, including failures. Do not silently change the old outward target
or remove its failing diagnostic. Do not expand R47's editable material mask
or reduce its posterior coverage to obtain a pass.
