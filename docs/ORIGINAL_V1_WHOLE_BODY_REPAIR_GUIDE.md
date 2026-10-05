# ORIGINAL v1 whole-body repair guide

This is the practical execution guide for the whole-body human deformation requirement.

## Core rule

When a joint or segment moves, every anatomically connected skin/muscle/tendon chain that should respond must respond coherently. Tissue that should remain rooted must remain rooted.

Repair the **earliest failing layer**. Do not allow a later corrective to hide an upstream kinematic, skinning, weight-ownership or topology defect.

## Preferred operator path

Use the generated Stage-1 packets as the primary workflow. They resolve the active
wave, package set, exact candidate identity, required frozen poses, required
generic sweeps and stop conditions from the live machine authorities.

### Laptop pickup — before editing

Generate the exact packet:

`RUN_ORIGINAL_V1_STAGE1_LAPTOP_PICKUP_PLAN.bat <candidate.blend> <current-revision> <new-revision> <source-branch> <l|r|bilateral|midline> <fresh-label> <future-workspace-dir> <fresh-plan-dir> [wave-id]`

The generated run order performs or requests:

1. human-body contract gates;
2. current Stage-1 wave work package;
3. package-aware read-only pre-repair diagnostics;
4. one-time all-11 generic sweep calibration when still required;
5. exact pre-edit sweep baselines required by the selected packages;
6. a PRE-EDIT repair workspace with immutable declaration templates;
7. coupling-weight/diagnosis review;
8. the first legitimate model-edit boundary.

Do not edit before every blocking command/review gate in that packet is satisfied.

### Model edit

- repair only the earliest failing layer selected by
  `ORIGINAL_V1_DEFORMATION_DIAGNOSIS_TREE.json`;
- stay inside the immutable declaration's allowed vertices/bones/operations;
- repair weights/base support before corrective refinement;
- save as a **new** numbered candidate;
- never overwrite r95 or the direct parent.

### Laptop continuation — immediately after saving

Generate the exact post-edit packet:

`RUN_ORIGINAL_V1_STAGE1_POST_EDIT_CONTINUATION_PLAN.bat <workspace-dir> <final-candidate.blend> <revision> <prior-revision-or-dash> <fresh-label> <calibration-record-or-empty> <fresh-plan-dir>`

The packet then drives:

1. finalization of the PRE-EDIT workspace against the exact FINAL Blend SHA;
2. core post-repair validation;
3. every required final-candidate generic movement sweep;
4. required visual captures for every authoritative sample/camera;
5. raw contact/load measurements for contact-bearing sweeps;
6. collection of sweep evidence into the finalized repair workspace;
7. automatic creation of per-sweep motion-review records;
8. engineering review of motion, visuals, contact and human evidence;
9. `RUN_ORIGINAL_V1_VALIDATE_WORKSPACE_SWEEP_ACCEPTANCE.bat` to prove every required sweep acceptance record is engineering PASS and FINAL-SHA-bound;
10. completion of weights-only, coupling, movement-coupling, surface, execution, regression/contact/change and issue-closure evidence;
11. unified parent-to-candidate comparison.

Raw sweep execution, renders or contact measurements never grant acceptance by
themselves. Engineering sweep PASS requires the calibrated runner plus reviewed
motion continuity/reversibility, required visual evidence, contact evidence where
applicable and the declared real-human reference review.

### Lower-level utilities

`RUN_ORIGINAL_V1_CREATE_POST_EDIT_EVIDENCE_BUNDLE.bat` and the standalone sweep
review-workspace builder remain useful **lower-level** recovery/support utilities,
but they are not the preferred operator route when the PRE-EDIT repair workspace
exists.

The pre-edit declaration SHA and final post-edit candidate SHA are intentionally
different identities. Never rewrite a declaration after the edit to make them
match.

## Diagnosis order

1. Exact source/candidate reproduced?
2. Canonical joint/bone motion plausible?
3. Saved base skinning mode appropriate enough to continue, or does a controlled A/B need to be run?
4. Weights-only shared-tissue ownership plausible?
5. Existing topology capable of supporting the required fold/slide/compression?
6. Residual pose-space corrective genuinely needed?
7. Contact/load path coherent?
8. Dense motion continuous and return-reversible?
9. Whole-body regression clean?
10. Exact candidate visually human against permissible real-human surface observations?

The machine authority is `ORIGINAL_V1_DEFORMATION_DIAGNOSIS_TREE.json`.

## Repair packages

