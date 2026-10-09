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
