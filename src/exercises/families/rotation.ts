import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import type { TechniqueRule } from '../../constraints/types';
import type { EquipmentInstance } from '../../equipment/types';
import { vec3 } from '../../rig/types';
import { withTwoHandGripWidth } from '../../equipment/library';
import { bilateralJoints, bilateralLock } from '../mirror';
import { plantedContact } from '../presets';
import { ANKLE_HEIGHT, flatFootAim, seatedStance } from '../stance';
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
 *
 * ## The cable woodchop (`setup: 'cable'`)
 *
 * Standing side-on to a cable tower on the right, the handle in both hands at
 * the high pulley, pulled down across the body to beside the left hip. The
 * hips pivot 15° over planted feet and the spine turns 35° more, from turned
 * towards the pulley to turned away; the knees sink 6 cm and the trunk bends
 * 12° into the finish. The arms are blended as joint angles rather than driven
 * by hand IK, so the handle sweeps an arc on long arms (see `CHOP_ARMS`).
 *
 * Its tower stands beside the lifter, which is where the rig's mirror-image
 * body showed: the production character performs the rig's mirror image, and
 * until world-placed equipment was reflected with it (`equipment/mirror.ts`)
 * this exercise reached away from its own pulley in the character view.
 */

export interface RotationVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  /** Seated on the floor (the Russian twist), or standing at a cable. */
  setup?: 'seated' | 'cable';
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
  if (variant.setup === 'cable') return cableChop(variant);
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

// ------------------------------------------------------------ The woodchop

/**
 * The cable woodchop's arms, degrees: the angles the arm IK solves for the two
 * grips on the handle at each end (63.2 mm apart, the handle's own spacing),
 * then blended as joint angles.
 *
 * Driven by the IK instead, the hands blended in a straight line from the
 * pulley to the far hip, which cuts inside the arc long arms sweep: mid-chop
 * the elbows bent and the handle passed in front of the face. Blended as
 * angles, the arms stay long (the grips about 60 cm from the shoulders the
 * whole way, elbows 17–31°) and the handle swings out 57 cm in front of the
 * chest half way down.
 *
 * The price is that the two hands are no longer held exactly on the handle
 * between the ends. The finish was chosen to keep that small: with both elbows
 * ending nearly as bent (31° and 29°) the grips open to 73 mm and close to
 * 62 mm, so each hand stays within 5.1 mm of its grip. Finishing with the
 * right elbow at 53° instead, the drift was three times as large.
 *
 * Top: the handle up towards the pulley, 1.78 m high and 33 cm to the right.
 * Finish: beside the left hip, 88 cm high.
 */
const CHOP_ARMS = {
  top: {
    upperarm_l: { x: 116.13, y: 7.49, z: 16.16 },
    upperarm_r: { x: 115.81, y: 6.7, z: -15.34 },
    forearm_l: { x: 24.71, y: 0 },
    forearm_r: { x: 16.56, y: 0 },
    hand_l: { x: 0, z: 0 },
    hand_r: { x: 0, z: 0 },
  },
  finish: {
    upperarm_l: { x: 41.97, y: -71.09, z: 0 },
    upperarm_r: { x: 26.8, y: -40.89, z: -26.62 },
    forearm_l: { x: 31.38, y: 0 },
    forearm_r: { x: 28.51, y: 0 },
    hand_l: { x: 0, z: 0 },
    hand_r: { x: 0, z: 0 },
  },
};

/**
 * Hips and trunk turned to one side: +1 towards the pulley (right), -1 away.
 * The hips turn 15° over planted feet, the spine 35° more, the head 10°. The
 * finish also bends forward 12° through the spine as the handle comes low.
 */
function chopTrunk(side: 1 | -1, bend: number) {
  return {
    pelvis: { x: 0, y: side * 15 },
    spine_01: { x: bend / 3, y: side * 8 },
    spine_02: { x: bend / 3, y: side * 12 },
    spine_03: { x: bend / 3, y: side * 15 },
    neck: { x: 0, y: side * 10 },
  };
}

/** Where the tower stands: to the right and a little ahead, turned to face across. */
const TOWER = vec3(0.95, 0, 0.35);

function chopStation(): EquipmentInstance[] {
  const still = { position: vec3(0, 0, 0), rotation: vec3(0, 0, 0), visible: true };
  const handle: EquipmentInstance = {
    id: 'handle',
    kind: 'cable_handle',
    label: 'Cable handle',
    mass: 1,
    ...still,
    attachment: { mode: 'hands', leftSocket: 'grip_l', rightSocket: 'grip_r', gripRoll: 90 },
  };
  return [
    {
      id: 'tower',
      kind: 'cable_tower',
      label: 'Cable tower',
      mass: 0,
      ...still,
      position: TOWER,
      rotation: vec3(0, -90, 0),
      attachment: { mode: 'static' },
    },
    withTwoHandGripWidth(handle, null),
    {
      id: 'cable',
      kind: 'cable',
      label: 'Cable',
      mass: 0,
      ...still,
      attachment: { mode: 'cable', from: { equipment: 'tower', socket: 'pulley' }, to: { equipment: 'handle', socket: 'clip' } },
    },
  ];
}

/**
 * Feet planted 50 cm apart and turned out 8°, pinned flat where they stand
 * rather than held from the opening frame. The chop opens with the hips
 * already turned 15°, and a foot held from there stood turned with them, its
 * toe off the floor, then dipped 5 cm through it as the hips came round. Pinned,
 * the hips turn over still feet, the thighs taking the turn, and each knee
 * points out along its foot (a pole 2 m ahead and 1.5 m up), since a leg this
 * straight has no bend of its own to follow.
 */
