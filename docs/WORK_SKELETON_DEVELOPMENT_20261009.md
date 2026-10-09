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
Evidence and six mutation/consistency tests: `hand_coordinate_integrity.py` and `test_hand_coordinate_integrity.py`.
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
