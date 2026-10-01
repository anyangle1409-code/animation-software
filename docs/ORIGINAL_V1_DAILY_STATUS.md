# ORIGINAL v1 daily status (generated)

CURRENT PHASE
Phase 3 / 4

CURRENT CANDIDATE
r38 — TRADE-OFF; EXPERIMENTAL. R2 stays pinned.
SHA-256: `7369b2d886ddffe6d8f80911a14f0efc69d8b5daf741ba92014434433323819b`

DEVELOPMENT BLOCKERS
0 failures; 5 separate strict severity regressions versus R2.


WHAT CHANGED
r38: solution o37b.npz on HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r37.blend; candidate remains experimental.

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
- r38 visual snapshot — pending, NON-BLOCKING.
- Latest candidate snapshot remains pending; images must come from real renders.

NEXT EXACT TASK
RECONCILE freeze regressions — zero blockers is insufficient for strict freeze; inherited R2 regressions remain

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

Evidence timestamp: 2026-10-01T21:54:25.996131+00:00
Evidence references (exact content hashes are in machine status):

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r38_merged_pose_report.json`
- `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r38.json`
- `ORIGINAL_V1_CANDIDATE_STATUS.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r38_evidence_manifest.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r38_comparison_vs_R2.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r38_comparison_vs_r28.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r38_comparison_vs_r29.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r38_comparison_vs_r30.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r38_comparison_vs_r32.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r38_comparison_vs_r35.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r38_comparison_vs_r36.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r38_comparison_vs_r37.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r38/diagnostic_brief.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r38/edge_extremes.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r38/grip_penetration.json`
- `ORIGINAL_V1_WORK/candidates/review/visual_r38/visual_review_manifest.json`

The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.
Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.
No model geometry, weights, rig, thresholds or baseline changes are made by this generator.
