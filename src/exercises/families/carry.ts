import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import type { TechniqueRule } from '../../constraints/types';
import type { Vec3 } from '../../rig/types';
import { vec3 } from '../../rig/types';
import { bilateralJoints, bilateralRule } from '../mirror';
import { evenSides } from '../presets';
import { BALL_HEIGHT, FOOT_LENGTH, flatFootAim, handDumbbells } from '../stance';

/**
 * The carry family: walking with a load.
 *
 * The fourteenth family, and the first that walks. It is built from the
 * forward lunge's parts — feet driven as pose-level IK targets and timed
 * within their phases (`MovementPhase.ikTiming`) — with one foot always on the
 * floor.
 *
 * ## Walking in place
 *
 * A clip that loops cannot travel: its last frame is its first, so a body that
 * walked forward would jump back. The walk is therefore in place, the way a
 * game's locomotion clip is. Each repetition is two steps. While a foot is
 * down it slides back along the floor at a constant speed (a linear blend,
 * 44 cm in each 0.6 s step: 0.733 m/s); while the other is up it swings forward
 * 6 cm off the floor. Moving the character forward at that speed
 * (`ExerciseDefinition.travel`, written into the exported file) holds each
 * planted foot still on the floor, as a treadmill does the other way round.
 *
 * * **The feet.** Each lands flat, 22 cm ahead of the hips, and leaves with its
 *   heel 15° up, pivoting on a ball that stays on the floor. Because its slide
 *   must be linear, the heel's rise is spread over the whole stance rather than
 *   left to push-off: the ball stays within 0.7 mm of the floor and, moved at
 *   the travel speed, within 1.2 mm of where it landed; the heel is a few
 *   degrees up by mid-stance.
 * * **The body.** The hips sit 4 cm lower than standing, so a leg can reach a
 *   foot 22 cm ahead and one 20 cm behind at once; they turn 4° with each
 *   stride, the chest 4° against them. The arms hang long, a heavy dumbbell in
 *   each hand, held out 12° to clear the swinging thighs.
 */

export interface CarryVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  /** Load per hand, kilograms. */
  mass?: number;
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

/** Feet hip width apart, each landing 22 cm ahead of the hips and leaving 22 cm behind. */
const FEET = { halfWidth: 0.1, halfStep: 0.22 };

/** The back foot's heel at push-off, degrees, and how high a swinging foot lifts, metres. */
const STEP = { heel: 15, lift: 0.06, seconds: 0.6 };

/** How far the hips sit below standing, metres. */
const DROP = -0.04;

/** A flat foot's ankle at `z`, or the back foot up on its ball with the heel raised. */
function foot(side: 1 | -1, z: number, heelUp: boolean) {
  const x = side * FEET.halfWidth;
  if (!heelUp) return { target: vec3(x, 0.08, z), aim: flatFootAim(0) };
  const aim = flatFootAim(0, STEP.heel);
  // The ball stays where the flat foot's was; the ankle rises about it.
  const ball = vec3(x, BALL_HEIGHT, z + 0.14);
  const d = aim.direction;
  const length = Math.hypot(d.x, d.y, d.z);
  return {
    target: vec3(x, ball.y - (d.y / length) * FOOT_LENGTH, ball.z - (d.z / length) * FOOT_LENGTH),
    aim,
  };
}

/** Each knee aimed along its foot, from 2 m ahead. */
const pole = (target: Vec3) => vec3(target.x, 1.5, target.z + 2);

/** Both feet at the moment one lands: the left ahead, or the right. */
function feet(leftAhead: boolean) {
  const left = foot(-1, leftAhead ? FEET.halfStep : -FEET.halfStep, !leftAhead);
  const right = foot(1, leftAhead ? -FEET.halfStep : FEET.halfStep, leftAhead);
  return {
    leg_l: { target: left.target, pole: pole(left.target), aim: left.aim },
    leg_r: { target: right.target, pole: pole(right.target), aim: right.aim },
  };
}

/** The body at the moment one foot lands; the legs' angles are starting guesses. */
function body(leftAhead: boolean) {
  const turn = leftAhead ? 1 : -1;
  return {
    pelvis: { x: 0, y: turn * 4 },
    spine_01: { x: 1, y: -turn * 2 },
    spine_02: { x: 0 },
    spine_03: { x: -1, y: -turn * 2 },
    neck: { x: -2 },
    thigh_l: { x: leftAhead ? 20 : -10 },
    shin_l: { x: -10 },
    thigh_r: { x: leftAhead ? -10 : 20 },
    shin_r: { x: -10 },
    ...bilateralJoints({ upperarm_l: { x: 2, z: -12 }, forearm_l: { x: 6, y: 0 }, hand_l: { z: 0 } }),
  };
}