| Package | Tissue chain | Foundational proof |
|---|---|---|
| RP-NECK-TRAP-001 | cervical -> trapezius -> shoulder girdle | distributed neck/girdle surface, no collar/shelf/pinch |
| RP-PEC-AX-002 | chest/pec -> anterior axilla -> humerus | pec stays chest-rooted while insertion/fold follow arm |
| RP-POSTAX-003 | trunk/lat/teres -> posterior axilla -> humerus | trunk-rooted posterior mass with supported moving fold |
| RP-DELTOID-004 | clavicle/acromion/scapula -> deltoid -> humerus | yoke-like multi-anchor cap, not a rigid sphere |
| RP-ARM-005 | upper arm -> elbow -> forearm | contour/folds follow elbow and rotation without ring/corkscrew |
| RP-WRIST-HAND-006 | forearm -> wrist -> hand | continuous twist/load path, no wrist seam/collapse |
| RP-FINGER-007 | palm/flexor path -> thumb/fingers | non-uniform digit motion, tendon-guided surface and release |
| RP-TRUNK-008 | ribcage -> abdomen/lumbar -> pelvis | distributed trunk motion, reversible compression/stretch |
| RP-GLUTE-009 | pelvis/glute -> femur/lateral thigh | pelvic-rooted glute with continuous hip-driven reshape |
| RP-GROIN-010 | pelvis/adductor -> medial thigh | reversible groin compression/lengthening without tunnel |
| RP-QUAD-011 | pelvis/femur -> quadriceps -> patella/tibia | multi-joint rectus/quad extensor-chain continuity |
| RP-HAM-012 | pelvis -> hamstrings -> posterior knee/lower leg | combined hip+knee response and preserved popliteal space |
| RP-CALF-013 | femur/tibia -> calf -> Achilles -> heel | knee+ankle-dependent calf and continuous Achilles path |
| RP-FOOT-014 | ankle/hindfoot -> arch -> forefoot/toes | coupled loaded foot chain, not a rigid block |

Detailed machine-readable packages are in `ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json`.

## Pre-edit sequence for any package

1. Copy `ORIGINAL_V1_COUPLING_ZONE_DECLARATION_TEMPLATE.json` to a fresh candidate-specific record.
2. Bind exact source Blend SHA and candidate revision.
3. Record linked defect IDs and human evidence IDs.
4. Declare proximal anchor, bridge tissue, distal anchor, protected neighbours and allowed edit vertices.
5. Validate the declaration.
6. Run the coupling-weight ownership audit.
7. Capture weights-only before evidence.
8. Make the smallest repair at the earliest failing layer.
9. Re-run weights-only motion before fitting any corrective.

## Weights-only rule

Use `ORIGINAL_V1_WEIGHTS_ONLY_ACCEPTANCE_CONTRACT.json`.

No body region can move to corrective refinement until the weights-only surface has:

- continuous anatomical attachments;
- a plausible multi-anchor ownership gradient;
- believable volume redistribution;
- correct lengthening/compression direction;
- mechanically justified folds;
- continuous silhouette;
- no intermediate popping;
- clean return;
- bilateral consistency;
- coherent contact/load path where relevant.

## Automatic pose review

1. Run `RUN_ORIGINAL_V1_POSE_COUPLING_SCOPE.bat`.
2. Feed its JSON into `RUN_ORIGINAL_V1_POSE_EVIDENCE_PLAN.bat`.
3. The planner expands moved bones into every required coupling system, camera, landmark, human reference and open surface-evidence need.

Pose identity is only a validation fixture. It is never a deformation driver.

## Motion quality

For every repaired candidate run:

- shoulder-layer decomposition when shoulder systems are involved;
- dense motion continuity;
- outbound/return reversibility;
- existing whole-body numerical regression;
- contact/floor/equipment checks;
- required visual capture matrix.

## Candidate verdict

Populate a fresh copy of `ORIGINAL_V1_CANDIDATE_COMPARISON_MANIFEST_TEMPLATE.json` and run:

`RUN_ORIGINAL_V1_CANDIDATE_COMPARISON.bat <manifest.json> <fresh-report.json>`

The report checks:

- exact SHA consistency;
- scoped weights-only clearance;
- scoped coupling clearance;
- movement-coupling completeness;
- defect closure evidence;
- reversibility;
- explicit continuity review;
- regression/contact/visual/change-audit status;
- no new Critical/High blockers.

Engineering eligibility never implies owner acceptance or production promotion.

## Current execution priority

The first repair package set remains:

`RP-PEC-AX-002 -> RP-POSTAX-003 -> RP-DELTOID-004 -> RP-NECK-TRAP-001`

These are solved as a connected shoulder-yoke system, not four independent cosmetic patches.

After the shoulder foundation is proven, continue through the remaining packages in Stage 1 until the complete body has candidate-bound shared-tissue proof.
