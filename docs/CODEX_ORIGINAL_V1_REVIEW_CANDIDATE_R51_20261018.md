# R51 bounded outline-preserving native surface study

Status: UNSAVED_SHAPE_STUDY_NOT_ACCEPTED. Model saved: false. Owner visual review pending.

R47's actual overall outline was approved; its surfaces were rejected. R50 retained
an unsafe outline-preserving checkpoint but produced no native media. Therefore
R47 is the actual rendered comparison for R51. No private image or traced target
enters this build.

R51 replaces repeated full LP optimality solves with a first-party bounded
primal-dual search proposal. Exact hinge-branch presolve preserves the mathematical
objective; independent hard-row projection and original-row reconstruction verify
proposal bounds. Proposals are explicitly NOT certified optimal. The fitter then
requires a lower actual joint-pose repair merit, the actual outline within0.95mm,
and both unchanged45mm displacement caps. All exact final nonlinear and native
safety gates remain identical to R50/R49. No old test or numerical limit changed.
Internal unsafe search retention is not a passed final gate.

See docs/CODEX_ORIGINAL_V1_R51_BUILD_NOTE_20261018.md for failing probes, exact LP
capture, regression tests and the local three-step preflight. CI repeats the
three-step preflight before a bounded15minute main search. Full native checking,
13 benchmarks, all historical tests and actual matched images/video follow even
when the retained search state remains unsafe. There is no model-save step.

Native83-response checks passed: False; new contact records: 42.
Back motion excess: 2.074110mm against unchanged0.5mm.
Posterior crease excess: 173.859020degrees against unchanged2degrees.
13 benchmarks passed: False; regression records: 6.
Actual marked-outline error against approved R47: 0.949999016269798mm; unchanged guard1mm.
Marked-pose reversed normals: 6.
Test exit codes (zero passes): {"preflight_back_surface_test_exit.txt": 1, "preflight_marked_surface_test_exit.txt": 1, "preflight_motion_test_exit.txt": 1, "preflight_outline_test_exit.txt": 0, "preflight_scope_test_exit.txt": 0, "r37_contour_test_exit.txt": 0, "r38_marks_test_exit.txt": 1, "r41_front_test_exit.txt": 1, "r41_line_test_exit.txt": 1, "r42_profile_test_exit.txt": 1, "r43_back_surface_test_exit.txt": 1, "r43_motion_test_exit.txt": 1, "r47_scope_test_exit.txt": 0, "r48_approved_outline_test_exit.txt": 0, "r48_marked_surface_test_exit.txt": 1, "r48_outline_derivative_test_exit.txt": 0, "r48_preparation_test_exit.txt": 0, "r51_bounded_proposal_test_exit.txt": 0, "r51_lp_test_exit.txt": 0, "r51_preflight_test_exit.txt": 0, "r51_preparation_test_exit.txt": 0, "r51_retention_test_exit.txt": 0, "r51_safety_policy_test_exit.txt": 0}.
Search exit and retained checkpoint: {"approved": false, "fit_completed": false, "fit_exit_code": 1, "fit_timed_out": false, "has_retained_search_state": true, "model_saved": false, "native_validation": "FAILED", "retained_state_safety": "NATIVE_CHECKS_FAILED_UNACCEPTED", "shape_repair_complete": false, "state_source": "main_repair_search_progress", "status": "PARTIAL_SEARCH_NATIVE_VALIDATION_PENDING"}.
Protected identity: {"basis": true, "bones": true, "groups": true, "non_s7": true, "weights": true}.

Historical outward-fill/line tests and full R47 scope tests remain unchanged and
all failures remain recorded. A successful evidence workflow or numerical pass
is not owner visual approval, anatomical correctness or a completed shape repair.
Frozen skeleton, Basis, weights, topology, HGPT_SHOULDER/non-S7 keys, lockout,
anchors and protected elbow/distal arm remain protected.

Review actual R47_R51_full_outline.jpg, R47_R51_marked_l/r.jpg,
R47_R51_press_comparison.mp4 and shoulder_press_r51.mp4. The fitting history,
non-optimal proposal reports, timeout/exit details and native failures are retained.
