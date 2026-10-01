# ORIGINAL v1 daily status (generated)

CURRENT PHASE
Phase 3 / 3B — core deformation

CURRENT CANDIDATE
r29 — TRADE-OFF; EXPERIMENTAL. R2 stays pinned.
SHA-256: `d9b24e75fa6f2eb4c8999787fd925d5986f236691e00c9d251be3f0f061d7574`

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
r29: O4 candidate shoulder weight optimisation (not production)

WHAT PASSED
- 3A DEVELOPMENT CLEAR

PENDING OWNER REVIEWS
- O2 neutral anatomy — pending, NON-BLOCKING.
- O4 deformation candidates — pending, NON-BLOCKING.
- Latest candidate snapshot remains pending; images must come from real renders.

NEXT EXACT TASK
RUN r30 — authorised finger-minimum recovery, preserving curl_peak clearance
`RUN_ORIGINAL_V1_R30.bat`

REVIEW SNAPSHOTS ARE NON-BLOCKING BY DEFAULT. Production approved: NO.

[✅] Phase 0 Provenance
[✅] Phase 1 Base body
[✅] Phase 2 Rig
[✅] Phase 3A Shoulders
[🟠] Phase 3B Hands/fingers
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

Evidence timestamp: 2026-09-30T23:03:40.828334+00:00
Evidence references (exact content hashes are in machine status):

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_merged_pose_report.json`
- `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.json`
- `ORIGINAL_V1_CANDIDATE_STATUS.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_comparison_vs_R2.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_comparison_vs_r28.json`

The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.
Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.
No model geometry, weights, rig, thresholds or baseline changes are made by this generator.
