# ORIGINAL v1 daily status (generated)

CURRENT PHASE
Phase 3 / 4

CURRENT CANDIDATE
r95 — TRADE-OFF; EXPERIMENTAL. P3B1 stays pinned.
SHA-256: `8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd`

DEVELOPMENT BLOCKERS
0 failures; 1 separate strict severity regressions versus P3B1.


WHAT CHANGED
r95: solution corr_scapular_v1.npz on HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r93.blend; candidate remains experimental.

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
RUN local axilla repair — r95 reduces the lateral/back lobe (zone offset 7.95 -> 4.18 cm in press_top) with 0 development failures and the single unchanged strict P3B1 regression (pullup_top torso); the final Phase 3A assessment of that residual is presented for the owner decision
`RUN_ORIGINAL_V1_AXILLA_PIT_AUTO.bat r95`
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

Evidence timestamp: 2026-10-04T18:41:18.719101+00:00
Evidence references (exact content hashes are in machine status):

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r95_merged_pose_report.json`
- `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r95.json`
- `ORIGINAL_V1_CANDIDATE_STATUS.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r95_evidence_manifest.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r95_comparison_vs_P3B1.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r95_comparison_vs_r93.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r95/diagnostic_brief.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r95/edge_extremes.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r95/grip_penetration.json`

The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.
Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.
No model geometry, weights, rig, thresholds or baseline changes are made by this generator.
