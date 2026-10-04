# ORIGINAL v1 daily status (generated)

CURRENT PHASE
Phase 3 / 4

CURRENT CANDIDATE
r90 — STRICT IMPROVEMENT; EXPERIMENTAL. P3B1 stays pinned.
SHA-256: `5c408a6d28f23e75ebf024cc9def753c9556f6cf3b7b99b82c9092dee20f4c8f`

DEVELOPMENT BLOCKERS
0 failures; 3 separate strict severity regressions versus P3B1.


WHAT CHANGED
r90: solution corr_flex_v2.npz on HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r83.blend; candidate remains experimental.

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
RUN local axilla repair — r90 is development-clear (0 failures) with 3 strict P3B1 regressions (r87 4): press_top arm and pullup_top torso minimum edge ratios sit on a measured trade-off frontier against the pull-up arm minimum (r88), and the push-up self-intersection item is a 3D wrist-band side effect; next is an owner decision on these three or a declared 3D wrist-weight experiment
`RUN_ORIGINAL_V1_AXILLA_PIT_AUTO.bat r90`
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

Evidence timestamp: 2026-10-04T13:42:17.489079+00:00
Evidence references (exact content hashes are in machine status):

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r90_merged_pose_report.json`
- `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r90.json`
- `ORIGINAL_V1_CANDIDATE_STATUS.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r90_evidence_manifest.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r90_comparison_vs_P3B1.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r90_comparison_vs_r87.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r90/diagnostic_brief.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r90/edge_extremes.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r90/grip_penetration.json`

The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.
Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.
No model geometry, weights, rig, thresholds or baseline changes are made by this generator.
