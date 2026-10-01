# ORIGINAL v1 daily status (generated)

CURRENT PHASE
Phase 3 / 3D

CURRENT CANDIDATE
r30 — TRADE-OFF; EXPERIMENTAL. R2 stays pinned.
SHA-256: `c842992f435ab43bc846782add8989afab3d7f03b59bc199615f9827c9444347`

DEVELOPMENT BLOCKERS
7 failures; 6 separate strict severity regressions versus R2.

- lunge / pelvis / region_max_ratio: 7.559 (<= 5.0)
- lunge / torso / region_min_ratio: 0.12 (>= 0.15)
- lunge / torso / region_max_ratio: 7.2 (<= 5.0)
- curl_handle / grip_l / grip_max_penetration_mm: 5.93 (<= 2.0)
- curl_handle / grip_r / grip_max_penetration_mm: 5.93 (<= 2.0)
- pullup_bar / grip_l / grip_max_penetration_mm: 5.93 (<= 2.0)
- pullup_bar / grip_r / grip_max_penetration_mm: 5.93 (<= 2.0)

WHAT CHANGED
r30: solution o22.npz on HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.blend; candidate remains experimental.

WHAT PASSED
- 3A DEVELOPMENT CLEAR
- 3B DEVELOPMENT CLEAR
- curl_peak DEVELOPMENT CLEAR (severity comparisons remain separate)
- pushup_bottom DEVELOPMENT CLEAR (severity comparisons remain separate)

PENDING OWNER REVIEWS
- O2 neutral anatomy — pending, NON-BLOCKING.
- O4 deformation candidates — pending, NON-BLOCKING.
- r30 visual snapshot — pending, NON-BLOCKING.
- Latest candidate snapshot remains pending; images must come from real renders.

NEXT EXACT TASK
RUN remaining diagnostics — isolate wrist/grip/lunge locally before editing
`RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat r30`

REVIEW SNAPSHOTS ARE NON-BLOCKING BY DEFAULT. Production approved: NO.

[✅] Phase 0 Provenance
[✅] Phase 1 Base body
[✅] Phase 2 Rig
[✅] Phase 3A Shoulders
[✅] Phase 3B Hands/fingers
[🟠] Phase 3C Grip
[🟡] Phase 3D Wrist
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

Evidence timestamp: 2026-10-01T17:07:09.695473+00:00
Evidence references (exact content hashes are in machine status):

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r30_merged_pose_report.json`
- `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.json`
- `ORIGINAL_V1_CANDIDATE_STATUS.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r30_evidence_manifest.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r30_comparison_vs_R2.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r30_comparison_vs_r28.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r30_comparison_vs_r29.json`
- `ORIGINAL_V1_WORK/candidates/review/visual_r30/visual_review_manifest.json`

The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.
Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.
No model geometry, weights, rig, thresholds or baseline changes are made by this generator.
