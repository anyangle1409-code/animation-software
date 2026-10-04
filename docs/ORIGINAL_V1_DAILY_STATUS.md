# ORIGINAL v1 daily status (generated)

CURRENT PHASE
Phase 3 / 4

CURRENT CANDIDATE
r93 — TRADE-OFF; EXPERIMENTAL. P3B1 stays pinned.
SHA-256: `6dfcd85a65e77fd832c9eb91cbe7eda04c81dc635201d260d6cbcf0eee508984`

DEVELOPMENT BLOCKERS
0 failures; 1 separate strict severity regressions versus P3B1.


WHAT CHANGED
r93: solution r93_flex.npz on r93_abd.blend; candidate remains experimental.

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
RUN local axilla repair — r93 removes the shoulder-top knobs/web contribution of the corrective (0 development failures, 1 strict P3B1 regression: pullup_top torso); the lateral/back wing flaps (scapula weights) are still visible and are the next declared investigation
`RUN_ORIGINAL_V1_AXILLA_PIT_AUTO.bat r93`
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

Evidence timestamp: 2026-10-04T16:31:32.044508+00:00
Evidence references (exact content hashes are in machine status):

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r93_merged_pose_report.json`
- `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r93.json`
- `ORIGINAL_V1_CANDIDATE_STATUS.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r93_evidence_manifest.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r93_comparison_vs_P3B1.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r93_comparison_vs_r92.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r93/diagnostic_brief.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r93/edge_extremes.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r93/grip_penetration.json`

The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.
Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.
No model geometry, weights, rig, thresholds or baseline changes are made by this generator.
