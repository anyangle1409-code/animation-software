# Skeleton human-movement reference and bone-sufficiency policy

Status: OWNER-MANDATED PRE-LOCK VALIDATION
Effective: 2026-10-02
Scope: `hgpt_canonical_v4_original` functional skeleton/rig validation before deformation freeze.

## Goal

Do not lock the production skeleton merely because it has the expected hierarchy or because endpoint
poses can be produced.

The production rig must:
1. represent the human joint motions needed by the exercise system;
2. move in anatomically defensible directions and ranges;
3. provide enough deformation degrees of freedom to support natural skinning;
4. avoid unnecessary anatomical complexity that does not improve movement/deformation;
5. be validated against multiple independent human anatomy/biomechanics sources before final lock.

Correctness takes priority over preserving the current 63-bone count.

## Multiple-source rule

For each major joint group, use at least **two independent reputable sources** before converting
external evidence into a project-owned movement rule. For complex/high-risk areas currently under
review (shoulder girdle, hand/fingers/wrist, foot/toes), use **three sources where practical**.

Prefer:
- peer-reviewed biomechanics/kinematics reviews or in-vivo studies;
- NCBI Bookshelf / PMC or comparable academic/clinical anatomy resources;
- established biomechanics standards when available;
- multiple subjects/studies rather than a single person's demonstration.

Do not treat a single reported range or one person's technique as the only correct human movement.
Record normal variability and distinguish:
- required joint direction / mechanical relationship;
- typical range;
- task-specific range;
- normal human variation.

External sources remain reference-only under
`docs/EXTERNAL_HUMAN_MOVEMENT_REFERENCE_POLICY.md`.

## Starter source set

These are starting references, not a closed list. Claude may find better or more specific sources.

### Hand / fingers

1. NCBI Clinical Methods — The Musculoskeletal Examination
   https://www.ncbi.nlm.nih.gov/books/NBK272/
   Useful for broad clinical finger and wrist ROM reference.

2. Hand kinematics: Application in clinical practice
   https://pmc.ncbi.nlm.nih.gov/articles/PMC3193629/
   Useful for PIP/DIP linked motion, MCP degrees of freedom and hand-chain behaviour.

3. Jam Injuries of the Finger: Diagnosis and Management...
   https://pmc.ncbi.nlm.nih.gov/articles/PMC5010131/
   Useful for PIP/DIP hinge behaviour and approximate flexion ranges.

### Wrist / forearm

1. Anatomy, Biomechanics, and Loads of the Wrist Joint
   https://pmc.ncbi.nlm.nih.gov/articles/PMC8880601/

2. Wrist Biomechanics
   https://pmc.ncbi.nlm.nih.gov/articles/PMC5397304/

3. Clinical anatomy and biomechanics of the elbow
   https://pmc.ncbi.nlm.nih.gov/articles/PMC8258984/
   Useful for separating elbow flexion/extension from forearm pronation/supination.

### Shoulder girdle

1. The biomechanics of the rotator cuff in health and disease — narrative review
   https://pmc.ncbi.nlm.nih.gov/articles/PMC8111677/

2. Assessment of scapulohumeral rhythm...
   https://pmc.ncbi.nlm.nih.gov/articles/PMC3377910/

3. Scapular and rotator cuff muscle activity during arm elevation...
   https://pmc.ncbi.nlm.nih.gov/articles/PMC2857390/

4. Characteristics of scapula movement during shoulder elevation depend on posture
   https://pmc.ncbi.nlm.nih.gov/articles/PMC9246406/

Important: do not encode a rigid universal 2:1 scapulohumeral ratio. Evidence shows the contribution
changes through the elevation arc and varies normally.

### Knee / lower limb

1. Knee Joint Biomechanics in Physiological Conditions...
   https://pmc.ncbi.nlm.nih.gov/articles/PMC7160724/

2. Kinematics of the Normal Knee during Dynamic Activities...
   https://pmc.ncbi.nlm.nih.gov/articles/PMC5405570/

### Ankle / foot / toes

1. Biomechanics of the ankle
   https://pmc.ncbi.nlm.nih.gov/articles/PMC4994968/

2. First metatarsophalangeal joint: Embryology, anatomy and biomechanics
   https://pmc.ncbi.nlm.nih.gov/articles/PMC12019138/

3. Three-Dimensional Kinematics of the Human Metatarsophalangeal Joint during Level Walking
   https://pmc.ncbi.nlm.nih.gov/articles/PMC4266096/

Use these to establish direction/functional relationships. Push-up toe support is task-specific and
must also be checked against competent real push-up examples.

### Thorax / rib cage

1. How Does the Rib Cage Affect the Biomechanical Properties of the Thoracic Spine?
   https://pmc.ncbi.nlm.nih.gov/articles/PMC9240654/

2. Introduction to Chest Wall Reconstruction: Anatomy and Physiology of the Chest...
   https://pmc.ncbi.nlm.nih.gov/articles/PMC3140236/

