# ORIGINAL v1 skeleton joint validation matrix

Status: PREPARED FOR BLENDER / REFERENCE EXECUTION  
Effective: 2026-10-02

This matrix converts the owner-mandated skeleton-motion gate into a joint-by-joint checklist.
It is not a substitute for the detailed policies:
- `docs/SKELETON_HUMAN_MOVEMENT_AND_BONE_SUFFICIENCY_POLICY.md`
- `docs/EXTERNAL_HUMAN_MOVEMENT_REFERENCE_POLICY.md`
- `docs/work_packages/PHASE_2_3_SKELETON_MOTION_VALIDATION_20261002.md`

External sources below are reference-only. Record source metadata/timecodes/observations; do not
transfer external assets or person-specific geometry into production.

| Region | Current project controls to inspect | Human movement question | Minimum evidence before lock | Bone-sufficiency question |
|---|---|---|---|---|
| Cervical/head | neck, head | Can head/neck flex, extend and rotate without forcing shoulder/torso deformation? | skeleton-only neutral + representative row/overhead motion; >=2 anatomy/kinematics sources | existing neck/head chain sufficient for exercise instruction? |
| Thorax/spine | pelvis, spine_01..03 | Does thoracic/lumbar motion distribute plausibly instead of hinging at one segment? | continuous squat/lunge/row/overhead inspection; thorax/rib-cage proxy review | need generic thorax/chest helper or corrective deformation, not individual rib bones by default? |
| Shoulder girdle | clavicle_l/r, scapula_l/r, upperarm_l/r | Does elevation combine humerus, scapula and clavicle plausibly through the whole arc? | press/pull-up skeleton-only sweep, front/side/3/4; >=3 sources | current scapula/clavicle controls sufficient? twist/helper or corrective needed? |
| Upper arm | upperarm_l/r | Can axial rotation be represented without dumping twist at shoulder/elbow? | overhead + row + press sweep; skin-off then skin-on comparison | upper-arm twist helper justified? |
| Elbow | forearm_l/r relative to upperarm | Does elbow hinge in correct direction while forearm rotation remains separable? | curl/press/row sweep; >=2 sources | existing chain adequate? |
| Forearm | forearm_l/r, hand_l/r | Can pronation/supination distribute naturally along forearm? | supinated curl, pronated push-up/press, pull-up grip | forearm twist helper justified? |
| Wrist | hand_l/r relative to forearm | Can wrist flex/extend/deviate without twisting hand support unnaturally? | push-up top/mid/bottom; curl/grip; >=3 sources for current high-risk review | current hand joint enough, or helper needed for loaded support? |
| Palm | hand + metacarpals | Can palm orient/cup while retaining flat loaded support when required? | push-up flat-palm review + cylindrical grip | palm/cupping helper justified only if correct bones cannot deform skin plausibly |
| Thumb | thumb_01..03 | Is opposition/flexion anatomically coherent and compatible with equipment contact? | neutral, cylindrical grip, pull-up/bar; >=3 sources where practical | existing 3-bone thumb chain sufficient? |
| Fingers | metacarpals + index/middle/ring/pinky 01..03 | Do MCP/PIP/DIP flex in coherent directions with no reverse distal bending? | skeleton-only curl/grip/bar sweeps; >=3 sources | do not add bones until axes/limits/pose logic proven correct |
| Hip | thigh_l/r relative to pelvis | Can flexion/extension, ab/adduction and rotation needed by squat/lunge occur without pelvis tearing? | squat/lunge continuous sweep; >=2 sources | thigh twist helper justified? |
| Knee | shin_l/r relative to thigh | Does knee behave primarily as a flexion/extension joint with plausible coupled motion? | squat/lunge sweep, side/front | existing knee chain sufficient for exercise set? |
| Shin/calf | shin_l/r | Does lower-leg axial behaviour distribute without ankle/knee candy-wrapper deformation? | squat/lunge/stance skin-off/on comparison | shin/calf twist helper justified? |
| Ankle | foot_l/r relative to shin | Can dorsiflexion/plantarflexion and required small multi-axis adjustment support squat/lunge/push-up? | squat/lunge/push-up foot sweep; >=2 sources | current ankle/foot control sufficient? |
| Forefoot/toes | toe_l/r | Can the rig represent loaded forefoot/toe dorsiflexion without rotating all toes unnaturally as one block? | push-up toe support + squat/lunge floor contact; >=3 sources for current high-risk review | single toe control sufficient, or hallux + grouped lesser-toe control justified? |

