import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  PoseSpec,
  Tempo,
} from '../types';
import type { TechniqueRule } from '../../constraints/types';
import type { EquipmentInstance } from '../../equipment/types';
import type { Vec3 } from '../../rig/types';
import { vec3 } from '../../rig/types';
import { bilateralJoints, bilateralRule } from '../mirror';
import { evenSides } from '../presets';
import { handDumbbells, seatedStance } from '../stance';
import { hingeRoot } from './hinge';

/**
 * The supine family: lying face up on a flat bench, feet flat on the floor,
 * moving a dumbbell in each hand over the chest.
 *
 * The eleventh family, and the first lying down. The body does not move at
 * all: the bench holds it, and the arms work over it. Two motions share the
 * one set-up:
 *
 * * `press` lowers the dumbbells to the sides of the chest, forearms vertical,
 *   elbows angled towards the hips, and presses them back up over the
 *   shoulders. The hands follow a line, so they are driven by pose-level IK
 *   targets (`PoseSpec.ik`), as the Pallof press's are.
 * * `fly` opens the arms wide on a soft, fixed elbow and sweeps them back
 *   together, a shoulder swing with the elbow held still. That is a joint
 *   motion rather than a hand path, so it is authored in joint angles, as the
 *   lateral raise is. It has to be: a fly holds the palms facing each other,
 *   which needs the forearm turned, and the arm IK solves the elbow as a plain
 *   hinge and leaves the forearm's twist at zero.
 *
 * ## Lying on the bench
 *
 * The root is pitched back 84.3° rather than 90°, head end up, and the pelvis
 * joint sits 59.8 cm off the floor. Both were tuned against the production
 * character, pad by pad, the way the seated press's seat height was. Lying
 * dead flat, the upper back sank 45 mm into the pad while the hips sank 22 mm:
 * the character's back is thicker at the shoulder blades than at the buttocks,
 * measured from the spine. Tilted, the upper back, hips and the back of the
 * head all rest on the pad together (deepest 13.7 mm, under the hamstrings'
 * origin, against the 15 mm compression limit), and the lower back keeps its
 * small natural arch clear of it. The tilt lifts the head too, so the neck
 * extends 16° to lay it back on the bench, with the head itself nodding 2° to
 * keep the face to the ceiling.
 *
 * The bench is turned so its head end is under the head, and its foot end
 * reaches 17.5 cm past the hip joints, under the glutes. The feet are planted
 * 42 cm apart and 50 cm past the hips, the knees bent about 65°.
 */

export type SupineMotion = 'press' | 'fly';

export interface SupineVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  motion: SupineMotion;
  /** Load per hand, kilograms. */
  mass?: number;
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

/** The pelvis joint, lying, and the body's pitch (negative lies back). */
const LYING = { pelvis: { y: 0.598, z: 0 }, pitch: -84.3 };

/** The bench's centre: its foot end 17.5 cm past the hips. */
const BENCH = vec3(0, 0, -0.45);

const FEET = { width: 0.42, toeOut: 10, forward: 0.5 };

const TRUNK = {
  pelvis: { x: 0 },
  spine_01: { x: 0 },
  spine_02: { x: 0 },
  spine_03: { x: 0 },
  neck: { x: -16 },
  head: { x: 2 },
};

/** Starting guesses; the planted feet decide the legs. */
const LEGS = bilateralJoints({ thigh_l: { x: -8, z: -8 }, shin_l: { x: -85 }, foot_l: { x: 0 } });

/**
 * Press: left wrist targets, metres. At the top, 55.6 cm above the shoulder
 * and a touch towards the feet, which leaves the elbow 11.5° short of locked.
 * At the bottom, 104° of elbow under a forearm 6° from vertical: the elbow
 * 6 cm below the shoulder and 14.4 cm towards the hips, an upper arm about 60°
 * out from the trunk rather than flared to 90°, and the handle 29 cm above the
 * shoulder, beside the chest.
 */
