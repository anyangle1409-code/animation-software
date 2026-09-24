import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import type { TechniqueRule } from '../../constraints/types';
import type { EquipmentInstance } from '../../equipment/types';
import type { Vec3 } from '../../rig/types';
import { vec3 } from '../../rig/types';
import { withTwoHandGripWidth } from '../../equipment/library';
import { bilateralJoints, bilateralRule } from '../mirror';
import { plantedStance } from '../stance';

/**
 * The anti-rotation family: the trunk holding still against a pull that would
 * twist it.
 *
 * The tenth family, and the first whose prime movers produce no visible motion.
 * The lifter stands side-on to a cable at chest height and presses the handle
 * straight out from the sternum; the further the arms reach, the longer the
 * cable's lever on the trunk, and the obliques and deep abdominals hold the hips
 * and shoulders square against it. What the animation has to show is the
 * absence of rotation while the arms move.
 *
 * ## The arms follow a line, not a pose
 *
 * The press is a straight line from the sternum outwards, the hands clasped
 * together on one handle. Both hands are driven by pose-level IK targets
 * (`PoseSpec.ik`), which the clip blends in a straight line between the chest
 * and full reach; the handle is held in both hands (`hands`), one above the
 * other, and so follows the hands exactly. The elbows are free to settle where
 * the arm solve puts them, pointing down and out.
 *
 * The cable runs from the tower's chest-height pulley to the handle's clip,
 * which is rolled to face it.
 */

export interface AntiRotationVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  /** Which side the cable pulls from. */
  side?: 'left' | 'right';
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

/**
 * Wrist targets, metres, for the upper (left) and lower (right) hand at the
 * chest and at full reach. They are solved, not chosen: each is the wrist
 * position that puts that hand's grip centre on the handle, the fists
 * interlocked one above the other on the midline (grips at y 1.20 and 1.14),
 * 17 cm forward at the chest, the upper grip 2 cm ahead of the lower. The grip centre sits 9 cm along the
 * hand from the wrist, and which way depends on how the hand ends up turned, so
 * the targets were found by moving each wrist by its grip's error until it
 * closed (0.01 mm).
 *
 * The handle tips forward a little, the upper grip 2 cm ahead, all the way.
 * At full reach (51 cm out) the upper hand sits nearer its shoulder, and with
 * both grips at one depth its elbow stayed bent 34° while the lower arm locked;
 * tipped, the elbows finish at 21° and 10° — long arms, soft elbows. At the
 * chest the tip keeps the handle turned the same way: held exactly upright, its
 * grip axis is vertical, and a two-hand item's roll is measured from the
 * vertical, so the handle spun a quarter turn over the press. At 52 cm the
 * lower hand runs out of reach.
 */
const HANDS = {
  chest: { upper: vec3(-0.0851, 1.1972, 0.1556), lower: vec3(0.0853, 1.1513, 0.1389) },
  reach: { upper: vec3(-0.0519, 1.23, 0.4548), lower: vec3(0.0473, 1.1839, 0.4393) },
};

/** Elbows down and out. */
const POLES = { upper: vec3(-0.7, 0.6, 0), lower: vec3(0.7, 0.6, 0) };

/** How far to the side the tower stands, metres. */
const TOWER_OFFSET = 0.9;

const BRACED = {
  pelvis: { x: 0 },
  spine_01: { x: 1 },
  spine_02: { x: 0 },
  spine_03: { x: -1 },
  neck: { x: -2 },
};

const ARMS = bilateralJoints({ upperarm_l: { x: 30, z: -20 }, forearm_l: { x: 90, y: 0 }, hand_l: { z: 0 } });

function station(side: 'left' | 'right'): EquipmentInstance[] {
  const still = { position: vec3(0, 0, 0), rotation: vec3(0, 0, 0), visible: true };
  const sign = side === 'left' ? -1 : 1;
  const handle: EquipmentInstance = {
    id: 'handle',
    kind: 'cable_handle',
    label: 'Cable handle',
    mass: 1,
    ...still,
    // Held upright in both hands; its clip is turned round to face the pulley.
    attachment: { mode: 'hands', leftSocket: 'grip_l', rightSocket: 'grip_r', gripRoll: side === 'left' ? 270 : 90 },
  };
  return [
    {
      id: 'tower',
      kind: 'cable_tower',
      label: 'Cable tower',
      mass: 0,
      ...still,
      // Turned to face the lifter from the side.
      position: vec3(sign * TOWER_OFFSET, 0, 0),
      rotation: vec3(0, -sign * 90, 0),
      attachment: { mode: 'static' },
    },
    withTwoHandGripWidth(handle, null),
    {
      id: 'cable',
      kind: 'cable',
      label: 'Cable',
      mass: 0,
      ...still,
      attachment: {
        mode: 'cable',
        from: { equipment: 'tower', socket: 'pulley_mid' },
        to: { equipment: 'handle', socket: 'clip' },
      },
    },
  ];
}

