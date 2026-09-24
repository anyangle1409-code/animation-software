import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import type { TechniqueRule } from '../../constraints/types';
import { vec3 } from '../../rig/types';
import { bilateralJointTarget, bilateralJoints, bilateralRule } from '../mirror';
import { evenSides } from '../presets';
import { handDumbbells, plantedStance } from '../stance';

/**
 * The shoulder-raise family: the deltoid lifting a straight-ish arm.
 *
 * The eighth family, and the first where the shoulder is the prime mover rather
 * than a support: the elbow stays soft and fixed, and the whole arm swings up
 * as one lever to shoulder height. The load is furthest from the shoulder at
 * the top, so the top is where it is hardest and where lifters cheat, by
 * swinging the trunk or shrugging.
 *
 * Two directions of the same lever, one shoulder axis each:
 *
 * * `lateral` raises the arm out to the side (abduction, the rig's upper-arm z),
 *   a little forward of the body's plane, in the line of the shoulder blade.
 *   The forearm stays at its neutral, and the palm turns to face the floor by
 *   itself as the arm rises: an arm hanging palm-in and swung out sideways
 *   finishes palm-down.
 * * `front` raises it straight ahead (flexion, upper-arm x), palms down.
 *
 * Scapular rhythm stays off, so the arm stops at shoulder height, which is
 * where the exercise stops anyway: past it the upper trapezius takes over.
 */

export type RaiseDirection = 'lateral' | 'front';

export interface RaiseVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  direction: RaiseDirection;
  /** Load per hand, kilograms. */
  mass?: number;
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

interface RaisePath {
  /** Upper arm at the bottom and the top: flexion (x) and abduction (z, negative is out). */
  bottom: { x: number; z: number };
  top: { x: number; z: number };
  /** Forearm twist, degrees: 0 is palm-in, negative pronates. */
  twist: number;
}

const PATHS: Record<RaiseDirection, RaisePath> = {
  // Hanging a little out from the thighs, so the dumbbells clear them, up to a
  // few degrees short of horizontal, 20° forward of the frontal plane.
  lateral: { bottom: { x: 8, z: -8 }, top: { x: 20, z: -84 }, twist: 0 },
  // Straight ahead, arms just apart, palms down.
  front: { bottom: { x: 6, z: -8 }, top: { x: 86, z: -8 }, twist: -72 },
};

/** A soft, fixed elbow: bent enough to take strain off it, not so much it rows. */
const ELBOW = 14;

const BRACED = {
  pelvis: { x: 2 },
  spine_01: { x: 2 },
  spine_02: { x: -1 },
  spine_03: { x: -1 },
  neck: { x: -2 },
};

