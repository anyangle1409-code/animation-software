# ORIGINAL v1 intermediate phase exit evidence

Phases 4–11 COMPLETE requires a candidate-bound exit packet with explicit checks
and exact source references. A plain PASS marker is insufficient. Phase 12 always
uses the separate production-promotion workflow. REVIEW SNAPSHOTS ARE NON-BLOCKING.

## Contract and commands

Create an INCOMPLETE template with:
`python scripts/verify_original_v1_phase_exit.py --phase <4–11> --template --json-out <fresh template.json>`.

Execute the roadmap/work-package tests, then create the actual exit report. Each
check has id, passed=true and a non-empty evidence list of repository path/SHA
references. Include schema_version=1, phase, candidate_sha256, status=PASS,
production_approved=false, actual command, exact source_git_commit and ISO
evidence_timestamp with timezone. owner_review is pending or explicitly accepted;
blocking=false. Phases 10/11 also require the exact target_runtime_commit.

Verify using `python scripts/verify_original_v1_phase_exit.py <packet.json> --phase <N> --json-out <fresh receipt.json>`.

Only verified actual reports belong in phase_completion_records. Source paths are
repository-local; hashes, check coverage/uniqueness, identity and dependencies are
checked. Templates never claim executed checks. The utility never mutates shared
state, assets or approval flags. Domain test results still need to be genuine:
contract validation does not infer anatomy quality or perform the runtime engine tests.

## Required checks by phase

| Phase | Explicit exit checks |
|---|---|
| 4 | `development_zero_failures`, `no_unresolved_regressions`, `replay_matches_primary`, `frozen_rig_baseline_gates`, `source_lineage_verified`, `published_review_snapshot`, `freeze_record_pinned` |
| 5 | `anatomy_5A_torso`, `anatomy_5B_shoulders`, `anatomy_5C_arms`, `anatomy_5D_hands`, `anatomy_5E_pelvis_legs`, `anatomy_5F_feet`, `anatomy_5G_head_neck`, `mesh_weight_audits`, `deformation_regression_checks`, `published_review_snapshots` |
| 6 | `manifold_surface`, `normals`, `degenerate_faces`, `joint_support`, `symmetry`, `topology_weight_audit`, `deformation_regression_checks` |
| 7 | `original_garment_provenance`, `dressed_deformation`, `coverage_clearance`, `bare_dressed_equivalence`, `published_review_snapshot` |
| 8 | `owned_material_sources`, `stable_presentation_capture`, `readable_application_views`, `no_concealed_body_failures`, `published_review_snapshot` |
| 9 | `production_target_zero_failures`, `continuous_motion_ranges`, `bilateral_grip_floor_contact`, `intersection_classification`, `final_body_clothing_hashes` |
| 10 | `real_engine_exercises`, `smooth_human_motion`, `canonical_rig_binding`, `bare_dressed_equivalence`, `export_round_trip`, `standalone_runtime_audit` |
| 11 | `deterministic_capture`, `automatic_visual_checks`, `pose_camera_region_coverage`, `first_party_reference_policy`, `coverage_limits_recorded`, `candidate_runtime_binding` |

Phase 4 additionally remains blocked by any recomputed development failure or unresolved strict regression against the active immutable stress-pose epoch baseline. Use its work package for exact replay/snapshot/pinning
commands. Later phases require preceding completion records and their domain evidence.
Final owner visual acceptance remains mandatory for production promotion.

Phase 12 does not use an ordinary phase-exit packet. Use the technical promotion
workflow first, then the separate final-freeze contract in
`docs/work_packages/PHASE_12_PRODUCTION_FREEZE.md`. The final-freeze verifier
revalidates the exact Phase 4-11 exit-report bytes, requires Phase 9 to bind the
final model source commit and Phases 10/11 to bind the final runtime commit, and
requires an explicit owner production-freeze authorization. It never promotes.

## Candidate changes and historical reports

A phase-exit packet is permanently bound to the exact candidate that passed that
phase. Later candidates **do not relabel or rewrite** the packet. Instead, production
control may inherit an earlier phase checkpoint only when the current candidate's
exact `parent_sha256` chain reaches the checkpoint candidate. A divergent branch,
missing parent identity, changed checkpoint bytes or out-of-order phase checkpoint
is refused rather than guessed.

This means a verified Phase 4 development-freeze candidate can remain the immutable
foundation checkpoint while Phase 5 creates descendant anatomy candidates. The same
principle applies to later ordered phases: each phase checkpoint must be on the
current lineage and at the same or a newer descendant position than its predecessor.
Later phase/domain evidence is responsible for proving its scoped changes preserve
earlier requirements; a new deformation failure can still reopen Phase 3 even while
the historical Phase 4 checkpoint remains recorded.

Use `phase_completion_history` for superseded/rejected/divergent checkpoint
records or when deliberately replacing an active checkpoint with a newer verified
checkpoint. Never use history to make an unrelated candidate look like a descendant.
R2/P2B1/P3B1 and other epoch baselines remain separate immutable comparison inputs,
not phase-completion records.

Phase 6–11 domain execution packages are now prepared under docs/work_packages.
Read their shared execution contract and tooling-readiness table. The named check
contract is implemented; several domain measurements remain unimplemented. A
template or contract PASS cannot substitute for missing dressed, continuous-motion,
runtime, surface or visual evidence. Keep those checks INCOMPLETE until executed.