function ik(hands: { upper: Vec3; lower: Vec3 }) {
  return {
    arm_l: { target: hands.upper, pole: POLES.upper },
    arm_r: { target: hands.lower, pole: POLES.lower },
  };
}

export function antiRotationFamily(variant: AntiRotationVariant): ExerciseDefinition {
  const side = variant.side ?? 'left';
  const stance = plantedStance({ width: 0.36 });

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'core',
    description: variant.description,

    equipment: { required: ['cable_tower', 'cable_handle', 'cable'], instances: station(side) },

    startPose: { label: 'At the chest', joints: { ...BRACED, ...ARMS }, ik: ik(HANDS.chest) },
    peakPose: { label: 'Arms extended', joints: { ...BRACED, ...ARMS }, ik: ik(HANDS.reach) },

    jointTargets: [],

    phases: [
      { id: 'press', label: 'Press out', to: 'peak', easing: 'lift', contraction: 'concentric' },
      { id: 'hold', label: 'Hold', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'return', label: 'Return', to: 'start', easing: 'lift', contraction: 'eccentric' },
      { id: 'reset', label: 'Reset', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { concentric: 1.2, pauseContracted: 2, eccentric: 1.4, pauseStretched: 0.6 },

    hands: { grip: 'handle', orientation: 'neutral', closure: 0.85 },
    feet: stance.feet,
    locks: stance.locks,

    muscles: {
      primary: ['obliques', 'rectus_abdominis'],
      secondary: ['deltoid_anterior', 'pectoralis', 'triceps'],
      stabilisers: ['gluteus', 'hip_abductors', 'erector_lower', 'latissimus'],
      ...variant.muscles,
    },

    technique: [
      ...stance.technique,
      // The point of the exercise: nothing turns towards the cable.
      {
        kind: 'jointAngle',
        id: 'hips_square',
        label: 'Hips stay square to the front, not turned towards the cable',
        bone: 'pelvis',
        axis: 'y',
        min: -3,
        max: 3,
        severity: 'error',
      },
      ...(['spine_01', 'spine_02', 'spine_03'] as const).map((bone): TechniqueRule => ({
        kind: 'jointAngle',
        id: `no_twist_${bone}`,
        label: 'Trunk does not twist towards the cable',
        bone,
        axis: 'y',
        min: -3,
        max: 3,
        severity: 'error',
      })),
      {
        kind: 'segmentAngle',
        id: 'torso_upright',
        label: 'Torso stays tall, not leaning away from the cable',
        bone: 'spine_02',
        reference: 'vertical',
        max: 5,
        severity: 'error',
      },
      // The hands press straight out along the midline.
      {
        kind: 'relativePosition',
        id: 'press_midline',
        label: 'Hands press straight out from the sternum, not drifting to the cable',
        point: { bone: 'hand_l', along: 1 },
        relativeTo: { bone: 'spine_03' },
        axis: 'x',
        min: -0.08,
        max: 0.08,
        severity: 'error',
      },
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'arms_long_l',
        label: 'Left arm reaches long at the hold',
        bone: 'forearm_l',
        axis: 'x',
        max: 30,
        phases: ['hold'],
        severity: 'error',
      }),
    ] satisfies TechniqueRule[],

    commonErrors: [
      {
        id: 'rotating',
        label: 'Turning towards the cable',
        description: 'The hips and shoulders rotate towards the stack as the arms press out.',
        ruleId: 'hips_square',
        correction: 'Brace the trunk and keep the belt buckle and chest facing forward.',
      },
      {
        id: 'drifting',
        label: 'Hands drifting towards the stack',
        description: 'The handle is pulled off the midline instead of held in front of the sternum.',
        ruleId: 'press_midline',
        correction: 'Press straight out and hold the handle in line with the sternum.',
      },
      {
        id: 'leaning',
        label: 'Leaning away',
        description: 'The trunk tilts away from the cable to counterbalance it.',
        ruleId: 'torso_upright',
        correction: 'Stand tall, feet a little wider, and resist through the obliques.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe out as you press, keep breathing through the hold, in as the handle returns.',
    },

    camera: {
      preset: 'front',
      position: vec3(0.6, 1.5, 3),
      target: vec3(-0.3, 1.1, 0.2),
      fov: 44,
      note: 'Front view shows the hips and shoulders staying square while the cable pulls from the side.',
      ...variant.camera,
    },
  };
}