const PRESS = { top: vec3(-0.19, 1.168, -0.46), bottom: vec3(-0.436, 0.81, -0.331) };

/** Elbows out, a little down and towards the feet. */
const PRESS_POLE = vec3(-0.9, 0.45, -0.1);

/**
 * The press's arm pose under the IK. The solve replaces the upper arm and
 * forearm; the hand stays straight on the forearm, which with the forearm
 * untwisted leaves the palms facing the feet — the pronated press grip, the
 * handles turned 31° from straight across at either end and 42° mid-press,
 * inner ends towards the head. That is the elbow's hinge plane, which tilts
 * with the upper arm; a lifter who wanted them dead straight would turn the
 * forearm, which the arm IK does not.
 */
const PRESS_ARMS = bilateralJoints({
  upperarm_l: { x: 90, z: -30 },
  forearm_l: { x: 60 },
  hand_l: { z: 0 },
});

/**
 * Fly: the upper arm swings about the one axis, z, from 10° off vertical to 2°
 * below level, held flexed 88° and turned in. Held that way, it sweeps across
 * the chest's own plane, over the nipple line; with the swing split between
 * flexion and abduction instead, the dumbbells drifted 22 cm towards the hips
 * half way out and came back. The forearm is turned 80° so the palms face each
 * other at the top and the ceiling at the bottom, the handles lying along the
 * body throughout (within 11°). The turn-in eases from 90° at the top to 70°
 * at the bottom, which keeps them there; held at 90° they tipped 17°.
 */
const FLY = {
  top: vec3(88, -90, -6),
  bottom: vec3(88, -70, -92),
};

/** A soft elbow, fixed for the whole repetition. */
const FLY_ELBOW = 20;

const flyArms = (upper: Vec3) =>
  bilateralJoints({
    upperarm_l: upper,
    forearm_l: { x: FLY_ELBOW, y: 80 },
    hand_l: { z: 0 },
  });

const mirror = (point: Vec3) => vec3(-point.x, point.y, point.z);

function pressIK(hand: Vec3) {
  return {
    arm_l: { target: hand, pole: PRESS_POLE },
    arm_r: { target: mirror(hand), pole: mirror(PRESS_POLE) },
  };
}

function bench(): EquipmentInstance {
  return {
    id: 'bench',
    kind: 'flat_bench',
    label: 'Flat bench',
    mass: 0,
    position: BENCH,
    // Head end under the head.
    rotation: vec3(0, 180, 0),
    visible: true,
    supportsBody: true,
    attachment: { mode: 'static' },
  };
}

function poses(motion: SupineMotion): { start: PoseSpec; peak: PoseSpec } {
  const root = hingeRoot(LYING.pitch, LYING.pelvis);
  const lying = { position: { y: root.y, z: root.z }, rotation: { x: LYING.pitch } };
  const body = { ...TRUNK, ...LEGS };
  if (motion === 'fly') {
    return {
      start: { label: 'Arms over the chest', joints: { ...body, ...flyArms(FLY.top) }, root: lying },
      peak: { label: 'Arms open', joints: { ...body, ...flyArms(FLY.bottom) }, root: lying },
    };
  }
  return {
    start: { label: 'Arms extended', joints: { ...body, ...PRESS_ARMS }, root: lying, ik: pressIK(PRESS.top) },
    peak: { label: 'At the chest', joints: { ...body, ...PRESS_ARMS }, root: lying, ik: pressIK(PRESS.bottom) },
  };
}

const hipsDown: TechniqueRule = {
  kind: 'stationary',
  id: 'hips_on_bench',
  label: 'Hips stay down on the bench',
  point: { bone: 'pelvis' },
  tolerance: 0.005,
  severity: 'error',
};

const level = evenSides({
  id: 'dumbbells_level',
  label: 'Both dumbbells move level with one another',
  point: { bone: 'hand_l', along: 1 },
  tolerance: 0.03,
});

