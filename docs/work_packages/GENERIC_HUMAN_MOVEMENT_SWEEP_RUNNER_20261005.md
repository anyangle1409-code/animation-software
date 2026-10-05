# Generic human movement sweep runner — implementation work package

**Date:** 2026-10-05  
**Asset:** HomeGymPT_Male_ORIGINAL_v1  
**Master stage:** 1 — Human movement foundation  
**Production approved:** NO

## Purpose

Implement one separate, read-only Blender validation runner for the deterministic
human-movement sweeps in:

- ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json
- ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_STATUS.json

The runner exists to prove connected human motion that is not adequately sampled
by the frozen P3a stress-pose fixtures.

Do **not** modify, repin or repurpose
scripts/pose_test_original_v1_o4_candidate_blender.py to manufacture this coverage.

Target implementation:

- scripts/run_original_v1_human_movement_sweep_blender.py
- RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP.bat

## Current Stage-1 priority

The active shoulder-yoke wave requires these sweep-only movements:

1. shoulder_abduction_elevation
2. humeral_internal_external_rotation
3. trunk_flexion
4. trunk_extension
5. trunk_lateral_bend
6. trunk_axial_rotation

After that, the remaining direct-sweep definitions are:

7. forearm_pronation_supination
8. grip_release
9. loaded_hip_hinge
10. hip_abduction_adduction
11. ankle_plantarflexion

The order above is implementation priority only. It does not alter Stage-1 repair
dependencies.

## Non-negotiable architecture

The runner must be **movement/joint-state driven**, never exercise-name driven.

For each sweep:

1. load the exact candidate Blend read-only;
2. hash the candidate before any pose operation;
3. load the authoritative sweep row and hash the sweep-plan file;
4. resolve a movement adapter by sweep ID;
5. reset to the exact canonical rest/neutral state;
6. apply deterministic joint-state inputs for each named sample;
7. record the joint/bone transform state used for that sample;
8. update twist/helper/corrective evaluation only through existing generic rig
   semantics;
9. capture whole-body and required regional evidence;
10. record numerical/contact state where applicable;
11. run every intermediate and return sample;
12. verify the source Blend SHA is unchanged on exit.

No source Blend may be saved.

## Two-layer proof for every movement adapter

### A. Skeleton / kinematic proof

Before surface evidence is trusted, each adapter must prove:

- the intended production bones moved;
- unintended upstream/downstream bones did not move materially without anatomical
  justification;
- joint direction and range are anatomically plausible;
- left/right mirrored inputs are equivalent where appropriate;
- multi-joint coordination is distributed where the evidence requires it;
- outbound and return joint states are deterministic;
- contact definitions are coherent where applicable.

The adapter's exact joint-state definition must be recorded in the evidence
manifest. Do not infer motion from a render alone.

### B. Surface / connected-tissue proof

Only after skeleton proof is clear, review:

- every coupling system triggered by the moved bones;
- attachment continuity;
- shared ownership gradient;
- lengthening/compression direction;
- volume redistribution;
- fold/crease appearance and release;
- whole-body silhouette;
- dense intermediate continuity;
- return reversibility;
- bilateral consistency;
- contact/load propagation where applicable;
- human exterior surface evidence IDs from the sweep plan.

A numerical pass does not overrule an obvious Critical/High human-looking defect.

## Adapter range rule

Do not invent a single "ideal human" ROM merely to make a convenient test.

Use the existing human-evidence manifest and canonical rig/joint-limit authorities
to choose a conservative audit domain. Where the evidence establishes
coordination but not a universal angle, record the chosen project audit range as
a deterministic validation range, not as a claim of universal human ROM.

The current evidence explicitly supports:

- distributed scapular/back/axillary response through arm elevation;
- shoulder axial rotation surface change with the arm abducted;
- distributed lumbopelvic contribution in flexion/extension/lateral bend/rotation;
- non-rigid forearm surface response during pronation/supination.

Do not transfer scans, images, marker coordinates or third-party geometry into
the production character.

## Required per-run outputs

Every sweep run must create a fresh output directory containing at least:

- sweep_execution_manifest.json
- sample_joint_states.json
- sample_capture_manifest.json
- motion_continuity.json
- motion_reversibility.json
- contact_state.json when applicable
- whole-body captures for every required sample
- required regional close captures
- numerical deformation summary where the existing project metrics apply

The execution manifest must contain:

- candidate filename and SHA-256;
- candidate revision;
- source branch when available;
- sweep ID;
- sweep-plan SHA-256;
- runner-script SHA-256;
- Blender version;
- exact sample order;
- exact adapter ID/revision;
- joint-state hash per sample;
- capture hashes;
- source_saved_or_modified = false;
- engineering_review = PENDING;
- owner_review = PENDING;
- production_approved = false.

## Fail-closed rules

Stop the sweep and preserve evidence if:

- candidate identity changes;
- a required bone is missing;
- a required sample cannot be constructed;
- a declared contact state cannot be represented;
- NaN/non-finite transforms appear;
- left/right mirroring produces an unexplained material difference;
- the source Blend would need to be saved;
- the runner would need to weaken a pose/regression/contact threshold;
- a movement can only be made to look plausible by exercise-specific deformation
  logic.

## Integration with Stage 1

The package validation selector already tells each repair package which movements
need the separate runner:

- scripts/build_original_v1_package_validation_selection.py

The wave work-package generator propagates the same requirement:

- scripts/build_original_v1_stage1_wave_work_package.py

After implementation, update
ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_STATUS.json:

- runner_binding_status -> BOUND
- blender_adapter_id -> stable adapter ID

Then run:

python scripts/validate_original_v1_human_movement_sweep_execution.py --require-bound

This validator becoming fully bound does **not** mean the body is accepted. It
only proves the 11 sweep definitions have an execution path. Each candidate must
still run the sweeps and produce candidate-bound evidence.

## Acceptance for the runner itself

The generic runner is ready for use only when:

- all 11 sweep definitions are bound;
- frozen P3a pose-definition content is unchanged;
- each adapter has a skeletal-only test/review output;
- each adapter records outbound/intermediate/return joint states;
- candidate/sweep/runner hashes are present;
- source-save protection is proven;
- repeat runs on the same candidate produce identical joint-state manifests;
- no adapter uses exercise identity as deformation logic;
- the contract validator passes with --require-bound.

Until then the generic sweep runner remains a tooling blocker for complete
Stage-1 movement proof, not a reason to weaken the human-body acceptance rules.
