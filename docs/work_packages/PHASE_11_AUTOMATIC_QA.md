# PHASE 11 — AUTOMATED VISUAL QA

PREPARED ONLY; NOT STARTED. Apply the shared execution contract/tooling-readiness
table. Entry: stable Phase 10 real-engine protocol, exact integration commit and
body/garment/export identities; actual owned reference captures.

## Scope and exact work

Prepare runtime-bound capture and visual tests, without changing model/rig/poses
or using V-series/third-party/generated reference images. Record reference source
candidate/asset/runtime hashes, review disposition, camera, scale, lighting,
pose/frame/time, renderer/version, colour management, crop and dimensions. A new
reference must not silently replace a pinned comparison or erase a regression.
Project-authored references may remain experimental while owner review is pending;
do not label them accepted. R2 remains the deformation baseline.

Inputs: actual bare/dressed runtime frames and owned reference inventory. Outputs:
per-view/per-frame silhouette/crop/visibility/contact/clearance findings, tested
coverage, mismatch categories, raw measurements and detector limits. Separate
capture mismatch from model regression. Do not compare unequal settings as matched
quantitative evidence. Colour/lighting changes must not conceal anatomy failures.

Use the existing review manifests/57-view plan for Blender visibility planning,
not as proof of runtime capture. Test neutral five views, listed anatomy close-ups
and exercise extrema plus continuous intermediate frames. Detect missing/cropped
hands/feet/equipment, lost floor/handle contact and garment/body defects where the
implemented detector can measure them. Missing or unsupported checks are UNKNOWN,
not PASS. Record tested and untested occluded regions; never claim all anatomy can
be judged from silhouettes or image similarity.

Replay captures independently under the same declared settings and verify identities
and reproducibility with declared tolerance. Confirm the tests actually catch
controlled defects using explicitly marked synthetic test fixtures or deliberately
altered owned copies. These are test inputs only, never review snapshots or approved
candidate imagery. Keep genuine model captures and detector fixtures separate.

## Renders, exit and rejection

Publish actual parent/new matched boards, runtime contact/clearance frames and QA
overlays linked to the unmodified source images. Record per-case failures rather
than a vague AI quality score. The current board tool proves source-image integrity
and capture matching; it does not implement these domain visual detectors.
Routine owner review is NON-BLOCKING: continue release-audit/promotion-packet
preparation while pending, but final visual OWNER ACCEPTED remains required.

Exit checks: `deterministic_capture`, `automatic_visual_checks`,
`pose_camera_region_coverage`, `first_party_reference_policy`,
`coverage_limits_recorded`, `candidate_runtime_binding`.
The Phase 11 exit packet requires exact target_runtime_commit. Commit capture
protocol, reference inventory/decisions, raw detector/replay/coverage reports,
actual image/overlay manifests and verified exit/shared state. Reject foreign/fake
references, silent reference replacement, capture/asset/commit drift, unsupported
checks labelled PASS or hidden per-case regressions. Preserve evidence and diagnose
the affected scope. Next: prepare Phase 12 final gate packet; no QA tool promotes.
