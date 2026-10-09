# Autonomous skeleton development — 9 October 2026

## Scope and safety
Live anatomical baseline: `2d4b352c30ebc092eb167832d727a529cd18fef6`.
PR #8 reviewed head: `8b56e8768665cfa8b01b664fee00c32f353b7e79`.
All accepted/audit assets and the legacy builder remain unchanged. No c005.
PR #8 remains draft and unmerged because anatomical hand acceptance is open.

## Initial full discovery
Command: `python -m unittest discover -s scripts -p 'test_*.py'`.
989 tests, five failures and four errors, 143.540 seconds.
The following inherited checks fail before this session's changes:

- ERROR: test_live_plan_covers_support_and_selects_active_r96_recovery (test_original_v1_execution_orchestration.ExecutionOrchestrationTests.test_live_plan_covers_support_and_selects_active_r96_recovery)
- ERROR: test_operational_tool_artifacts_are_validated (test_original_v1_execution_orchestration.ExecutionOrchestrationTests.test_operational_tool_artifacts_are_validated)
- ERROR: test_future_candidate_with_verified_sources_is_selected (test_original_v1_production_control.ControlTests.test_future_candidate_with_verified_sources_is_selected)
- ERROR: test_owner_accepted_regression_is_bound_to_exact_candidate_and_values (test_original_v1_production_control.ControlTests.test_owner_accepted_regression_is_bound_to_exact_candidate_and_values)
- FAIL: test_unknown_support_stage_refused (test_original_v1_execution_orchestration.ExecutionOrchestrationTests.test_unknown_support_stage_refused)
- FAIL: test_next_action_requires_both_source_bound_diagnostics (test_original_v1_production_control.ControlTests.test_next_action_requires_both_source_bound_diagnostics)
- FAIL: test_wrist_repair_precedes_grip_and_lunge_after_hand_recovery (test_original_v1_production_control.ControlTests.test_wrist_repair_precedes_grip_and_lunge_after_hand_recovery)
- FAIL: test_zero_blockers_cannot_hide_inherited_regressions (test_original_v1_production_control.ControlTests.test_zero_blockers_cannot_hide_inherited_regressions)
- FAIL: test_current_candidate_status_matches_repository_evidence (test_verify_original_v1_candidate_status.CandidateStatusTests.test_current_candidate_status_matches_repository_evidence)

These failures concern older production recovery expectations. No acceptance criteria were weakened to make them pass.

## Hand finding
108 independently mapped input points; 98 exact legacy correspondences and ten unresolved distal tails.
Wrist relative geometry and numerical digit continuity are preserved, not anatomical acceptance.
Evidence and seven mutation/consistency tests: `hand_coordinate_integrity.py` and `test_hand_coordinate_integrity.py`.
A passing reconstruction is not permission to freeze hand coordinates or promote c004.


## Skeleton-first construction tooling
Separate branch: `codex/skeleton-first-construction-20261009`, based on remote hand-review commit `b0cb388d`.
Explicit coordinates are copied without the old mesh-fit builder or containment. a003/c004 replay preserves 206 bones and 427 markers exactly. Replaying legacy coordinates does not give them independent evidence.
Skin clearance receives immutable endpoint tuples; an outside-skin diagnostic cannot relocate a bone.
18 constructor tests and seven independent hand tests pass after review fixes. Strict construction remains blocked because anatomical contact/envelope coverage is incomplete. No source-ready full skeleton exists.
The evidence ledger requires 1,472 endpoint/axis/centre/frame claims (618 bone claims + 854 joint claims); this is a software contract requirement, not a claim of 1,472 anatomical defects. Legacy replay has none of these new receipts populated.

Independent review (separate reviewer): three report-integrity defects reproduced RED then fixed GREEN:
- Nonfinite joint frame rejected before output serialization; pre-serialize JSON before exclusive file creation.
- Joint attachment constraints reject endpoint bones outside the articulation's participants, resolving additional structures to their owner bones.
- Wrist-relative preservation assertion now rejects a moved radius/ulna endpoint rather than merely reporting its residual.
Failing logs and CP2 summaries retained in `audit/skeleton_first_construction_20261009`.

Ruling: use the constructor only as diagnostic construction/replay until independently sourced coordinates, contacts, proper anatomical axes and programme gates exist. This intentionally blocks strict mode rather than pretending incomplete evidence is sufficient.

## Movement evidence and fresh Blender verification
All 78 labelled test-amplitude peaks across 49 tests are retained in 12 families by `movement_evidence_queue.py`. Seven tests include unknown-family, untraced-peak, channel/direction and metre-to-millimetre mutations. Independent reviewer found silent omission of UNTRACED peaks and overly broad digit-prefix classification; both reproduced as two failures, corrected, and mutation checks pass. No original limit or source record changed.

Three primary research contexts are retained under `audit/work_evidence_queue_20261009/source_contexts.json`: radiographic fingertip allowance (index/ring only), healthy mixed-sex passive hip ETS observations, and male footballer side-lying hip abduction. These are not coordinate targets or physiological hard limits. Population, frame and protocol incompatibilities remain explicit blockers.

Fresh Blender was restored in this session using Python 3.13.16 and bpy 5.2.1; the initial Python 3.12 package lookup had no compatible distribution. Fresh empty-scene c004 replay saves/reloads 206 bones/427 markers and passes coordinate/reference-frame roundtrip. Endpoint error 5.872660896281533e-8 m, marker centre error 1.9924837642947718e-7 m. CP2 remains FAIL: 8 PASS / 1 FAIL / 1 UNVERIFIED / 1 INFO. Readiness remains 0 READY / 9 PARTIAL / 3 BLOCKED.

Fresh c004 movement: 135/135 integrity checks pass; 41 Blender mirror pairs pass; two side-specific-amplitude pairs remain solver-only. Independent solver agreement: AGREE on 9,575 frames, 13,509 composed deltas and 49,991 channels, zero series drift/evaluation/measurement failures, worst delta component 1.4471605316312974e-6. Raw samples/captures/input and both Blender files retained with SHA256 under `audit/runs/work_fresh_c004_rehearsal_20261009/`. a003/c004 older movement captures also independently rechecked with current code and agree.

The historical a003 construction capture fails current metadata comparison for 202 carrier-versus-reference labels, as already documented on 8 October. The corrected archived capture passes. Neither archive was changed and neither establishes new anatomy.

Full post-review discovery: 1,021 tests in 151.857 seconds, 1,012 pass, five failures/four errors; all nine names match the initial 989-test baseline exactly. Full trace and baseline comparison retained. Errors bind to old r96 recovery phase/freeze expectations; action assertions now encounter shoulder-foundation rejection, and the candidate status is anatomical-repair rejected. These are unresolved production-control/test-fixture compatibility issues; no acceptance rules were weakened.

GitHub PR #8 check `isolated-probe` passes at `b0cb388df495c45a08d143842a53b0a814e460c8`, run 37897061210. PR remains draft/unmerged. No a003/c001–c004, original evidence, legacy builder, mesh, weights or runtime asset changed. New diagnostic branches preserve the anatomical audit baseline.

Detailed acceptance/pickup procedure: `docs/WORK_SKELETON_PICKUP_20261009.md`. Stage 1 computational review and Stage 2 tooling are delivered; full anatomical stages remain incomplete. Gates 6/8/9 and canonical promotion remain blocked. Blender execution is no longer the immediate blocker; independently sourced geometry, contacts and visual anatomical review remain necessary.
