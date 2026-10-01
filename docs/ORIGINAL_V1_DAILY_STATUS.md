# ORIGINAL v1 daily status (generated)

CURRENT PHASE
Phase 3 / 3E

CURRENT CANDIDATE
r36 — TRADE-OFF; EXPERIMENTAL. R2 stays pinned.
SHA-256: `6ae04e949fefdc3ec57e5a9a1c66e6d9aad3560075eda1cc0e43bcbf22e57f0d`

DEVELOPMENT BLOCKERS
2 failures; 5 separate strict severity regressions versus R2.

- lunge / pelvis / region_max_ratio: 7.237 (<= 5.0)
- lunge / torso / region_max_ratio: 6.371 (<= 5.0)

WHAT CHANGED
r36: solution geometry edit on HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r35.blend; candidate remains experimental.

WHAT PASSED
- 3A DEVELOPMENT CLEAR
- 3B DEVELOPMENT CLEAR
- 3C DEVELOPMENT CLEAR
- 3D DEVELOPMENT CLEAR
- curl_peak DEVELOPMENT CLEAR (severity comparisons remain separate)
- pushup_bottom DEVELOPMENT CLEAR (severity comparisons remain separate)

PENDING OWNER REVIEWS
- O2 neutral anatomy — pending, NON-BLOCKING.
- O4 deformation candidates — pending, NON-BLOCKING.
- Latest candidate snapshot remains pending; images must come from real renders.

NEXT EXACT TASK
RUN remaining diagnostics — isolate wrist/grip/lunge locally before editing
`RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat r36`

REVIEW SNAPSHOTS ARE NON-BLOCKING BY DEFAULT. Production approved: NO.

[✅] Phase 0 Provenance
[✅] Phase 1 Base body
[✅] Phase 2 Rig
[✅] Phase 3A Shoulders
[✅] Phase 3B Hands/fingers
[✅] Phase 3C Grip
[✅] Phase 3D Wrist
[🔴] Phase 3E Hip/lunge
[ ] Phase 4 Development freeze
[ ] Phase 5 High-detail anatomy
[ ] Phase 6 Final topology
[ ] Phase 7 Clothing
[ ] Phase 8 Materials
[ ] Phase 9 Production deformation
[ ] Phase 10 Runtime integration
[ ] Phase 11 Automatic QA
[ ] Phase 12 Production freeze

Evidence timestamp: 2026-10-01T20:49:04.332763+00:00
Evidence references (exact content hashes are in machine status):

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r36_merged_pose_report.json`
- `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r36.json`
- `ORIGINAL_V1_CANDIDATE_STATUS.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r36_evidence_manifest.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r36_comparison_vs_R2.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r36_comparison_vs_r28.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r36_comparison_vs_r29.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r36_comparison_vs_r30.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r36_comparison_vs_r32.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r36_comparison_vs_r35.json`

The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.
Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.
No model geometry, weights, rig, thresholds or baseline changes are made by this generator.
