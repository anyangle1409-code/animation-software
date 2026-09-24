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
 * The trunk-flexion family: lying on the floor, knees bent and feet flat,
 * curling the trunk up.
 *
 * The thirteenth family. Two motions from the one lying position:
 *
 * * `crunch` curls only the upper back off the floor. The spine flexes 30°,
 *   most of it high in the back (lumbar 4°, mid thoracic 9.5°, upper thoracic
 *   17°), and the neck nods 15°, so the shoulders rise 12.5 cm while the lower
 *   back and the hips stay down. Split evenly between the two thoracic joints,
 *   the muscle overlay's mid-back erector belly stood 8.2 mm out of the skin,
 *   past the 7 mm the overlay allows; curled higher and a little less, it stays
 *   inside, and a crunch curls from the top of the back anyway.
 * * `situp` carries on to sitting: the whole body pitches up about the hip
 *   joint, from lying to 25° short of upright, with a lighter curl through the
 *   spine, arms reaching past the knees.
 *
 * ## Lying on the floor
 *
 * As on the bench (`families/supine.ts`), lying is tuned against the
 * production character with the floor as the pad. Pitched back 84° with the
 * pelvis joint 13.3 cm up, the upper back rests 6.5 mm into the floor, the
 * sides of the chest 8.6 mm, the buttocks sit 1.3 mm up and the lower back
 * keeps a 1 cm arch; the neck extends 15° to lay the back of the head down.
 *
 * ## The sit-up rolls onto the seat
 *
 * Turning about a hip joint held still, the back of the pelvis swung down
 * through the floor as the body came up, 20 mm at the worst. A body sitting up
 * rolls onto its sitting bones, which lifts the hip joint, so the top places it
 * at 14.7 cm and the turn is about the hip joint (`rootPivot`) on its way
 * between the two: the seat then presses at most 11 mm into the floor mid-rise
 * and rests on it at the top.
 */

export type FlexionMotion = 'crunch' | 'situp';

export interface TrunkFlexionVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  motion: FlexionMotion;
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

/** The pelvis joint's height above the root; see `families/hinge.ts`. */
const PELVIS_HEIGHT = 0.95;

/** Lying: the pelvis joint and the body's pitch back. */
const LYING = { pelvis: { y: 0.133, z: 0 }, pitch: -84 };

/** Sitting up: the body 25° short of upright, rolled onto the seat. */
const SITTING = { pelvis: { y: 0.147, z: 0 }, pitch: -25 };

/** Heels down 30 cm apart, 50 cm past the hips: knees bent about 100°. */
const FEET = { width: 0.3, toeOut: 6, forward: 0.5 };

/** Starting guesses; the planted feet decide the legs. */
const LEGS = bilateralJoints({ thigh_l: { x: 50, z: -6 }, shin_l: { x: -100 }, foot_l: { x: 0 } });

/** The curl's scale at the top: the crunch's, and the sit-up's. */
const CURL = { crunch: 38, situp: 15 };

/**
 * The trunk curled on a scale of `curl`: a tenth of it at the lumbar joint, a
 * quarter mid thoracic, nearly half upper thoracic, and the neck nodding up
 * from the 15° extension that lays the head on the floor.
 */
function trunk(curl: number) {
  return {
    pelvis: { x: 0 },
    spine_01: { x: 0.1 * curl },
    spine_02: { x: 0.25 * curl },
    spine_03: { x: 0.45 * curl },
    neck: { x: -15 + 0.4 * curl },
    head: { x: 2 },
  };
}

/**
 * Arms reaching towards the knees, raised off the floor by `reach` degrees of
 * shoulder flexion: resting along the thighs when lying, and reaching straight
 * forward past the knees at the top of a sit-up. Held 12° out from the sides:
 * at 8° the upper arm passed 0.88 mm from the chest as the sit-up came up.
 */
const arms = (reach: number) =>
  bilateralJoints({ upperarm_l: { x: reach, z: -12 }, forearm_l: { x: 8 }, hand_l: { z: 0 } });

const REACH = { lying: 20, crunch: 30, situp: 65 };

const neckRule: TechniqueRule = {
  kind: 'jointAngle',
  id: 'neck_neutral',
  label: 'Chin stays off the chest — the trunk lifts the head, the hands do not pull it',
  bone: 'neck',
  axis: 'x',
  max: 10,
  severity: 'error',
};

const CRUNCH_RULES: TechniqueRule[] = [
  {
    kind: 'stationary',
    id: 'hips_down',
    label: 'Hips stay down on the floor',
    point: { bone: 'pelvis' },
    tolerance: 0.003,
    severity: 'error',
  },
  {
    kind: 'segmentAngle',
    id: 'lower_back_down',
    label: 'Lower back stays on the floor — a crunch, not a sit-up',
    bone: 'spine_01',
    reference: 'vertical',
    min: 75,
    severity: 'error',
  },
  {
    kind: 'relativePosition',
    id: 'shoulders_lift',
    label: 'Shoulder blades curl clear of the floor',
    point: { bone: 'upperarm_l' },
    relativeTo: { bone: 'pelvis' },
    axis: 'y',
    min: 0.12,
    phases: ['top'],
    severity: 'error',
  },
  neckRule,
];