export function carryFamily(variant: CarryVariant): ExerciseDefinition {
  const root = { position: { y: DROP, z: 0 } };

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'core',
    description: variant.description,

    equipment: { required: ['dumbbell'], instances: handDumbbells(variant.mass ?? 24) },

    startPose: { label: 'Left foot lands', joints: body(true), root, ik: feet(true) },
    peakPose: { label: 'Right foot lands', joints: body(false), root, ik: feet(false) },

    jointTargets: [],

    // One step each; the foot that is down slides back at a constant speed, the
    // other swings forward and lands as the phase ends.
    phases: [
      {
        id: 'right_step',
        label: 'Right step',
        to: 'peak',
        easing: 'easeInOut',
        contraction: 'concentric',
        duration: STEP.seconds,
        ikTiming: { leg_l: { easing: 'linear' }, leg_r: { lift: STEP.lift, easing: 'easeInOut' } },
      },
      {
        id: 'left_step',
        label: 'Left step',
        to: 'start',
        easing: 'easeInOut',
        contraction: 'concentric',
        duration: STEP.seconds,
        ikTiming: { leg_r: { easing: 'linear' }, leg_l: { lift: STEP.lift, easing: 'easeInOut' } },
      },
    ],

    // The phases carry their own durations; walking has no lowering or holds.
    tempo: variant.tempo ?? { concentric: STEP.seconds, pauseContracted: 0, eccentric: STEP.seconds, pauseStretched: 0 },

    travel: { speed: (2 * FEET.halfStep) / STEP.seconds },

    hands: { grip: 'dumbbell', orientation: 'neutral', closure: 0.9 },
    feet: { width: FEET.halfWidth * 2, toeOut: 0, planted: false },
    locks: [],

    muscles: {
      primary: ['forearm_flexors', 'trapezius_upper'],
      secondary: ['obliques', 'gluteus', 'quadriceps'],
      stabilisers: ['rectus_abdominis', 'erector_lower', 'calves', 'hip_abductors'],
      ...variant.muscles,
    },

    technique: [
      {
        kind: 'segmentAngle',
        id: 'tall',
        label: 'Walks tall — no leaning forward or to one side under the load',
        bone: 'spine_02',
        reference: 'vertical',
        max: 6,
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'hips_level',
        label: 'Hips stay level from side to side',
        bone: 'pelvis',
        axis: 'z',
        min: -4,
        max: 4,
        severity: 'error',
      },
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'shoulders_down_l',
        label: 'Left shoulder stays down — no shrugging under the load',
        bone: 'clavicle_l',
        axis: 'z',
        min: -6,
        max: 6,
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'arms_long_l',
        label: 'Left arm hangs long — the weight is carried, not curled',
        bone: 'forearm_l',
        axis: 'x',
        max: 15,
        severity: 'error',
      }),
      evenSides({
        id: 'dumbbells_level',
        label: 'Both dumbbells hang level',
        point: { bone: 'hand_l', along: 1 },
        tolerance: 0.02,
      }),
    ] satisfies TechniqueRule[],

    commonErrors: [
      {
        id: 'leaning',
        label: 'Leaning',
        description: 'The trunk tips forward or to one side under the weight.',
        ruleId: 'tall',
        correction: 'Stand tall, ribs down, and let the weights hang straight from the shoulders.',
      },
      {
        id: 'shrugging',
        label: 'Shrugging',
        description: 'The shoulders creep up towards the ears as the grip tires.',
        ruleId: 'shoulders_down_l',
        correction: 'Pull the shoulders down and back and keep them there.',
      },
      {
        id: 'hip_drop',
        label: 'Hips dropping',
        description: 'The hip on the swinging side sags with each step.',
        ruleId: 'hips_level',
        correction: 'Brace the trunk and squeeze the glute of the standing leg.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Brace before you lift the weights, then breathe steadily behind the brace as you walk.',
    },

    camera: {
      preset: 'right',
      position: vec3(2.8, 1.1, 0.4),
      target: vec3(0, 0.9, 0),
      fov: 44,
      note: 'Side view shows the steps and the tall trunk; the clip walks in place.',
      ...variant.camera,
    },
  };
}
