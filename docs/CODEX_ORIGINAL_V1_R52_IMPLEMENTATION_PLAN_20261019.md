# R52 temporal surface study Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Investigate a smoother shoulder/side trajectory without changing the approved R47 outline or protected anatomy.

**Architecture:** Add independent, bounded integer-degree increments to the existing S7 native sampling layer. A matrix-free primal-dual feasibility calculation couples the original press-motion response with spatial and temporal regularization. Every finite-iteration state remains an unsafe study until independently checked; native rendering and all failures are retained.

**Tech Stack:** Python, NumPy2.3.5, SciPy1.17.0, checksum-pinned Blender5.2.1 and existing native checks.

**Spec:** docs/CODEX_ORIGINAL_V1_R52_PROPOSED_TEMPORAL_STUDY_20261019.md; owner approved19October07:59 Europe/London.

## Global Constraints

No old model, test, workflow or production asset is edited. Same approved material union, frozen skeleton/Basis/weights/topology/non-S7/HGPT keys, source110/166, anchors and any-angle distal arm stay fixed. Keep1mm outline,0.5mm original motion,2degree crease and45mm material guards. No save or promotion in this study. Native evidence and owner approval are distinct.

## Review Focus

Negative/cancelled coefficient vectors must not identify an incorrect elevation.
Adjacent fixed controls must not permit displacement outside the material domain.
A sampled motion pass must not hide integer-degree jumps.
Native independent-key installation must match its affine response to0.01mm.
Legacy seven-control diagnostics must not be presented as validation of independent dense increments.

### Task1: Independent temporal representation

Create scripts/original_review_r52_temporal.py and tests/test_original_review_r52_temporal.py.
Interfaces: decode(old_weight)->(lo,hi,alpha), blend(dense,mapping), blend_adjoint(force,mapping,nodes).
- [ ] Test dense sampling reproduces old cubic trajectories, including negative weights, exact source knots and below95 activation.
- [ ] Test forward/adjoint dot identity and reject coefficient mismatch/nonfinite input.
- [ ] Add dense masks: exact original per-source masks, strict original material union and zero95/110/166/anchors/distal material.
- [ ] Add a regression rejecting the90mm neighboring-control jump even when sampled motion passes.
- [ ] Run focused tests and preserve red/green logs.

### Task2: Bounded feasibility fitting

Create scripts/solve_original_review_r52.py and tests/test_original_review_r52_projection.py.
Interface: original response and R51 retained delta -> NPZ containing dense_delta plus source-knot projection delta and explicit study status.
- [ ] Test mask/material/marked-boundary projection and motion forward/adjoint identity.
- [ ] Use original back-motion mask and exact original affine transforms; primal-dual motion-ball constraints and3mm per-degree material-step constraint, plus spatial and temporal quadratic regularization.
- [ ] Preserve current marked silhouette-support vertices while allowing other skin points to redistribute; independently measure actual full outline for retention.
- [ ] Bound runtime, log every retained state, mark incomplete/failed constraints; never call an iteration a repaired model.
- [ ] Run a short local preflight before native CI. Do not weaken a test when infeasible.

### Task3: Actual native evidence

Create new R52 native installer/detector/renderer/benchmark/package scripts and workflow original-review-r52.yml.
- [ ] Install dense increments directly over the unchanged R41 baseline S7 interpolation; protect identities.
- [ ] Run all original83 area/contact/orientation/affine checks and13 benchmarks on the actual dense candidate.
- [ ] Run original tests unchanged on the explicitly labeled source-knot projection; additionally enforce equivalent original thresholds on actual native dense geometry. Projection checks alone never certify the new representation.
- [ ] Add161-pose full-press coverage against native R41; report normalized acceleration and integer-degree step guards separately. No false pass if undersampled.
- [ ] Render actual R51/R52 matching rear/three-quarter comparisons, both closeups and press videos, with R47 as approved-outline reference.
- [ ] Keep all failures in a new codex_review_r52_study_20261019 folder; no model-save step.
- [ ] Commit source normally, inspect the finished run/artifact/media, then report saved status and all regressions honestly.
