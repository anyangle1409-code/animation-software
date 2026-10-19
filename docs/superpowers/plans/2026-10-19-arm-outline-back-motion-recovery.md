# ORIGINAL_v1 arm-to-body outline and back-motion recovery plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Track steps with checkboxes. This is a staged diagnostic and visual-target plan; the geometry implementation is selected only after its evidence gates.

**Goal:** Match the owner's supplied arm-to-body relationship throughout the press while eliminating artificial torso swelling and preserving the improved arms and elbows.

**Architecture:** Separate reference interpretation, spatial surface repair and temporal deformation. Establish the intended silhouette before optimizing it; validate actual Blender geometry throughout the movement. R52 is rejected evidence, not the approved shape or a safe model baseline.

**Tech Stack:** Existing first-party authoring scripts; checksum-pinned Blender 5.2.1 and Python. Existing pinned fitting dependencies only if needed; no new third-party assets or app dependencies.

**Spec:** Owner feedback of 19 October 2026 08:39–09:15 Europe/London; docs/HANDOFF_ORIGINAL_V1_PRESS_SHOULDER_20261016.md; docs/CODEX_ORIGINAL_V1_R52_BUILD_NOTE_20261019.md; docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R52_20261019.md. Private original reference IMG_1978(1).jpeg and marked IMG_1987.jpeg remain outside Git.

## Global constraints

- Work only on claude/original-v1-consolidated-review-20261014; no main merge or force-push.
- Planning HEAD: 54863ba4addd8fcb0d8547b97e24310290758b37. Fetch live state before implementation.
- Canonical skeleton, Basis, topology, weights, groups, HGPT_SHOULDER/non-S7 keys and V-production assets remain protected.
- Preserve current approved elbow/distal-arm detail. Retain existing source110/166, anchor, distal and45mm-cap protections unless a concrete conflict is demonstrated and the owner explicitly approves a narrowly specified change.
- New geometry must use a new separately named candidate folder, own test and measured short doc. Check whether R53 is available before allocating it.
- Keep every old test and threshold unchanged. Conflicting historical shape targets remain visible diagnostics; document why they differ from the newly confirmed requirement.
- No reference photos or private reference traces in Git.
- No model save/promotion during diagnostic or outline-preview work. A later save requires actual safety gates; visual approval remains separate.

## Review focus

1. A correct still silhouette can develop an armpit hook at another press angle.
2. A smaller41-frame motion error can hide jumps between frames.
3. A target shape can be correct while folds, reversed faces or intersections remain.
4. Source anchors or protected166 can conflict with the intended silhouette; do not silently release them.
5. A back with no swelling must still allow natural shoulder-blade movement; do not freeze the entire torso.

## Evidence already established

- R52 workflow39215634074 completed19October2026 08:44 London; artifact12170257665 hash verified.
- No R52 Blender model saved. R41 remains the immutable saved baseline.
- R52 actual marked outline error0.949948mm passes the historical R47-target1mm guard, yet the owner rejects the arch in the moving outline.
- Original native motion improved2.074110 to0.706690mm but fails0.5mm.
-83 actual checks:43 pass/40 fail;7 contact records;6 marked reversed faces; posterior crease142.121832degrees excess against2.
-161-pose normalized acceleration excess40.644618mm fails0.5mm; early outward0.624537mm fails0.05mm; adjacent material step3.139175mm fails3mm.
-13 benchmarks ran,6 shoulder-press regressions against R41. Late-press stretch also worsened against R51.
- Do not launch another unchanged long fit or treat the old1mm outline pass as matching the owner's original example.

### Task1: Establish the intended outline visually

**Files:** This plan; a new diagnostic note under docs/ once measurements exist. Private reference inspection/annotation stays outside Git.
**Consumes:** Original IMG_1978 reference, IMG_1987 marked t=0.800 screenshot, actual R51/R52 rendered frames.
**Produces:** Matched-camera comparison identifying the intended arm underside, torso-side transition and rejected hook; a separate list of pose/camera differences.