export function raiseFamily(variant: RaiseVariant): ExerciseDefinition {
  const path = PATHS[variant.direction];
  const lateral = variant.direction === 'lateral';
  const stance = plantedStance();
  const arms = (upper: { x: number; z: number }) =>
    bilateralJoints({
      upperarm_l: { x: upper.x, z: upper.z },
      forearm_l: { x: ELBOW, y: path.twist },
      hand_l: { z: 0 },
    });

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'shoulders',
    description: variant.description,

    equipment: { required: ['dumbbell'], instances: handDumbbells(variant.mass ?? 6) },

    startPose: { label: 'Arms down', joints: { ...BRACED, ...arms(path.bottom) } },
    peakPose: { label: 'Shoulder height', joints: { ...BRACED, ...arms(path.top) } },

    jointTargets: lateral
      ? [
          ...bilateralJointTarget({
            bone: 'upperarm_l', axis: 'z', start: path.bottom.z, peak: path.top.z, role: 'prime',
            range: { min: -95, max: 0 },
          }),
          ...bilateralJointTarget({ bone: 'upperarm_l', axis: 'x', start: path.bottom.x, peak: path.top.x, role: 'support' }),
        ]
      : [
          ...bilateralJointTarget({
            bone: 'upperarm_l', axis: 'x', start: path.bottom.x, peak: path.top.x, role: 'prime',
            range: { min: 0, max: 95 },
          }),
        ],

    phases: [
      { id: 'concentric', label: 'Raise', to: 'peak', easing: 'lift', contraction: 'concentric' },
      { id: 'top', label: 'Top', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'eccentric', label: 'Lower', to: 'start', easing: 'lift', contraction: 'eccentric' },
      { id: 'bottom', label: 'Reset', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { concentric: 1.2, pauseContracted: 0.4, eccentric: 2, pauseStretched: 0.4 },

    hands: { grip: 'dumbbell', orientation: lateral ? 'neutral' : 'pronated', closure: 0.85 },
    feet: stance.feet,
    locks: stance.locks,

    muscles: lateral
      ? {
          primary: ['deltoid_medial'],
          secondary: ['deltoid_anterior', 'trapezius_upper'],
          stabilisers: ['trapezius_mid', 'rectus_abdominis', 'obliques', 'erector_lower', 'forearm_extensors'],
          ...variant.muscles,
        }
      : {
          primary: ['deltoid_anterior'],
          secondary: ['deltoid_medial', 'pectoralis'],
          stabilisers: ['trapezius_upper', 'rectus_abdominis', 'obliques', 'erector_lower', 'forearm_extensors'],
          ...variant.muscles,
        },

    technique: [
      ...stance.technique,
      {
        kind: 'segmentAngle',
        id: 'torso_upright',
        label: 'Torso stays upright — no swinging the weights up',
        bone: 'spine_02',
        reference: 'vertical',
        max: 8,
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'no_lean_back',
        label: 'Lower back does not lean back to heave the weights',
        bone: 'spine_01',
        axis: 'x',
        min: -4,
        max: 8,
        severity: 'error',
      },
      // The arm reaches shoulder height at the top: its angle from hanging.
      ...bilateralRule({
        kind: 'segmentAngle',
        id: 'shoulder_height_l',
        label: 'Left arm rises to shoulder height',
        bone: 'upperarm_l',
        reference: 'vertical',
        min: 72,
        phases: ['top'],
        severity: 'error',
      }),
      // And no higher: the hand stays at or below the shoulder joint.
      ...bilateralRule({
        kind: 'relativePosition',
        id: 'not_above_shoulder_l',
        label: 'Left hand stops at shoulder height, not above',
        point: { bone: 'hand_l' },
        relativeTo: { bone: 'upperarm_l' },
        axis: 'y',
        max: 0.04,
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'soft_elbow_l',
        label: 'Left elbow stays soft and fixed — not locked, not rowing',
        bone: 'forearm_l',
        axis: 'x',
        min: 5,
        max: 30,
        severity: 'error',
      }),
      ...bilateralRule(lateral
        ? {
            kind: 'jointAngle',
            id: 'raise_plane_l',
            label: 'Left arm rises in line with the shoulder blade, a little forward of the body',
            bone: 'upperarm_l',
            axis: 'x',
            min: 0,
            max: 35,
            severity: 'error',
          }
        : {
            kind: 'jointAngle',
            id: 'raise_plane_l',
            label: 'Left arm rises straight ahead, not out to the side',
            bone: 'upperarm_l',
            axis: 'z',
            min: -20,
            max: 5,
            severity: 'error',
          }),
      {
        kind: 'jointAngle',
        id: 'no_shrug',
        label: 'Shoulders stay down — no shrugging the weight up',
        bone: 'clavicle_l',
        axis: 'z',
        min: -6,
        max: 6,
        severity: 'error',
      },
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
        id: 'dumbbells_level',
        label: 'Both dumbbells rise level with one another',
        point: { bone: 'hand_l', along: 1 },
        tolerance: 0.03,
      }),
    ] satisfies TechniqueRule[],

    commonErrors: [
      {
        id: 'swinging',
        label: 'Swinging the weights up',
        description: 'The trunk rocks back to throw the dumbbells up, taking the load off the deltoids.',
        ruleId: 'no_lean_back',
        correction: 'Stand tall and braced; lighten the weight until only the arms move.',
      },
      {
        id: 'too_high',
        label: 'Raising above the shoulders',
        description: 'The arms keep going past shoulder height and the upper trapezius takes over.',
        ruleId: 'not_above_shoulder_l',
        correction: 'Stop with the hands level with the shoulders.',
      },
      {
        id: 'shrugging',
        label: 'Shrugging',
        description: 'The shoulders lift towards the ears as the arms rise.',
        ruleId: 'no_shrug',
        correction: 'Keep the shoulders down and away from the ears.',
      },
      {
        id: 'bent_arm',
        label: 'Bending the elbows',
        description: 'The elbows bend as the weight rises, shortening the lever and turning it into a row.',
        ruleId: 'soft_elbow_l',
        correction: 'Fix a slight bend in the elbow and keep it there.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe out as the arms rise, in as they lower.',
    },

    camera: {
      preset: 'front',
      position: lateral ? vec3(0, 1.35, 3.2) : vec3(2.8, 1.35, 1.2),
      target: vec3(0, 1.2, 0),
      fov: 42,
      note: lateral
        ? 'Front view shows both arms reaching shoulder height together.'
        : 'Three-quarter side view shows the arms rising straight ahead to shoulder height.',
      ...variant.camera,
    },
  };
}