const PRESS_RULES: TechniqueRule[] = [
  ...bilateralRule({
    kind: 'relativePosition',
    id: 'press_depth_l',
    label: 'Left dumbbell lowers to the side of the chest',
    point: { bone: 'hand_l', along: 1 },
    relativeTo: { bone: 'upperarm_l' },
    axis: 'y',
    max: 0.33,
    phases: ['bottom'],
    severity: 'error',
  }),
  ...bilateralRule({
    kind: 'segmentAngle',
    id: 'forearm_vertical_l',
    label: 'Left forearm stands vertical under the dumbbell at the bottom',
    bone: 'forearm_l',
    reference: 'vertical',
    max: 15,
    phases: ['bottom'],
    severity: 'error',
  }),
  ...bilateralRule({
    kind: 'relativePosition',
    id: 'elbow_tuck_l',
    label: 'Left elbow angles towards the hips, not flared straight out',
    point: { bone: 'forearm_l' },
    relativeTo: { bone: 'upperarm_l' },
    axis: 'z',
    min: 0.06,
    phases: ['bottom'],
    severity: 'error',
  }),
  ...bilateralRule({
    kind: 'jointAngle',
    id: 'full_press_l',
    label: 'Left arm presses to near straight',
    bone: 'forearm_l',
    axis: 'x',
    max: 20,
    phases: ['top'],
    severity: 'error',
  }),
  ...bilateralRule({
    kind: 'jointAngle',
    id: 'soft_lockout_l',
    label: 'Left elbow stops short of snapping locked',
    bone: 'forearm_l',
    axis: 'x',
    min: 5,
    severity: 'error',
  }),
  ...bilateralRule({
    kind: 'relativePosition',
    id: 'over_shoulders_l',
    label: 'Left dumbbell finishes over the shoulder, not the face or the stomach',
    point: { bone: 'hand_l', along: 1 },
    relativeTo: { bone: 'upperarm_l' },
    axis: 'z',
    min: -0.05,
    max: 0.1,
    phases: ['top'],
    severity: 'error',
  }),
];

const FLY_RULES: TechniqueRule[] = [
  ...bilateralRule({
    kind: 'jointAngle',
    id: 'fixed_elbow_l',
    label: 'Left elbow stays softly bent and fixed — not pressing, not locked',
    bone: 'forearm_l',
    axis: 'x',
    min: 10,
    max: 30,
    severity: 'error',
  }),
  ...bilateralRule({
    kind: 'segmentAngle',
    id: 'fly_depth_l',
    label: 'Left arm opens until the upper arm is level with the chest',
    bone: 'upperarm_l',
    reference: 'vertical',
    min: 80,
    phases: ['bottom'],
    severity: 'error',
  }),
  ...bilateralRule({
    kind: 'relativePosition',
    id: 'not_too_deep_l',
    label: 'Left dumbbell never drops below the shoulder',
    point: { bone: 'hand_l', along: 1 },
    relativeTo: { bone: 'upperarm_l' },
    axis: 'y',
    min: 0,
    severity: 'error',
  }),
  ...bilateralRule({
    kind: 'relativePosition',
    id: 'fly_line_l',
    label: 'Left arm sweeps across the chest, not towards the head or the hips',
    point: { bone: 'hand_l', along: 1 },
    relativeTo: { bone: 'upperarm_l' },
    axis: 'z',
    min: -0.08,
    max: 0.12,
    severity: 'error',
  }),
];

const PRESS_ERRORS: CommonError[] = [
  {
    id: 'flaring',
    label: 'Elbows flared',
    description: 'The elbows point straight out from the shoulders at the bottom, loading the front of the shoulder joint.',
    ruleId: 'elbow_tuck_l',
    correction: 'Angle the elbows about 45–60° from the body, towards the hips.',
  },
  {
    id: 'half_reps',
    label: 'Stopping short',
    description: 'The dumbbells turn around well above the chest.',
    ruleId: 'press_depth_l',
    correction: 'Lower until the dumbbells are beside the chest, then press.',
  },
  {
    id: 'hips_up',
    label: 'Lifting the hips',
    description: 'The hips come off the bench to drive the press.',
    ruleId: 'hips_on_bench',
    correction: 'Keep the glutes on the bench and push through the feet without bridging.',
  },
];

