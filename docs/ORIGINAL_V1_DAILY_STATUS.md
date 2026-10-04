# ORIGINAL v1 daily status (generated)

CURRENT PHASE
Phase 3 / 4

CURRENT CANDIDATE
r87 — TRADE-OFF; EXPERIMENTAL. P3B1 stays pinned.
SHA-256: `019891ddcc7d9d49486a2f89917d09129a43e53bb0b45402b7f8e685ee6e84cc`

DEVELOPMENT BLOCKERS
0 failures; 4 separate strict severity regressions versus P3B1.


WHAT CHANGED
r87: solution corr_flex_v1.npz on HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r83.blend; candidate remains experimental.

WHAT PASSED
- 3A DEVELOPMENT CLEAR
- 3B DEVELOPMENT CLEAR
- 3C DEVELOPMENT CLEAR
- 3D DEVELOPMENT CLEAR
- 3E DEVELOPMENT CLEAR
- curl_peak DEVELOPMENT CLEAR (severity comparisons remain separate)
- pushup_bottom DEVELOPMENT CLEAR (severity comparisons remain separate)

PENDING OWNER REVIEWS
- O2 neutral anatomy — pending, NON-BLOCKING.
- O4 deformation candidates — pending, NON-BLOCKING.
- Latest candidate snapshot remains pending; images must come from real renders.

NEXT EXACT TASK
RUN local axilla repair — r87 is development-clear (0 failures) with 4 strict P3B1 regressions (down from r83's 7); the squat arm, squat shoulder and squat p01 regressions are cleared by the forward-flexion corrective; the remaining four (press_top arm and pullup_top torso minimum edge ratios, squat volume deviation, push-up self-intersections) are not addressed by a flexion-gated key: next is an owner decision on them
`RUN_ORIGINAL_V1_AXILLA_PIT_AUTO.bat r87`
Read `docs/work_packages/PHASE_3A_AXILLA_PIT_LOCAL_REPAIR.md`.

REVIEW SNAPSHOTS ARE NON-BLOCKING BY DEFAULT. Production approved: NO.

[✅] Phase 0 Provenance
[✅] Phase 1 Base body
[✅] Phase 2 Rig
[✅] Phase 3A Shoulders
[✅] Phase 3B Hands/fingers
[✅] Phase 3C Grip
[✅] Phase 3D Wrist
[✅] Phase 3E Hip/lunge
[ ] Phase 4 Development freeze
[ ] Phase 5 High-detail anatomy
[ ] Phase 6 Final topology
[ ] Phase 7 Clothing
[ ] Phase 8 Materials
[ ] Phase 9 Production deformation
[ ] Phase 10 Runtime integration
[ ] Phase 11 Automatic QA
[ ] Phase 12 Production freeze

Evidence timestamp: 2026-10-04T12:54:11.077521+00:00
Evidence references (exact content hashes are in machine status):

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r87_merged_pose_report.json`
- `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r87.json`
- `ORIGINAL_V1_CANDIDATE_STATUS.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r87_evidence_manifest.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r87_comparison_vs_P3B1.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r87_comparison_vs_r83.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r87/diagnostic_brief.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r87/edge_extremes.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r87/grip_penetration.json`

The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.
Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.
No model geometry, weights, rig, thresholds or baseline changes are made by this generator.
