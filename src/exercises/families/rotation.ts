import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import type { TechniqueRule } from '../../constraints/types';
import { vec3 } from '../../rig/types';
import { bilateralJoints } from '../mirror';
import { seatedStance } from '../stance';
import { hingeRoot } from './hinge';

/**
 * The rotation family: the trunk turning, driven by the obliques, while the
 * hips stay put.
 *
 * The twelfth family. Where anti-rotation (the Pallof press) holds the trunk
 * still against a twisting load, this one makes the twist the movement. The
 * rotation is spread up the spine in proportion to what each joint allows —
 * lumbar 10°, lower thoracic 18°, upper thoracic 22°, 50° in all — with the
 * neck adding 12° so the eyes follow the hands. The pelvis does not turn.
 *
 * ## The Russian twist
 *
 * Seated on the floor, leaning back 40°, knees bent and heels down, hands
 * clasped in front of the chest. The shoulders turn from side to side.
 *
 * * **One side to the other is the whole repetition.** The start pose is turned
 *   left and the peak turned right, so the clip's blend between them passes
 *   through square; turning right and turning left are both concentric, both
 *   timed from `tempo.concentric`.
 * * **The arms are authored in joint angles**, relative to the chest, so they
 *   turn with it. Hand IK targets would be fixed in the world and blend in a
 *   straight line from one side to the other, cutting through the arc the
 *   hands actually travel; at this reach the hands would pass 10 cm closer to
 *   the chest at the middle. The angles were solved for wrists 5 cm apart,
 *   35 cm in front of the chest, fingertips 3.5 cm apart: palms pressed.
 * * **Sitting on the floor** was tuned against the production character, as
 *   the benches were. With the pelvis joint 14.6 cm up the buttocks rest 8 mm
 *   into the floor; at 13 cm they sank 23 mm.
 * * The rig's twist is positive to the body's right (the hands go to +x). Its
 *   joint-limit labels read the other way round; the angles here are measured.
 */

export interface RotationVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

/** The pelvis joint, seated on the floor, and the trunk's lean back. */
const SEAT = { pelvis: { y: 0.146, z: 0 }, pitch: -40 };

/** Heels down 30 cm apart, 58 cm in front of the hips: knees bent about 95°. */
const FEET = { width: 0.3, toeOut: 6, forward: 0.58 };

/** Twist per joint, degrees, turned right; turned left is the negative. */
const TWIST = { spine_01: 10, spine_02: 18, spine_03: 22, neck: 12 };

/** The trunk turned to one side: +1 right, -1 left. */
function trunk(side: 1 | -1) {
  return {
    pelvis: { x: 0, y: 0 },
    spine_01: { x: 0, y: side * TWIST.spine_01 },
    spine_02: { x: 0, y: side * TWIST.spine_02 },
    spine_03: { x: 0, y: side * TWIST.spine_03 },
    // Nodded forward to look at the hands rather than the ceiling.
    neck: { x: 15, y: side * TWIST.neck },
    head: { x: 5 },
  };
}

/** Starting guesses; the planted feet decide the legs. */
const LEGS = bilateralJoints({ thigh_l: { x: 85, z: -6 }, shin_l: { x: -90 }, foot_l: { x: 0 } });

/**
 * Hands clasped in front of the chest, palms together (solved; see the header),
 * the wrists straight and the forearms turned so the index knuckles sit above
 * the little fingers'. A first solve let the wrists flex 6°; the production
 * character's hands then rolled 1.1° away from the rig's, through its embedded
 * palm-roll correction, where every other exercise holds within 0.72°. A
 * second, with straight wrists but no say over the palms, turned them up.
 */
const ARMS = bilateralJoints({
  upperarm_l: { x: 31.5, y: 28.3, z: 30.8 },
  forearm_l: { x: 43.3, y: -41.5 },
  hand_l: { x: 0, z: 0 },
});