These establish that the rib cage affects thoracic stiffness/stability and that ribs/sternum move
during respiration. They do NOT imply that an animation rig needs a deform bone for every rib.

## Bone-sufficiency audit before final skeleton lock

Before locking the skeleton, evaluate the current rig by **function**, not by bone count.

For each region ask:
- Can the existing bones represent all required human degrees of freedom?
- Are the joint centres and local axes appropriate?
- Can continuous motion be produced without non-human coupling or sign reversal?
- Can the skin distribute twist/volume around the joint without obvious candy-wrapper collapse,
  pinching or rigid blocks?
- Is the problem a missing anatomical degree of freedom, or merely a skinning/topology problem?
- Would an extra helper/deform bone solve a generic class of movement, or would it be an
  exercise-specific hack?

### Candidate additions that must be evaluated

Do NOT add these automatically. Test whether evidence demonstrates need.

#### Twist/deformation helpers
Consider helper/deform bones for:
- upper-arm twist;
- forearm twist;
- thigh/femur twist;
- shin/calf twist.

These are not extra anatomical joints. Their purpose is to distribute axial rotation through a
long soft-tissue segment rather than concentrating it at one end.

If linear skinning around the current major bone produces unnatural twisting despite correct joint
motion and carefully authored weights/topology, a twist helper may be justified.

#### Shoulder / thorax helpers
The current shoulder system already has project-owned clavicle/scapula concepts. Validate whether
their axes and coupled movement are sufficient before adding anything.

Potential additional helper controls may be justified for:
- upper-thorax/chest deformation;
- sternum/chest expansion;
- generic elevation-driven soft-tissue correction.

Prefer a small number of generic deformation controls or joint-angle-driven corrective shapes over
adding many pseudo-anatomical bones solely to chase a silhouette.

#### Foot / toes
Determine whether one foot + one toe chain per side is sufficient for:
- push-up forefoot support;
- squat/lunge floor contact;
- later shoe deformation;
- required barefoot instructional views.

If the single toe control cannot represent the required forefoot/hallux behaviour without
distorting the whole toe region, consider a more expressive first-party forefoot structure (for
example a hallux/major-toe control plus a grouped lesser-toe control). Add only if the exercise and
deformation evidence requires it.

#### Hand
The existing finger chains must first be validated for axes, limits and pose construction. More
finger bones should not be added merely to fix an axis/sign error.

Only add extra hand helpers if the existing joint chains are anatomically correct but cannot produce
required palm cupping, thumb opposition/contact or loaded palm deformation without broad mesh
distortion.

## Do we need a 3D skeleton mesh?

A separate visible 3D anatomical skeleton **does not replace the armature** and does not
automatically improve skin deformation.

However, a project-owned **3D anatomical proxy** can be valuable as a non-production validation
tool.

Recommended use:
- generate simple first-party proxy geometry around the existing armature;
- show approximate pelvis, thoracic cage/sternum, scapulae, humeral heads, long-bone shafts and
  major joint centres;
- use it to inspect proportions, clearances, joint centres and coupled motion with the skin hidden;
- never copy a third-party anatomical skeleton mesh.

The armature remains the movement driver. The proxy is an anatomical/debug reference.

## Rib cage / chest decision

The rib cage matters to real human thoracic mechanics and to the visual foundation of the chest.
It should therefore be represented in the **anatomical volume and validation model**.

This does NOT mean adding 24 individual deforming ribs.

For this exercise-instruction character, first validate whether the following are enough:
- pelvis + existing spine chain;
- an anatomically proportioned thoracic/rib-cage volume in the body mesh;
- clavicles and scapulae;
- correct thoracic extension/rotation behaviour;
- appropriate torso weights/topology;
- generic corrective deformation where linear skinning is insufficient.

If later requirements include visible breathing/chest expansion, add a project-owned chest-expansion
control or corrective deformation system only after a specific requirement is defined and tested.

A simple first-party 3D rib-cage/sternum **proxy** is recommended for joint/volume validation because
it can help position the shoulder girdle and judge chest depth/width. It should not be mistaken for
a skin-driving requirement.

## Skeleton lock output

Before the skeleton is considered locked, produce:

- exact rig revision/hash;
- complete bone list and parent map;
- joint-centre/rest-transform audit;
- local-axis audit;
- joint-limit/movement-envelope table;
- multi-source reference matrix with source metadata;
- continuous skeleton-only motion evidence;
- left/right symmetry audit;
- bone-sufficiency decision for every major region;
- explicit list of any new anatomical or helper bones and why each one exists;
- explicit list of considered-but-rejected bones/helpers and why they were unnecessary;
- dependent deformation/contact regression results;
- skeleton-only review images/video frames with the skin hidden;
- final skeleton-motion lock record.

After this lock, skinning/deformation work proceeds on the locked rig by default.
