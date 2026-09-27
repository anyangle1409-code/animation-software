# ORIGINAL v1 whole-body movement-envelope validation

## Purpose

Prove that the clean-room character deforms correctly across human movement categories, not merely across whichever exercises happen to exist in the library.

Exercise playback is one source of evidence. Synthetic anatomical stress poses are a second, independent source.

## Existing exercise coverage

### Trunk flexion
- sit-up
- crunch

Stress:
- lumbar/thoracic flexion;
- abdominal compression;
- pelvis/hip relationship;
- head/neck continuity.

### Trunk rotation
- Russian twist
- cable woodchop

Stress:
- thoracic/lumbar axial rotation;
- oblique region;
- ribcage/pelvis counter-rotation.

### Anti-rotation
- Pallof press

Stress:
- torso rigidity under lateral cable load;
- shoulder/hand load without trunk twist.

### Hip hinge
- Romanian deadlift
- bent-over row

Stress:
- hip flexion with long spine;
- hamstring/glute region;
- pelvis-to-lumbar transition.

### Squat / lunge
- air squat
- split squat
- forward lunge
- reverse lunge

Stress:
- deep hip/knee flexion;
- ankle dorsiflexion;
- groin/glute folds;
- unilateral stance;
- back-foot toe extension.

### Calf / ankle
- calf raise
- dumbbell calf raise

Stress:
- plantarflexion;
- Achilles/ankle surface;
- forefoot loading.

### Horizontal push
- push-up
- dumbbell bench press
- dumbbell fly

Stress:
- shoulder horizontal motion;
- chest/axilla;
- elbow;
- loaded wrist extension for push-up;
- bench contact.

### Vertical push
- shoulder press
- seated shoulder press

Stress:
- shoulder elevation/abduction;
- axilla;
- scapular region;
- elbow lockout;
- overhead hand position.

### Vertical pull / hang
- pull-up

Stress:
- overhead traction;
- shoulder/scapula;
- elbow flexion;
- bar grip;
- full body suspended from hands.

### Shoulder raise
- front raise
- lateral raise

Stress:
- shoulder flexion/abduction through long lever;
- deltoid/upper-arm junction.

### Elbow flexion
- bicep curl
- hammer curl
- reverse curl
- incline curl

Stress:
- elbow fold;
- forearm rotation;
- multiple grip orientations;
- shoulder/upper-arm resting alignment.

### Elbow extension
- cable pushdown
- overhead extension

Stress:
- deep elbow flexion into extension;
- overhead triceps path;
- cable grip.

### Carry / gait-like support
- farmer's walk

Stress:
- loaded neutral arms;
- bilateral equipment;
- standing alignment.

## Synthetic movement-envelope poses

These must exist even if there is no production exercise using them yet.

### Spine
1. maximum certified trunk flexion;
2. moderate extension;
3. left/right axial rotation;
4. left/right lateral flexion;
5. combined flexion + rotation at conservative range.

### Shoulder
1. sagittal flexion;
2. abduction;
3. extension;
4. internal/external rotation with arm down;
5. internal/external rotation at elevated arm;
6. cross-body adduction;
7. overhead reach with scapula at rest;
8. later, overhead reach with approved scapular rhythm.

### Elbow / forearm
1. near-full flexion;
2. full extension;
3. pronation;
4. supination;
5. flexion + pronation;
6. flexion + supination.

### Wrist / hand
1. extension floor-load pose;
2. flexion;
3. radial/ulnar deviation;
4. open hand;
5. full fist;
6. cylindrical power grip;
7. pull-up/bar grip;
8. thumb-to-index/middle/ring/pinky opposition.

### Hip
1. deep flexion;
2. extension;
3. abduction;
4. adduction;
5. internal/external rotation;
6. combined flexion + rotation at conservative range.

### Knee
1. full standing extension;
2. moderate flexion;
3. deep squat flexion;
4. kneeling-range stress if within certified rig range.

### Ankle / foot
1. dorsiflexion;
2. plantarflexion;
3. inversion/eversion;
4. toe extension under lunge;
5. forefoot loading.

## Measurements for every pose

Record:
- mesh self-intersection summary;
- nonmanifold/degenerate state unchanged;
- worst triangle area retention;
- edge stretch/compression percentiles;
- joint-region volume proxy;
- silhouette continuity;
- left/right equivalence;
- skin-weight normalisation;
- contact drift where a contact is expected;
- body/equipment clearance where equipment is present.

## Visual boards

Generate matched neutral + stress-pose views:
- front;
- side;
- back;
- three-quarter;
- joint close-up where needed.

The board must make it possible to reject:
- collapsing armpit;
- shoulder ledge;
- elbow spike;
- pinched groin;
- knee cave/fold;
- wrist collapse;
- segmented fingers;
- thumb web tearing;
- spine accordion folding.

## Acceptance rule

ORIGINAL v1 is not a finished production character merely because every current exercise runs.

It must pass:
1. the existing exercise library;
2. the synthetic whole-body envelope;
3. contact/equipment tests;
4. final visual review.

This is the model-level foundation for future prompt-generated exercises such as new sit-up, rotation, mobility or bodyweight variants.