export function rotationFamily(variant: RotationVariant): ExerciseDefinition {
  const stance = seatedStance(FEET);
  const root = hingeRoot(SEAT.pitch, SEAT.pelvis);
  const seat = { position: { y: root.y, z: root.z }, rotation: { x: SEAT.pitch } };
  const body = { ...LEGS, ...ARMS };

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'core',
    description: variant.description,

    equipment: { required: [], instances: [] },

    startPose: { label: 'Turned left', joints: { ...body, ...trunk(-1) }, root: seat },
    peakPose: { label: 'Turned right', joints: { ...body, ...trunk(1) }, root: seat },

    jointTargets: [],

    phases: [
      { id: 'turn_right', label: 'Turn right', to: 'peak', easing: 'lift', contraction: 'concentric' },
      { id: 'right', label: 'Right', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'turn_left', label: 'Turn left', to: 'start', easing: 'lift', contraction: 'concentric' },
      { id: 'left', label: 'Left', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    // Both turns are concentric, so `eccentric` goes unused.
    tempo: variant.tempo ?? { concentric: 1, pauseContracted: 0.25, eccentric: 1, pauseStretched: 0.25 },

    hands: { grip: 'none', orientation: 'neutral', closure: 0.6 },
    feet: stance.feet,
    locks: stance.locks,

    muscles: {
      primary: ['obliques'],
      secondary: ['rectus_abdominis'],
      stabilisers: ['erector_lower', 'hip_adductors', 'quadriceps'],
      ...variant.muscles,
    },

    technique: [
      ...stance.technique,
      {
        kind: 'jointAngle',
        id: 'hips_still',
        label: 'Hips stay facing forward — the turn comes from the trunk',
        bone: 'pelvis',
        axis: 'y',
        min: -3,
        max: 3,
        severity: 'error',
      },
      {
        kind: 'stationary',
        id: 'seated',
        label: 'Stays seated, without rocking',
        point: { bone: 'pelvis' },
        tolerance: 0.005,
        severity: 'error',
      },
      {
        kind: 'segmentAngle',
        id: 'lean_back',
        label: 'Leans back about 40°, neither upright nor lying down',
        bone: 'spine_02',
        reference: 'vertical',
        min: 30,
        max: 55,
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'full_turn_right',
        label: 'Turns fully to the right',
        bone: 'spine_03',
        axis: 'y',
        min: 18,
        phases: ['right'],
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'full_turn_left',
        label: 'Turns fully to the left',
        bone: 'spine_03',
        axis: 'y',
        max: -18,
        phases: ['left'],
        severity: 'error',
      },
      {
        kind: 'distance',
        id: 'hands_clasped',
        label: 'Hands stay clasped together',
        from: { bone: 'hand_l', along: 0.5 },
        to: { bone: 'hand_r', along: 0.5 },
        max: 0.06,
        severity: 'error',
      },
    ] satisfies TechniqueRule[],

    commonErrors: [
      {
        id: 'arms_only',
        label: 'Swinging the arms',
        description: 'The hands swing side to side while the chest stays facing forward.',
        ruleId: 'full_turn_right',
        correction: 'Keep the hands in front of the sternum and turn the shoulders with them.',
      },
      {
        id: 'hips_turning',
        label: 'Turning the hips',
        description: 'The knees and hips swing with the trunk, so the obliques never twist against anything.',
        ruleId: 'hips_still',
        correction: 'Keep the knees pointing forward and the hips square.',
      },
      {
        id: 'sitting_up',
        label: 'Sitting upright',
        description: 'The trunk comes up to vertical, taking the load off the abdominals.',
        ruleId: 'lean_back',
        correction: 'Hold the lean back, spine long, throughout.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe out as you turn to each side, in through the middle.',
    },

    camera: {
      preset: 'front',
      position: vec3(0.6, 1.3, 2.4),
      target: vec3(0, 0.4, 0),
      fov: 42,
      note: 'Front view shows the shoulders turning from side to side over hips that stay square.',
      ...variant.camera,
    },
  };
}