## Starting human-reference evidence

### Fingers / grip
- Finger Kinematics during Human Hand Grip and Release  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC10296280/
  - use to inspect relative MCP/PIP/DIP contribution through grip/release;
  - do not assume all finger joints contribute equally.

- Hand kinematics: Application in clinical practice  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3193629/
  - use for linked PIP/DIP behaviour and multi-joint hand kinematics.

### Wrist / loaded palm
- Dorsal Wrist Pain in the Extended Wrist-Loading Position  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5658215/
  - confirms that push-up-type loading is an extended-wrist loading condition;
  - use for qualitative loaded wrist orientation, not a single universal angle.

- Anatomy, Biomechanics, and Loads of the Wrist Joint  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8880601/

- Wrist Biomechanics  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5397304/

### Shoulder
- Assessment of scapulohumeral rhythm for scapular plane shoulder elevation  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3377910/

- Scapulothoracic rhythm affects glenohumeral joint force  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6620199/

- Characteristics of scapula movement during shoulder elevation depend on posture  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9246406/

Use these together. Do not encode one fixed universal scapulohumeral ratio across the whole elevation arc.

### Knee / lower limb
- Knee Joint Biomechanics in Physiological Conditions and How Pathologies Can Affect It  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7160724/

Use exercise-specific squat/lunge references as an additional task layer rather than assuming walking
kinematics define squat/lunge movement.

### Foot / forefoot / toes
- Midfoot and forefoot involvement in lateral ankle sprains  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5095951/
  - useful reminder that the foot behaves as multiple functional segments rather than one rigid block.

- Effects of Short-Term Limitation of Movement of the First Metatarsophalangeal Joint  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7941761/

Use competent push-up examples in addition to gait/foot literature for the actual push-up toe-support task.

## Blender evidence sequence per row

For every region:

1. Run `scripts/audit_original_v1_rig_structure_blender.py`.
2. Run `scripts/audit_original_v1_skeleton_motion_blender.py` for relevant poses.
3. Hide skin and inspect the joint through continuous motion.
4. Compare against the required number of independent sources.
5. Record:
   - observed rig behaviour;
   - source-supported human behaviour;
   - match / mismatch;
   - root cause;
   - whether extra bone/helper is required.
6. If rig changes, assign a new rig revision/hash and rerun all dependent deformation/contact evidence.
7. Only mark the row LOCKED when there is no known unresolved skeleton-level defect.

## Lock table

Claude should copy/update this section during the laptop session rather than claiming completion from prepared text.

| Region | Status | Rig defect? | Extra bone/helper? | Evidence path | Notes |
|---|---|---|---|---|---|
| head/neck | NOT RUN | — | — | — | |
| thorax/spine | NOT RUN | — | — | — | |
| shoulder girdle | NOT RUN | — | — | — | |
| upper arm / twist | NOT RUN | — | — | — | |
| elbow | NOT RUN | — | — | — | |
| forearm / twist | NOT RUN | — | — | — | |
| wrist | NOT RUN | — | — | — | |
| palm | NOT RUN | — | — | — | |
| thumb | NOT RUN | — | — | — | |
| fingers | NOT RUN | — | — | — | |
| hip | NOT RUN | — | — | — | |
| knee | NOT RUN | — | — | — | |
| shin/calf / twist | NOT RUN | — | — | — | |
| ankle | NOT RUN | — | — | — | |
| forefoot/toes | NOT RUN | — | — | — | |

No row may be marked LOCKED solely because the current model passes a deformation metric.
