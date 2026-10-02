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

Updated 2026-10-02 from executed evidence (see `docs/ORIGINAL_V1_SKELETON_MOTION_LOCK.md`).

| Region | Status | Rig defect? | Extra bone/helper? | Evidence path | Notes |
|---|---|---|---|---|---|
| head/neck | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | neck/head hinge in squat/row within envelope; single neck + head chain sufficient for exercise instruction |
| thorax/spine | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | pelvis hinge plus three spine segments distribute flexion (row: pelvis 38 + spine 10; squat 18 + 15); rib-cage proxy built; no rib bones, no chest helper required |
| shoulder girdle | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | clavicle + scapula + humerus coherent through press/pull-up; rhythm poses use a modest, non-fixed scapular share (references show 0.9:1..3.8:1); axilla defect classified as pose/rig construction and fixed (P2 + twist helpers) |
| upper arm / twist | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | upperarm_tw0/tw1 (l,r) | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | humeral rotation 63-90 deg in 7 poses; twist stress at 90 deg: slice radius 0.856 -> 0.907 but the abstract minimum edge worsened 0.28 -> 0.22 at the dense (8 mm) deltoid edges; in the real stress poses the helpers clear the shoulder-minimum development failures (5 -> 2 failures vs P2B1) at the price of arm-region stretch up to 3.2 (gate 5.0), left to the weight re-solve; forearm-only variant r42 shown for contrast |
| elbow | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | hinge purity: elbow abduction within +-10 deg in all poses and samples (P1: up to 107 deg sideways) |
| forearm / twist | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | forearm_tw0/tw1 (l,r) | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | twist stress 90 deg: slice radius 0.76 -> 0.92, edge min 0.705 -> 0.92 |
| wrist | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | push-up: ~78 deg loaded extension, small ulnar deviation (P1: 88 deg radial deviation); no wrist helper required |
| palm | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | palm planted (hand region 3.6 mm, thumb pad 0 mm, palm normal 5.7 deg from the floor normal); cupping handled by metacarpal + finger chains; palm helpers not justified |
| thumb | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | P1 reversed the thumb IP in the grip; fixed with a single chain hinge; thumb flattened into the palm plane for loaded support |
| fingers | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | P1 bent the distal joint backwards (-55 deg; -85 on handle grips) in 11 poses due to pose-construction axis flip; fixed (fixed hinge axis); 0 reversal flags |
| hip | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | squat/lunge within envelope; thigh twist helper considered and rejected (femoral 45 deg: slice radius 0.99, edge 0.86) |
| knee | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | flexion 98 (squat), 79/62 (lunge) within envelope, hinge only; no helper |
| shin/calf / twist | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | shin twist helper considered and rejected (physiological +-30 deg: slice radius 0.97, edge 0.90) |
| ankle | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | P1 squat ankle plantarflexed (seated posture); P2 dorsiflexion 23 deg, push-up <= ~25 deg |
| forefoot/toes | LOCKED (2026-10-02, r41, rig rev2) | rig bones: none; pose-construction defects fixed in P2 where noted | no | ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r41/ (kinematics, finger, twist, floor, envelope, proxy, review images) | P1 bent the toe the wrong way (-60 deg); P2 dorsiflexion 80 deg with toe pads on the floor; single toe bone sufficient for support mechanics; hallux/lesser-toe split deferred until individually modelled toes exist (Phase 5F trigger documented) |

No row may be marked LOCKED solely because the current model passes a deformation metric.
