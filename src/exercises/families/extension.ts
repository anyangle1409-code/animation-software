import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import { vec3 } from '../../rig/types';
import { bilateralJointTarget, bilateralJoints, bilateralRule } from '../mirror';
import { evenSides } from '../presets';
import { handDumbbells, plantedStance } from '../stance';

/**
 * The elbow-extension family: the triceps.
 *
 * The sixth family, and the curl turned inside out. A curl flexes the elbow
 * against a load hanging from it; an extension straightens the elbow against a
 * load that wants to fold it. The reference variant does it overhead, which is
 * what makes it a family rather than a curl with the sign changed: with the
 * upper arm pointing at the ceiling, the forearm folds *behind the head*, and
 * the triceps' long head, which crosses the shoulder, is stretched as far as it
 * goes.
 *
 * ## What it asks that nothing before it did
 *
 * The load travels past the head. Every other exercise keeps its equipment in
 * front of the body or beside it; this one lowers two dumbbells into the space
 * behind the skull and the neck, so the clearance gate measuring the head
 * (`spine006` on the production character) is what decides the range, not the
 * joint limit.
 *
 * The upper arm is the thing that has to stay still, as in the curl: the elbow
 * points up and in, and the shoulder does not help by swinging the arm forward
 * as the weight comes up.
 */

export interface ExtensionVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  /** Load per hand, kilograms. */
  mass?: number;
  /** Elbow flexion at lockout and at the stretch, degrees. */
  elbow?: { start: number; peak: number };
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

/** Nearly locked out overhead, down to the forearm folded behind the head. */
const ELBOW = { start: 8, peak: 120 };

/** The upper arm points up at the ceiling and stays there. */
const UPPER_ARM = { flexion: 172, abduction: 5 };

const BRACED = {
  pelvis: { x: 2 },
  spine_01: { x: 2 },
  spine_02: { x: -1 },
  spine_03: { x: -1 },
  neck: { x: 4 },
};

export function extensionFamily(variant: ExtensionVariant): ExerciseDefinition {
  const elbow = variant.elbow ?? ELBOW;
  const stance = plantedStance();
  const arms = (flexion: number) =>
    bilateralJoints({
      upperarm_l: { x: UPPER_ARM.flexion, z: -UPPER_ARM.abduction },
      forearm_l: { x: flexion, y: 2 },
      hand_l: { z: 0 },
    });

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'arms',
    description: variant.description,

    equipment: { required: ['dumbbell'], instances: handDumbbells(variant.mass ?? 8) },

    startPose: { label: 'Locked out', joints: { ...BRACED, ...arms(elbow.start) } },
    peakPose: { label: 'Behind the head', joints: { ...BRACED, ...arms(elbow.peak) } },

    jointTargets: [
      ...bilateralJointTarget({
        bone: 'forearm_l', axis: 'x', start: elbow.start, peak: elbow.peak, role: 'prime',
        range: { min: 0, max: 135 },
      }),
      ...bilateralJointTarget({
        bone: 'upperarm_l', axis: 'x', start: UPPER_ARM.flexion, peak: UPPER_ARM.flexion, role: 'stabilise',
      }),
    ],

    phases: [
      { id: 'eccentric', label: 'Lower behind the head', to: 'peak', easing: 'lift', contraction: 'eccentric' },
      { id: 'stretch', label: 'Stretch', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'concentric', label: 'Extend', to: 'start', easing: 'lift', contraction: 'concentric' },
      { id: 'lockout', label: 'Lockout', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { eccentric: 2.2, pauseStretched: 0.4, concentric: 1.4, pauseContracted: 0.5 },

    // Palms facing, which keeps the elbows pointing forward rather than flared.
    hands: { grip: 'dumbbell', orientation: 'neutral', closure: 0.85 },
    feet: stance.feet,
    locks: stance.locks,

    muscles: {
      primary: ['triceps'],
      secondary: ['forearm_extensors'],
      stabilisers: ['deltoid_anterior', 'trapezius_upper', 'rectus_abdominis', 'obliques', 'erector_lower'],
      ...variant.muscles,
    },

    technique: [
      ...stance.technique,
      {
        kind: 'segmentAngle',
        id: 'torso_upright',
        label: 'Torso stays upright — no leaning back under the weight',
        bone: 'spine_02',
        reference: 'vertical',
        max: 8,
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'no_arch',
        label: 'Lower back does not arch to get the arms overhead',
        bone: 'spine_01',
        axis: 'x',
        min: -4,
        max: 10,
        severity: 'error',
      },
      // The upper arm is the pivot; if it swings forward the shoulder is doing
      // the lifting.
      ...bilateralRule({
        kind: 'segmentAngle',
        id: 'upper_arm_vertical_l',
        label: 'Left upper arm stays pointing at the ceiling',
        bone: 'upperarm_l',
        reference: 'vertical',
        max: 20,
        severity: 'error',
      }),
      {
        kind: 'distance',
        id: 'elbows_in',
        label: 'Elbows stay in, not flared out to the sides',
        from: { bone: 'forearm_l' },
        to: { bone: 'forearm_r' },
        axis: 'x',
        max: 0.5,
      },
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'lockout_l',
        label: 'Left elbow straightens fully at the top',
        bone: 'forearm_l',
        axis: 'x',
        max: 15,
        phases: ['lockout'],
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'full_stretch_l',
        label: 'Left elbow bends past 100° behind the head',
        bone: 'forearm_l',
        axis: 'x',
        min: 100,
        phases: ['stretch'],
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'grip_held_l',
        label: 'Left palm stays neutral, facing in',
        bone: 'forearm_l',
        axis: 'y',
        min: -12,
        max: 15,
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'wrist_neutral_l',
        label: 'Left wrist stays neutral',
        bone: 'hand_l',
        axis: 'z',
        min: -12,
        max: 15,
      }),
      evenSides({
        id: 'dumbbells_aligned',
        label: 'Both dumbbells stay level with one another',
        point: { bone: 'hand_l', along: 1 },
        tolerance: 0.03,
      }),
    ],

    commonErrors: [
      {
        id: 'elbow_flare',
        label: 'Flaring the elbows',
        description: 'The elbows drift out to the sides, taking the long head of the triceps out of its stretch.',
        ruleId: 'elbows_in',
        correction: 'Keep the elbows pointing forward and close to the head.',
      },
      {
        id: 'shoulder_swing',
        label: 'Swinging from the shoulder',
        description: 'The upper arm travels forward as the weight comes up, turning it into a pullover.',
        ruleId: 'upper_arm_vertical_l',
        correction: 'Hold the upper arms still; only the forearms move.',
      },
      {
        id: 'arching',
        label: 'Arching the lower back',
        description: 'The ribs flare and the lower back arches to get the arms overhead.',
        ruleId: 'no_arch',
        correction: 'Brace the abdominals and squeeze the glutes before the first rep.',
      },
      {
        id: 'short_range',
        label: 'Stopping short',
        description: 'The dumbbells stop above the head, so the triceps never works from length.',
        ruleId: 'full_stretch_l',
        correction: 'Lower until the forearms are past horizontal behind the head.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe in as the weights lower, out as you straighten the arms.',
    },

    camera: {
      preset: 'three_quarter',
      position: vec3(2.2, 1.7, 2.2),
      target: vec3(0, 1.45, 0),
      fov: 42,
      note: 'High three-quarter view keeps the dumbbells in shot behind the head.',
      ...variant.camera,
    },
  };
}
