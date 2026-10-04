# ORIGINAL v1 whole-body deformation recovery — 2026-10-04

## Authority and status

The owner has rejected the visible chest, axilla, shoulder and grip quality shown by the r95 milestone evidence and has directed continued model work using real-human evidence.

This decision supersedes the practical use of the r95 Phase 4 development freeze as a model-quality sign-off. Historical Phase 4 records remain immutable evidence of what was previously measured; they are not production approval and must not be deleted or rewritten. The current branch reopens anatomical and deformation validation from the exact r95 candidate.

- Recovery branch: `codex/whole-body-deformation-recovery-20261004`
- Parent branch: `claude/original-v1-blender-o2-20260929`
- Parent HEAD: `540edd4ca97927e04c2966a27f70148678c29464`
- Exact r95 Blend SHA-256: `8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd`
- Exact r93 Blend SHA-256: `6dfcd85a65e77fd832c9eb91cbe7eda04c81dc635201d260d6cbcf0eee508984`
- Production approval: `false`

The exact r90-r95 Blend sources were recovered from the previous worker's temporary checkout and copied into the ignored local candidate workspace. Their hashes match the committed candidate manifests.

## Owner requirement

The target is not a small set of exercise-specific corrections. The model must behave as a plausible human across the natural movement envelope. Skeleton motion, coupled joint motion, surface anatomy, skin folds, soft-tissue compression, volume changes, contact, load response and transitions must be validated together.

Real-human photographs and videos from multiple people, builds, angles and motion phases are mandatory development evidence. Published anatomical and biomechanical evidence must support the movement rules. Reference material is development-only and must not become a runtime or shipped-asset dependency.

Numerical gates support the anatomical review; they never overrule an obviously incorrect visual result.

## Evidence-backed shoulder model requirements

Direct-bone three-dimensional measurements show that overhead elevation combines glenohumeral motion with clavicular elevation/retraction/posterior rotation and scapular upward rotation/posterior tilt. A single fixed shoulder ratio is not an adequate full-range model, and normal rhythm varies through the elevation arc.

Primary references:

- Ludewig et al., *Motion of the Shoulder Complex During Multiplanar Humeral Elevation*: https://pmc.ncbi.nlm.nih.gov/articles/PMC2657311/
- Matsuki et al., *In Vivo Assessment of Scapulohumeral Rhythm During Unconstrained Overhead Reaching*: https://pmc.ncbi.nlm.nih.gov/articles/PMC2841046/
- Axillary anatomy review: https://pmc.ncbi.nlm.nih.gov/articles/PMC10175532/

The axillary surface must preserve the anatomical relationship between the anterior fold (pectoralis major), posterior fold (latissimus dorsi/teres major), medial thoracic wall/serratus region and lateral upper-arm boundary. A long planar membrane, knife-edge trench or detached pec/arm transition is a failure.

## Initial visual defect ledger

| ID | Region | Evidence | Defect | Severity | State |
|---|---|---|---|---|---|
| WB-AX-001 | bilateral axilla | r95 overhead press | long membrane-like axillary wall and deep trench | Critical | Open |
| WB-PEC-002 | lateral pec | r95 overhead press | excessive tissue transport with humerus | Critical | Open |
| WB-PEC-003 | chest volume | r95 overhead press | lateral collapse with central pec ballooning | Critical | Open |
| WB-AX-004 | posterior axillary fold | r95 overhead press/rear shoulder | inadequate lat/teres support | High | Open |
| WB-SHO-005 | deltoid | r95 neutral shoulder close-ups | oversized spherical cap and poor regional definition | High | Open |
| WB-SHO-006 | shoulder/arm junction | r95 neutral shoulder close-ups | abrupt narrowing, pinch and discontinuity | High | Open |
| WB-CLV-007 | clavicle/scapula/trapezius | neutral and overhead views | inadequate surface and motion coupling | High | Open |
| WB-SYM-008 | bilateral shoulder complex | r95 overhead press | inconsistent left/right deformation | High | Open |
| WB-GRP-009 | fingers/thumb | grip/curl view | uniform finger curl, weak thumb opposition and implausible handle conformance | High | Open |
| WB-WRI-010 | wrist/load path | grip/curl view | unstable wrist/handle alignment | High | Open |
| WB-QA-011 | validation process | r95 Phase 4 record and milestone set | numerical/freeze completion despite unresolved visible anatomy | Critical | Open |

The two uploaded neutral shoulder images are byte-identical to the committed r95 milestone images. The supplied grip and overhead images are crops/zooms and are retained as owner review evidence outside the repository; the corresponding full milestone renders remain committed in `ORIGINAL_V1_WORK/candidates/review/milestone_r95/`.

## Recovery sequence

1. Reproduce r95 through the exact P3a production deformation path with all six shoulder corrective keys driven.
2. Add a fail-closed visual rejection record without rewriting the historical Phase 4 packet.
3. Build a real-human reference inventory for whole-body movement primitives and the high-risk surface regions.
4. Expand the pose matrix to include elevation increments, flexion, abduction, rotation, loaded/unloaded motion and transitional frames.
5. Instrument the shoulder/axilla chain to separate skeleton motion, weights and each corrective contribution.
6. Identify the first causal boundary that creates the axillary membrane/pec transport defect.
7. Declare the smallest auditable correction scope before editing the model.
8. Create a new candidate; never overwrite r95.
9. Run full numerical, visual, symmetry, collision, contact, arc-continuity and whole-body regression evidence.
10. Repeat region by region until no Critical or High whole-body anatomical defects remain.

## Acceptance gate

No development freeze or later phase may be treated as anatomically accepted until:

- every movement primitive has real-human reference evidence;
- start, intermediate, end and reversal frames have been inspected;
- no Critical or High item remains open;
- visual and numerical gates both pass;
- the production deformation path is used for every validation render;
- fixes preserve already accepted movement, contact and symmetry behaviour;
- evidence, issue status, model hashes and restart instructions are committed and pushed.

## Immediate restart point

Open the exact r95 candidate in Blender 5.2 and reproduce the committed overhead press, neutral shoulder and grip views. Confirm the six corrective keys and P3a driver values in each pose. Do not modify weights, shape keys, topology or gates until the failing contribution has been isolated.