- [ ] Retrieve the actual original reference and latest markup, rather than using R47 as a substitute.
- [ ] Match available rear and three-quarter native views; include the marked t=0.800 frame and135.625-degree reference pose. Clearly label unmatched reference poses.
- [ ] Show the owner an annotated comparison of the current contour and proposed target interpretation before changing geometry. A drawn target is an explanatory sketch, never a Blender result.
- [ ] Record what the owner confirms. Do not infer full-motion approval from one still.
- [ ] Audit whether fixed anchors/source110/166 prevent the requested contour; demonstrate any conflict visually and numerically before proposing a scope change.

### Task2: Locate the cause of back swelling and intermediate jumps

**Files:** New diagnostic script/test and short note, named for the newly allocated study. Existing scripts remain unchanged.
**Consumes:** Hash-verified R41 baseline, R51/R52 increments, actual161-pose positions and original motion mask.
**Produces:** Worst offending vertices, exercise times/elevations and deformation-family contributions; reproduction of actual versus predicted motion.

- [ ] Reproduce the original41-pose and additional161-pose R52 failures before proposing another temporal method.
- [ ] Compare identical poses with candidate increments disabled, baseline S7 alone and candidate increments active, using temporary in-memory diagnostic states only.
- [ ] Check displacement continuity and slope changes at active control intervals and source110/166; establish why dense motion is much worse than the coarse metric.
- [ ] Compare prediction with actual Blender positions at the offending times, including early outward0.624537mm versus the smaller fitter diagnostic. Do not assume the discrepancy's cause.
- [ ] Record whether swelling comes from baseline deformation, added corrections, interpolation or a combination. Add a regression reproducing the demonstrated cause.

### Task3: Short spatial feasibility study

**Files:** New separately named candidate folder, authoring script, scope/surface tests and short doc.
**Consumes:** Confirmed target from Task1 and cause analysis from Task2.
**Produces:** Actual native target-pose previews with safety and preservation measurements.

- [ ] Author only the smallest permitted skin-region change needed for the confirmed contour, preserving newer arm/elbow detail.
- [ ] Evaluate120/130/135.625/145/156/166degrees plus the marked t=0.800 pose, both sides, rear/three-quarter and front safety views.
- [ ] Measure true surface geometry: new intersections, collapsed/stretching faces, marked normal reversals and crease severity. Preserve all original guard values.
- [ ] Reject unsafe target poses before a long movement fit. Report infeasibility rather than smoothing away the desired outline.
- [ ] Show actual native before/after images before expanding to the full movement.

### Task4: Repair temporal deformation and verify the whole press

**Files:** New candidate-specific temporal implementation and regression tests; old tests untouched.
**Consumes:** Spatially viable targets and the diagnosed temporal cause.
**Produces:** Actual full-press geometry, original and denser motion reports, matched press video.

- [ ] Select the temporal representation only after Task2. Require continuous positions and controlled transitions; no independent frame edits that hide jumps.
- [ ] Include intermediate poses in the fitting/acceptance calculation instead of optimizing only the coarse41 samples.
- [ ] Run original83 native checks and13 movement benchmarks, all historical shape/front tests, protected identities, source/domain/cap preservation and actual-outline measurements.
- [ ] Retain additional161-pose motion with16 normalization and0.5mm limit, adjacent3mm and early outward0.05mm guards. Adaptively inspect between samples near control transitions.
- [ ] Compare with R41 for safety and R51/R52 for improvement/regression. Compare the visual outline with the newly confirmed target throughout movement, not solely R47 at one pose.

### Task5: Deliver an honest review package

**Files:** New candidate doc/JSON, matched rear/three-quarter before-after images, normal-speed press video and focused slow-motion back view.
**Consumes:** All native results and confirmed target.
**Produces:** Owner-review package, with explicit saved-model and unresolved-issue status.

- [ ] State completed/remaining/failed checks and exact regressions. Do not describe code tests or workflow success as geometry acceptance.
- [ ] Show the armpit junction and back at identical exercise times, including the owner's marked time and worst measured motion times.
- [ ] Save a new model only if the full applicable safety/preservation gates pass and the saving stage is explicitly prepared. Keep failures and failed candidates immutable.
- [ ] Owner visual review decides whether the intended shape and movement have been achieved.

## Next concrete deliverable

Task1's reference-versus-current contour comparison, alongside Task2's read-only diagnosis. No new long fit is authorized by this plan alone. Existing large-change approval rule applies when a concrete geometry proposal is ready; do not ask the owner to approve an unspecified algorithm or another unchanged continuation.
