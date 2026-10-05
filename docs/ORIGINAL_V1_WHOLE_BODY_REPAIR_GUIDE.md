# ORIGINAL v1 whole-body repair guide

This is the practical execution guide for the whole-body human deformation requirement.

## Core rule

When a joint or segment moves, every anatomically connected skin/muscle/tendon chain that should respond must respond coherently. Tissue that should remain rooted must remain rooted.

Repair the **earliest failing layer**. Do not allow a later corrective to hide an upstream kinematic, skinning, weight-ownership or topology defect.

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
