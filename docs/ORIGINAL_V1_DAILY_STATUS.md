# ORIGINAL v1 daily status (generated)

CURRENT PHASE
Phase 3 / 4

CURRENT CANDIDATE
r81 — TRADE-OFF; EXPERIMENTAL. P3B1 stays pinned.
SHA-256: `fa95c0b4f6f4815202936639aa173f61fdc0db43837f8f0c40a7af95d74d2b0a`

DEVELOPMENT BLOCKERS
0 failures; 12 separate strict severity regressions versus P3B1.


WHAT CHANGED
r81: solution corr_v20.npz on r81_weights_intermediate.blend; candidate remains experimental.

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
RUN local axilla repair — r81 is development-clear and has removed every shoulder self-intersection regression versus P3B1 (press_top 16, rhythm 12, pull-ups 0), leaving 12 strict regressions that are compression-type minimum-edge-ratio drops in the arm/torso/shoulder regions plus squat volume/p01 and push-up self-intersections, all inside the gates; next is a declared iteration aimed at that compression family (for example more smoothing iterations or a relaxed corrective compression floor), or an owner disposition of the remaining 12
`RUN_ORIGINAL_V1_AXILLA_PIT_AUTO.bat r81`
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

Evidence timestamp: 2026-10-03T23:57:31.785643+00:00
Evidence references (exact content hashes are in machine status):

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r81_merged_pose_report.json`
- `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r81.json`
- `ORIGINAL_V1_CANDIDATE_STATUS.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r81_evidence_manifest.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r81_comparison_vs_P3B1.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r81_comparison_vs_r80.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r81/diagnostic_brief.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r81/edge_extremes.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r81/grip_penetration.json`

The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.
Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.
No model geometry, weights, rig, thresholds or baseline changes are made by this generator.