function chopStance() {
  const width = 0.5;
  const toeOut = 8;
  const turn = (toeOut * Math.PI) / 180;
  return {
    feet: { width, toeOut, planted: true },
    locks: bilateralLock({
      id: 'foot_l',
      chain: 'leg_l',
      mode: 'floor',
      position: vec3(-width / 2, ANKLE_HEIGHT, 0),
      aim: flatFootAim(toeOut),
      pole: vec3(-width / 2 - 2 * Math.sin(turn), 1.5, 2 * Math.cos(turn)),
      enabled: true,
    }),
    technique: plantedContact({ point: { bone: 'foot_l' }, tolerance: 0.012, label: 'Left foot stays planted' }),
  };
}

function cableChop(variant: RotationVariant): ExerciseDefinition {
  const stance = chopStance();
  const bend = 12;
  // Sinking 6 cm and sitting back 3 cm into the finish.
  const finishRoot = { position: { y: -0.06, z: -0.03 } };

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'core',
    description: variant.description,

    equipment: { required: ['cable_tower', 'cable_handle', 'cable'], instances: chopStation() },

    // Knees soft from the start: standing tall, the legs could not reach feet
    // pinned this wide, and the ankles hung 1.6 cm above the floor.
    startPose: {
      label: 'Reaching up to the pulley',
      joints: { ...CHOP_ARMS.top, ...chopTrunk(1, 0) },
      root: { position: { y: -0.025 } },
    },
    peakPose: {
      label: 'Chopped down across the body',
      joints: { ...CHOP_ARMS.finish, ...chopTrunk(-1, bend) },
      root: finishRoot,
    },

    jointTargets: [],

    phases: [
      { id: 'chop', label: 'Chop', to: 'peak', easing: 'lift', contraction: 'concentric' },
      { id: 'finish', label: 'Finish', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'return', label: 'Return', to: 'start', easing: 'lift', contraction: 'eccentric' },
      { id: 'reach', label: 'Reach', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { concentric: 1, pauseContracted: 0.3, eccentric: 1.6, pauseStretched: 0.4 },

    hands: { grip: 'handle', orientation: 'neutral', closure: 0.85 },
    feet: stance.feet,
    locks: stance.locks,

    muscles: {
      primary: ['obliques'],
      secondary: ['rectus_abdominis', 'latissimus', 'deltoid_anterior'],
      stabilisers: ['gluteus', 'erector_lower', 'quadriceps', 'hip_abductors'],
      ...variant.muscles,
    },

    technique: [
      ...stance.technique,
      ...(['l', 'r'] as const).map((side): TechniqueRule => ({
        kind: 'jointAngle',
        id: `arms_long_${side}`,
        label: `${side === 'l' ? 'Left' : 'Right'} arm stays long — the trunk moves the handle, not the arms`,
        bone: `forearm_${side}`,
        axis: 'x',
        max: 40,
        severity: 'error',
      })),
      {
        kind: 'jointAngle',
        id: 'full_turn_start',
        label: 'Turns fully towards the pulley to reach for the handle',
        bone: 'spine_03',
        axis: 'y',
        min: 12,
        phases: ['reach'],
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'full_turn_finish',
        label: 'Turns fully through to the far side at the finish',
        bone: 'spine_03',
        axis: 'y',
        max: -12,
        phases: ['finish'],
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'hips_pivot',
        label: 'Hips turn with the trunk at the finish rather than the spine wringing alone',
        bone: 'pelvis',
        axis: 'y',
        max: -10,
        phases: ['finish'],
        severity: 'error',
      },
      {
        kind: 'relativePosition',
        id: 'chops_low',
        label: 'The handle finishes low, beside the far hip',
        point: { bone: 'hand_l', along: 1 },
        relativeTo: { bone: 'pelvis' },
        axis: 'y',
        max: 0.1,
        phases: ['finish'],
        severity: 'error',
      },
      {
        kind: 'segmentAngle',
        id: 'chest_up',
        label: 'Chest stays up — bending at the hips, not folding over',
        bone: 'spine_02',
        reference: 'vertical',
        max: 25,
        severity: 'error',
      },
    ] satisfies TechniqueRule[],

    commonErrors: [
      {
        id: 'arm_pull',
        label: 'Pulling with the arms',
        description: 'The elbows bend and the arms drag the handle down while the trunk barely turns.',
        ruleId: 'arms_long_r',
        correction: 'Keep the arms long and let the hips and trunk turn the handle down.',
      },
      {
        id: 'short_turn',
        label: 'Stopping short',
        description: 'The handle stops in front of the body instead of finishing beside the far hip.',
        ruleId: 'full_turn_finish',
        correction: 'Turn all the way through, chest to the far side.',
      },
      {
        id: 'locked_hips',
        label: 'Locked hips',
        description: 'The hips stay square and the lower back twists alone.',
        ruleId: 'hips_pivot',
        correction: 'Let the hips turn with the chop, knees soft.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe out as you chop down, in as the handle returns.',
    },

    camera: {
      preset: 'front',
      position: vec3(0.4, 1.4, 3.2),
      target: vec3(0.1, 1.1, 0.2),
      fov: 46,
      note: 'Front view shows the handle travelling from the pulley down across the body as the hips and trunk turn.',
      ...variant.camera,
    },
  };
}
