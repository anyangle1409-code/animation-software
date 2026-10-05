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

## Investigation checkpoint — production-path reproduction

Blender 5.2.1 LTS loaded the recovered r95 candidate and passed the candidate smoke inspection:

- candidate hash matched `8a39a22d...8403bdd`;
- rig identity `hgpt_canonical_v4_original`;
- rig revision `rev2_forearm_twist_only`;
- 67 bones / 66 deform bones;
- no linked libraries;
- source scene was not saved or modified.

The P3a pose renderer regenerated neutral, press-top and curl-handle milestone images. Pixel comparison of the regenerated images against the committed r95 milestone PNGs returned no differing pixel for the two shoulder views, press-top three-quarter view or curl-handle three-quarter view. Therefore the owner-rejected appearance is present in the exact frozen candidate and exact production deformation path. It is not an obsolete screenshot, omitted driver or rendering mismatch.

The Windows `python` command is an unavailable Store alias on this laptop. Use the bundled workspace Python at `C:/Users/Mark/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`, or Blender's Python where appropriate. Blender is at `C:/Program Files/Blender Foundation/Blender 5.2/blender.exe`.

## Investigation checkpoint — corrective-layer isolation

The four high-elevation shoulder poses were rendered from r95 with scene driver configurations disabled in memory. No Blend was saved.

| State | Press-top volume | Compressed edges | Stretched edges | Self-intersections | Visual result |
|---|---:|---:|---:|---:|---|
| weights only | 1.0095 | 648 | 853 | 58 | very large lateral torso/axilla wing pulled toward the raised arm |
| abduction corrective only | 1.0050 | 548 | 877 | 30 | wing folded inward, but deep pec/axilla scoop and membrane introduced |
| scapular corrective only | 1.0023 | 658 | 859 | 58 | wing reduced to a smaller pointed flap; underlying ownership remains wrong |
| all r95 correctives | 0.9958 | 556 | 865 | 30 | external wing mostly hidden, but scoop, trench, membrane and pec collapse remain |

The forward-flexion corrective is effectively inactive in the press-top abduction plane, as expected from the driver definition.

### Root-cause conclusion

The first failing boundary is the underlying shoulder/torso skin-weight and support structure. The base weights create the large wing. The abduction and scapular correctives compensate for that wing rather than deforming an anatomically supported anterior/posterior axillary structure. Their combined result trades the external wing for the owner-rejected trench, membrane, chest transport and volume collapse.

This is an architectural limit of the current correction stack, not a single bad threshold. The r49-r95 history already contains many local corrective attempts with migrating trade-offs. Do not add another local patch to r95.

## Selected recovery architecture

The owner delegated model control and requested unattended progress, so the recovery uses the evidence-selected foundational option:

1. Preserve r95 unchanged as the frozen comparator.
2. Rebuild the shoulder-yoke/axilla foundation in a new candidate with explicit anterior fold, posterior fold, deltoid/pec transition and thoracic support zones.
3. Re-solve local weights against clavicle, scapula, thorax and humerus motion before fitting new correctives.
4. Fit generic motion-driven correctives only after the weights-only surface forms plausible folds throughout the elevation arc.
5. Validate against real-human references and the complete movement/regression matrix.

Rejected alternatives:

- continuing directly into cosmetic Phase 5 sculpting on r95, because the weights-only deformation is already structurally wrong;
- adding another r95 corrective, because previous layers conceal one failure by producing another;
- weakening gates or accepting the defect, because the owner explicitly rejected the visual result.

## Power-loss / phone continuation

Authoritative branch: `codex/whole-body-deformation-recovery-20261004`.

On any other device or session:

1. fetch that branch;
2. read this file before acting;
3. preserve r95 and all historical evidence;
4. continue read-only evidence collection or design work if the exact local Blend is unavailable;
5. do not claim a model correction without a new candidate, production-path renders and complete regression evidence.

## Autonomous r96 checkpoint — 2026-10-05

The deformation-layer diagnostic, declaration controls and first r96 foundation probes are complete and pushed. r95 remains immutable. Production approval remains false and every Critical/High shoulder issue remains open.

### Evidence established

- A declared 120-vertex all-quad support ring preserved all original geometry, weights and shape-key points, but did not remove the pointed axillary notch, membrane or posterior wing.
- Mild bounded weight diffusion was numerically non-regressive but visually near-identical to r95. Stronger diffusion regressed press-top compression.
- Declared 4/8/12 mm support-row rest-length probes failed: 4 mm retained the visible defects, while 8/12 mm increased squat self-intersections.
- A declared 164-vertex anatomical fold transfer toward upper arm/clavicle/scapula failed monotonically. Even 15% increased failed checks from 2 to 10; 45% reached 144 press-top self-intersection pairs and 11.470 torso maximum stretch.
- Exact edge localization found the dominant lower/anterior axilla strain cells (`6-6290`, `922-6290`, `890-6231`, `6-4507`, `859-6105`) and proved the first support ring crossed the wrong cells.
- Three newly declared 64-edge lower support rows authored cleanly, but interpolated topology alone increased failed checks from 2 to 3, produced 14 material regressions and zero improvements. Press-top torso maximum stretch rose from 3.545 to 4.690.

### Current technical conclusion

The failures are no longer consistent with insufficient mesh density or a simple broad weight-ownership error. The exact high-strain chain already has a smooth thorax-to-arm weight gradient; under extreme elevation, linear blend skinning turns that gradient into either stretched membrane or transported wing. More interpolated vertices inherit the incompatible endpoint motion, while more arm ownership amplifies the torso stretch.

Do not add more support loops or broaden arm-follow weights. Preserve-volume/dual-quaternion skinning was considered read-only and rejected as a delivery architecture: Blender's Preserve Volume option uses quaternion deformation, while the required glTF 2.0 runtime skinning path is explicitly a weighted linear sum of joint matrices and has no field for the Blender modifier setting. A Blender-only visual improvement would therefore not reproduce in the application.

The viable path remains the already owner-authorized, generic elevation-driven morph-target architecture in `docs/ORIGINAL_V1_SHOULDER_CORRECTIVE_DESIGN.md`. glTF applies morph-target displacement before skinning, matching that design. Resume Task 7 from the topology-only r96 intermediate, but do not reuse r95's failed displacement field: declare a fresh mask and fit one residual behavior at a time with explicit inward-displacement, volume, fold and whole-body regression guards.

### Recoverable state

- Branch: `codex/whole-body-deformation-recovery-20261004`
- Latest pushed checkpoint: `821db94` (`Reject interpolated r96 lower support rows`)
- Exact r95 SHA-256: `8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd`
- Topology-only r96 intermediate SHA-256: `6934594dde9140193882c0e293f8b404fb24bed8b1b1b2722267ff97d13844dd`
- Correctives stayed disabled for every Task 6 numerical and visual screen.
- Generated probes remain under ignored `work/r96/`; all decisions, declarations, comparison reports and authoring receipts needed to reproduce them are committed.

Next laptop action: begin the already-approved Task 7 residual-corrective declaration from the topology-only r96 intermediate. Keep r96 fail-closed and promote nothing until the complete numerical and visual gates pass.