const SITUP_RULES: TechniqueRule[] = [
  {
    kind: 'stationary',
    id: 'seated',
    label: 'Hips stay on the floor, rolling onto the seat rather than lifting',
    point: { bone: 'pelvis' },
    tolerance: 0.02,
    severity: 'error',
  },
  {
    kind: 'segmentAngle',
    id: 'sits_up',
    label: 'Comes all the way up to sitting',
    bone: 'spine_02',
    reference: 'vertical',
    max: 30,
    phases: ['top'],
    severity: 'error',
  },
  {
    kind: 'segmentAngle',
    id: 'lowers_fully',
    label: 'Lowers all the way back to the floor',
    bone: 'spine_02',
    reference: 'vertical',
    min: 75,
    phases: ['bottom'],
    severity: 'error',
  },
  neckRule,
];

const CRUNCH_ERRORS: CommonError[] = [
  {
    id: 'neck_pull',
    label: 'Pulling on the neck',
    description: 'The chin drives into the chest and the head leads, straining the neck.',
    ruleId: 'neck_neutral',
    correction: 'Keep a fist of space under the chin and lift from the chest.',
  },
  {
    id: 'sitting_up',
    label: 'Coming too high',
    description: 'The lower back leaves the floor and the hip flexors take over.',
    ruleId: 'lower_back_down',
    correction: 'Curl only until the shoulder blades clear the floor.',
  },
  {
    id: 'no_curl',
    label: 'Not curling',
    description: 'The head lifts but the shoulder blades stay on the floor.',
    ruleId: 'shoulders_lift',
    correction: 'Draw the ribs towards the hips until the shoulder blades lift.',
  },
];

const SITUP_ERRORS: CommonError[] = [
  {
    id: 'neck_pull',
    label: 'Pulling on the neck',
    description: 'The head leads and the chin drives into the chest.',
    ruleId: 'neck_neutral',
    correction: 'Keep the head in line with the curl of the trunk.',
  },
  {
    id: 'half_rep',
    label: 'Stopping short',
    description: 'The trunk turns round well before sitting upright.',
    ruleId: 'sits_up',
    correction: 'Come all the way up until the chest is over the hips.',
  },
  {
    id: 'dropping',
    label: 'Dropping back',
    description: 'The trunk falls back to the floor instead of lowering under control.',
    ruleId: 'lowers_fully',
    correction: 'Lower slowly, one segment of the back at a time, all the way down.',
  },
];

export function trunkFlexionFamily(variant: TrunkFlexionVariant): ExerciseDefinition {
  const situp = variant.motion === 'situp';
  const stance = seatedStance(FEET);
  const place = (at: { pelvis: { y: number; z: number }; pitch: number }) => {
    const root = hingeRoot(at.pitch, at.pelvis);
    return { position: { y: root.y, z: root.z }, rotation: { x: at.pitch } };
  };
  const lying = place(LYING);

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'core',
    description: variant.description,

    equipment: { required: [], instances: [] },

    startPose: { label: 'Lying', joints: { ...LEGS, ...trunk(0), ...arms(REACH.lying) }, root: lying },
    peakPose: situp
      ? { label: 'Sitting up', joints: { ...LEGS, ...trunk(CURL.situp), ...arms(REACH.situp) }, root: place(SITTING) }
      : { label: 'Curled up', joints: { ...LEGS, ...trunk(CURL.crunch), ...arms(REACH.crunch) }, root: lying },
    // The sit-up turns about the hip joint rather than the root on the floor.
    ...(situp ? { rootPivot: vec3(0, PELVIS_HEIGHT, 0) } : {}),

    jointTargets: [],

    phases: [
      { id: 'concentric', label: situp ? 'Sit up' : 'Curl up', to: 'peak', easing: 'lift', contraction: 'concentric' },
      { id: 'top', label: 'Top', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'eccentric', label: 'Lower', to: 'start', easing: 'lift', contraction: 'eccentric' },
      { id: 'bottom', label: 'Bottom', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo:
      variant.tempo ??
      (situp
        ? { concentric: 1.4, pauseContracted: 0.4, eccentric: 2, pauseStretched: 0.4 }
        : { concentric: 1, pauseContracted: 0.6, eccentric: 1.4, pauseStretched: 0.4 }),

    hands: { grip: 'none', orientation: 'neutral', closure: 0.2 },
    feet: stance.feet,
    locks: stance.locks,

    muscles: situp
      ? {
          primary: ['rectus_abdominis'],
          secondary: ['obliques', 'quadriceps'],
          stabilisers: ['hip_adductors', 'erector_lower'],
          ...variant.muscles,
        }
      : {
          primary: ['rectus_abdominis'],
          secondary: ['obliques'],
          stabilisers: ['hip_adductors'],
          ...variant.muscles,
        },

    technique: [...stance.technique, ...(situp ? SITUP_RULES : CRUNCH_RULES)] satisfies TechniqueRule[],

    commonErrors: [...(situp ? SITUP_ERRORS : CRUNCH_ERRORS), ...(variant.commonErrors ?? [])],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: situp ? 'Breathe out as you sit up, in as you lower.' : 'Breathe out as you curl up, in as you lower.',
    },

    camera: {
      preset: 'right',
      position: vec3(2.4, 0.9, 0),
      target: vec3(0, 0.35, -0.15),
      fov: 42,
      note: situp
        ? 'Side view shows the trunk curling and rising to sitting over feet that stay down.'
        : 'Side view shows the shoulder blades lifting while the lower back stays on the floor.',
      ...variant.camera,
    },
  };
}
