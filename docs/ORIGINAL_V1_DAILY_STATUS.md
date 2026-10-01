# ORIGINAL v1 daily status (generated)

CURRENT PHASE
Phase 3 / 3C

CURRENT CANDIDATE
r32 — TRADE-OFF; EXPERIMENTAL. R2 stays pinned.
SHA-256: `56205ee89a4bd5f8d5999ce64cf97f3b09a14876465af2c8fe7f382abf989295`

DEVELOPMENT BLOCKERS
7 failures; 5 separate strict severity regressions versus R2.

- lunge / pelvis / region_max_ratio: 7.559 (<= 5.0)
- lunge / torso / region_min_ratio: 0.12 (>= 0.15)
- lunge / torso / region_max_ratio: 7.2 (<= 5.0)
- curl_handle / grip_l / grip_max_penetration_mm: 5.93 (<= 2.0)
- curl_handle / grip_r / grip_max_penetration_mm: 5.93 (<= 2.0)
- pullup_bar / grip_l / grip_max_penetration_mm: 5.93 (<= 2.0)
- pullup_bar / grip_r / grip_max_penetration_mm: 5.93 (<= 2.0)

WHAT CHANGED
r32: solution o26.npz on HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.blend; candidate remains experimental.

WHAT PASSED
- 3A DEVELOPMENT CLEAR
- 3B DEVELOPMENT CLEAR
- 3D DEVELOPMENT CLEAR
- curl_peak DEVELOPMENT CLEAR (severity comparisons remain separate)
- pushup_bottom DEVELOPMENT CLEAR (severity comparisons remain separate)

PENDING OWNER REVIEWS
- O2 neutral anatomy — pending, NON-BLOCKING.
- O4 deformation candidates — pending, NON-BLOCKING.
- r32 visual snapshot — pending, NON-BLOCKING.
- Latest candidate snapshot remains pending; images must come from real renders.

NEXT EXACT TASK
REPAIR grip/thumb — Bilateral equipment penetration must satisfy unchanged gates.
Read `docs/work_packages/PHASE_3C_GRIP_THUMB.md`.

REVIEW SNAPSHOTS ARE NON-BLOCKING BY DEFAULT. Production approved: NO.

[✅] Phase 0 Provenance
[✅] Phase 1 Base body
[✅] Phase 2 Rig
[✅] Phase 3A Shoulders
[✅] Phase 3B Hands/fingers
[🟠] Phase 3C Grip
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

Evidence timestamp: 2026-10-01T17:52:25.369854+00:00
Evidence references (exact content hashes are in machine status):

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r32_merged_pose_report.json`
- `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r32.json`
- `ORIGINAL_V1_CANDIDATE_STATUS.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r32_evidence_manifest.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r32_comparison_vs_R2.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r32_comparison_vs_r28.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r32_comparison_vs_r29.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r32_comparison_vs_r30.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r32/diagnostic_brief.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r32/edge_extremes.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r32/grip_penetration.json`
- `ORIGINAL_V1_WORK/candidates/review/visual_r32/visual_review_manifest.json`

The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.
Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.
No model geometry, weights, rig, thresholds or baseline changes are made by this generator.