const FLY_ERRORS: CommonError[] = [
  {
    id: 'pressing',
    label: 'Turning it into a press',
    description: 'The elbows bend more on the way down and straighten on the way up, so the triceps take the work.',
    ruleId: 'fixed_elbow_l',
    correction: 'Fix a soft bend in the elbow and keep it; only the shoulder moves.',
  },
  {
    id: 'too_deep',
    label: 'Opening too far',
    description: 'The dumbbells sink below the shoulders, stretching the front of the shoulder under load.',
    ruleId: 'not_too_deep_l',
    correction: 'Stop when the upper arms are level with the chest.',
  },
  {
    id: 'hips_up',
    label: 'Lifting the hips',
    description: 'The hips come off the bench as the arms open.',
    ruleId: 'hips_on_bench',
    correction: 'Keep the glutes on the bench and the feet flat.',
  },
];

export function supineFamily(variant: SupineVariant): ExerciseDefinition {
  const fly = variant.motion === 'fly';
  const stance = seatedStance(FEET);
  const { start, peak } = poses(variant.motion);

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'upper_push',
    description: variant.description,

    equipment: {
      required: ['dumbbell', 'flat_bench'],
      instances: [...handDumbbells(variant.mass ?? (fly ? 10 : 16)), bench()],
    },

    startPose: start,
    peakPose: peak,

    jointTargets: [],

    phases: [
      { id: 'eccentric', label: fly ? 'Open' : 'Lower', to: 'peak', easing: 'lift', contraction: 'eccentric' },
      { id: 'bottom', label: 'Bottom', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'concentric', label: fly ? 'Close' : 'Press', to: 'start', easing: 'lift', contraction: 'concentric' },
      { id: 'top', label: 'Top', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo:
      variant.tempo ??
      (fly
        ? { eccentric: 2.2, pauseStretched: 0.4, concentric: 1.6, pauseContracted: 0.5 }
        : { eccentric: 2, pauseStretched: 0.4, concentric: 1.2, pauseContracted: 0.5 }),

    hands: { grip: 'dumbbell', orientation: fly ? 'neutral' : 'pronated', closure: 0.85 },
    feet: stance.feet,
    locks: stance.locks,

    muscles: fly
      ? {
          primary: ['pectoralis'],
          secondary: ['deltoid_anterior'],
          stabilisers: ['biceps', 'rectus_abdominis', 'gluteus'],
          ...variant.muscles,
        }
      : {
          primary: ['pectoralis'],
          secondary: ['deltoid_anterior', 'triceps'],
          stabilisers: ['deltoid_posterior', 'latissimus', 'rectus_abdominis', 'gluteus'],
          ...variant.muscles,
        },

    technique: [...stance.technique, hipsDown, level, ...(fly ? FLY_RULES : PRESS_RULES)] satisfies TechniqueRule[],

    commonErrors: [...(fly ? FLY_ERRORS : PRESS_ERRORS), ...(variant.commonErrors ?? [])],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: fly
        ? 'Breathe in as the arms open, out as they sweep back together.'
        : 'Breathe in as the dumbbells lower, out as you press.',
    },

    camera: fly
      ? {
          preset: 'front',
          position: vec3(0.8, 1.7, 2.4),
          target: vec3(0, 0.75, -0.35),
          fov: 44,
          note: 'View from the feet shows both arms opening wide and sweeping back together over the chest.',
          ...variant.camera,
        }
      : {
          preset: 'right',
          position: vec3(2.6, 1.2, -0.3),
          target: vec3(0, 0.75, -0.35),
          fov: 42,
          note: 'Side view shows the dumbbells travelling from the chest to over the shoulders, and the body staying on the bench.',
          ...variant.camera,
        },
  };
}
