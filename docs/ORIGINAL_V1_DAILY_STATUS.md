# ORIGINAL v1 daily status (generated)

CURRENT PHASE
Phase 3 / 3C

CURRENT CANDIDATE
r35 — TRADE-OFF; EXPERIMENTAL. R2 stays pinned.
SHA-256: `741ff74f24ffdfbda952875ca6136e23abe05a68881b83dceeb42758ed1f31d8`

DEVELOPMENT BLOCKERS
6 failures; 5 separate strict severity regressions versus R2.

- lunge / pelvis / region_max_ratio: 7.237 (<= 5.0)
- lunge / torso / region_max_ratio: 6.371 (<= 5.0)
- curl_handle / grip_l / grip_max_penetration_mm: 5.93 (<= 2.0)
- curl_handle / grip_r / grip_max_penetration_mm: 5.93 (<= 2.0)
- pullup_bar / grip_l / grip_max_penetration_mm: 5.93 (<= 2.0)
- pullup_bar / grip_r / grip_max_penetration_mm: 5.93 (<= 2.0)

WHAT CHANGED
r35: solution o33.npz on HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r32.blend; candidate remains experimental.

WHAT PASSED
- 3A DEVELOPMENT CLEAR
- 3B DEVELOPMENT CLEAR
- 3D DEVELOPMENT CLEAR
- curl_peak DEVELOPMENT CLEAR (severity comparisons remain separate)
- pushup_bottom DEVELOPMENT CLEAR (severity comparisons remain separate)

PENDING OWNER REVIEWS
- O2 neutral anatomy — pending, NON-BLOCKING.
- O4 deformation candidates — pending, NON-BLOCKING.
- r35 visual snapshot — pending, NON-BLOCKING.
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

Evidence timestamp: 2026-10-01T18:44:26.103886+00:00
Evidence references (exact content hashes are in machine status):

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r35_merged_pose_report.json`
- `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r35.json`
- `ORIGINAL_V1_CANDIDATE_STATUS.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r35_evidence_manifest.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r35_comparison_vs_R2.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r35_comparison_vs_r28.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r35_comparison_vs_r29.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r35_comparison_vs_r30.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r35_comparison_vs_r32.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r35/diagnostic_brief.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r35/edge_extremes.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r35/grip_penetration.json`
- `ORIGINAL_V1_WORK/candidates/review/visual_r35/visual_review_manifest.json`

The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.
Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.
No model geometry, weights, rig, thresholds or baseline changes are made by this generator.
