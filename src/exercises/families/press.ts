import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import { vec3 } from '../../rig/types';
import { bilateralJointTarget, bilateralRule } from '../mirror';
import { evenSides } from '../presets';
import { handDumbbells, plantedStance } from '../stance';

/**
 * The overhead press family.
 *
 * The second family, and the one that decides whether the pattern in
 * `families/curl.ts` was a pattern or a curl-shaped coincidence. It holds up,
 * with one thing learned: a press needs its rules scoped to phases in a way a
 * curl never did — the elbow must bend past 85° at the bottom but lock out at
 * the top, and those are the same joint checked against opposite bounds at
 * different moments. `TechniqueRule.phases` already carried that, so the family
 * passes the phase ids through rather than inventing anything.
 *
 * What a press is: the humerus travels from 72° of abduction to nearly
 * overhead while the elbow extends, with the trunk braced so nothing below the
 * shoulders contributes. That is the whole shoulder range, at the end where the
 * joint limits are tightest, which is why the press earns a family of its own
 * rather than being a curl with different numbers.
 *
 * ## What is shared with the curl, and what is deliberately not
 *
 * The standing stance — feet, floor locks, planted rule — and the pair of
 * hand-held dumbbells come from `stance.ts`, because the two families already
 * said those identically. The torso rule does not: a press is held to 8°
 * because leaning back turns it into an incline press, where a curl's 10° is
 * about not swinging the weight up. Same shape, different reason, so they stay
 * apart.
 */

/** How the palms are held. */
export type PressGrip = 'pronated' | 'neutral';

interface GripSpec {
  /**
   * Forearm axial rotation through the press, degrees, left side.
   *
   * A pronated overhead press gets its palms-forward position from the
   * shoulder's external rotation, not from the forearm, which is why it holds
   * the forearm neutral and still reads as pronated. A neutral-grip press
   * additionally turns the forearm so the palms face each other, and that is a
   * real rotation rather than a caption.
   */
  rotation: { start: number; peak: number };
  /** The band the technique rule holds the forearm inside, degrees, left side. */
  allowed: { min: number; max: number };
  orientation: 'pronated' | 'neutral';
  /** External rotation of the humerus at the rack and at lockout, degrees. */
  external: { start: number; peak: number };
  palm: string;
}

const GRIPS: Record<PressGrip, GripSpec> = {
  pronated: {
    rotation: { start: 0, peak: 0 },
    allowed: { min: -15, max: 15 },
    orientation: 'pronated',
    // The external rotation that holds the forearms vertical unwinds as the
    // arms come overhead, which is what stops the dumbbells finishing out to
    // the side.
    external: { start: 70, peak: 10 },
    palm: 'facing forward',
  },
  neutral: {
    // Palms face each other: the forearm turns towards supination from the
    // pronated press's neutral forearm, and the shoulder externally rotates
    // less because the elbows track in front rather than out to the side.
    rotation: { start: 34, peak: 22 },
    allowed: { min: 12, max: 45 },
    orientation: 'neutral',
    external: { start: 44, peak: 8 },
    palm: 'facing each other',
  },
};

export interface PressVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  /** What the palms do, as motion rather than as a caption. */
  grip: PressGrip;
  /** Load per hand, kilograms. */
  mass?: number;
  /** Humerus abduction at the rack and at lockout, degrees. */
  abduction?: { start: number; peak: number };
  /** Elbow flexion at the rack and at lockout, degrees. */
  elbow?: { start: number; peak: number };
  tempo?: Tempo;
  closure?: number;
  handWidth?: number;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

/** Racked beside the head, finishing stacked over the shoulders. */
const ABDUCTION = { start: -72, peak: -170 };
const ELBOW = { start: 100, peak: 8 };

/** The trunk is braced, so nothing above the hips moves. */
const BRACED = {
  pelvis: { x: 2 },
  spine_01: { x: 2 },
  spine_02: { x: -2 },
  spine_03: { x: -2 },
  neck: { x: -2 },
};

export function pressFamily(variant: PressVariant): ExerciseDefinition {
  const grip = GRIPS[variant.grip];
  const abduction = variant.abduction ?? ABDUCTION;
  const elbow = variant.elbow ?? ELBOW;
  const stance = plantedStance();

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'upper_push',
    description: variant.description,

    equipment: { required: ['dumbbell'], instances: handDumbbells(variant.mass ?? 12) },

    startPose: { label: 'Racked', joints: { ...BRACED } },
    peakPose: { label: 'Overhead', joints: { ...BRACED } },

    jointTargets: [
      ...bilateralJointTarget({
        bone: 'upperarm_l',
        axis: 'z',
        start: abduction.start,
        peak: abduction.peak,
        role: 'prime',
        range: { min: -175, max: -30 },
      }),
      ...bilateralJointTarget({
        bone: 'forearm_l',
        axis: 'x',
        start: elbow.start,
        peak: elbow.peak,
        role: 'prime',
        range: { min: 0, max: 120 },
      }),
      ...bilateralJointTarget({
        bone: 'upperarm_l',
        axis: 'y',
        start: grip.external.start,
        peak: grip.external.peak,
        role: 'support',
      }),
      ...bilateralJointTarget({ bone: 'upperarm_l', axis: 'x', start: 14, peak: 4, role: 'support' }),
      // Only a grip that actually turns the forearm authors this. The pronated
      // press holds the forearm neutral and gets its palms from the shoulder,
      // so writing a 0-to-0 target would add a joint target that does nothing.
      ...(grip.rotation.start === 0 && grip.rotation.peak === 0
        ? []
        : bilateralJointTarget({
            bone: 'forearm_l',
            axis: 'y',
            start: grip.rotation.start,
            peak: grip.rotation.peak,
            role: 'support',
          })),
    ],

    phases: [
      { id: 'concentric', label: 'Press', to: 'peak', easing: 'grind', contraction: 'concentric' },
      { id: 'lockout', label: 'Lockout', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'eccentric', label: 'Lower', to: 'start', easing: 'lift', contraction: 'eccentric' },
      { id: 'racked', label: 'Reset', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { eccentric: 2, pauseStretched: 0.5, concentric: 1.6, pauseContracted: 0.6 },

    hands: {
      grip: 'dumbbell',
      orientation: grip.orientation,
      closure: variant.closure ?? 0.85,
      width: variant.handWidth ?? 1.027,
    },
    feet: stance.feet,
    locks: stance.locks,

    muscles: {
      primary: ['deltoid_anterior', 'deltoid_medial'],
      secondary: ['triceps', 'trapezius_upper'],
      stabilisers: [
        'deltoid_posterior',
        'rectus_abdominis',
        'obliques',
        'erector_lower',
        'erector_mid',
        'gluteus',
        'forearm_flexors',
      ],
      ...variant.muscles,
    },

    technique: [
      ...stance.technique,
      {
        kind: 'segmentAngle',
        id: 'torso_upright',
        label: 'Torso stays upright — no leaning back to press',
        bone: 'spine_02',
        reference: 'vertical',
        max: 8,
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'no_layback',
        label: 'Lower back does not arch to turn the press into an incline press',
        bone: 'spine_01',
        axis: 'x',
        min: -4,
        max: 10,
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'bottom_depth',
        label: 'Elbows bend past 85° at the bottom, so the range is not cut short',
        bone: 'forearm_l',
        axis: 'x',
        min: 85,
        phases: ['racked'],
        severity: 'error',
      },
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'lockout_l',
        label: 'Left elbow locks out overhead',
        bone: 'forearm_l',
        axis: 'x',
        min: 0,
        max: 15,
        phases: ['lockout'],
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'relativePosition',
        id: 'overhead_l',
        label: 'Left dumbbell finishes over the shoulder, not out to the side',
        point: { bone: 'hand_l' },
        relativeTo: { bone: 'upperarm_l' },
        axis: 'x',
        min: -0.16,
        max: 0.02,
        phases: ['lockout'],
        severity: 'error',
      }),
      {
        kind: 'relativePosition',
        id: 'press_height',
        label: 'The dumbbells finish a full arm above the shoulders',
        point: { bone: 'hand_l' },
        relativeTo: { bone: 'upperarm_l' },
        axis: 'y',
        min: 0.5,
        phases: ['lockout'],
        severity: 'error',
      },
      ...bilateralRule({
        kind: 'distance',
        id: 'wrist_over_elbow_l',
        label: 'Left wrist stays stacked over the elbow',
        from: { bone: 'forearm_l' },
        to: { bone: 'hand_l' },
        axis: 'x',
        max: 0.1,
      }),
      ...bilateralRule({
        kind: 'relativePosition',
        id: 'press_plane_l',
        label: 'Left dumbbell stays in the plane of the shoulder, not pressed out in front',
        point: { bone: 'hand_l' },
        relativeTo: { bone: 'upperarm_l' },
        axis: 'z',
        min: -0.12,
        max: 0.14,
      }),
      // The grip rule and the grip motion come from the same row of GRIPS, so a
      // variant cannot be checked against a grip it does not hold.
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'grip_held_l',
        label: `Left palm stays ${grip.palm}`,
        bone: 'forearm_l',
        axis: 'y',
        min: grip.allowed.min,
        max: grip.allowed.max,
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'wrist_neutral_l',
        label: 'Left wrist stays neutral under the dumbbell',
        bone: 'hand_l',
        axis: 'z',
        min: -12,
        max: 12,
      }),
      {
        kind: 'distance',
        id: 'hand_width',
        label: 'Hands stay in the press path, neither collapsing in nor flaring wide',
        from: { bone: 'hand_l' },
        to: { bone: 'hand_r' },
        axis: 'x',
        min: 0.517,
        max: 1.117,
      },
      evenSides({
        id: 'even_press',
        label: 'Both dumbbells stay level with one another',
        point: { bone: 'hand_l', along: 1 },
        tolerance: 0.02,
      }),
    ],

    commonErrors: [
      {
        id: 'layback',
        label: 'Leaning back under the weight',
        description: 'The lower back arches and the press turns into an incline press.',
        ruleId: 'no_layback',
        correction: 'Squeeze the glutes and brace the abdominals before the first rep.',
      },
      {
        id: 'pressing_forward',
        label: 'Pressing out in front',
        description: 'The dumbbells travel forward of the shoulders, loading the front delt alone.',
        ruleId: 'press_plane_l',
        correction: 'Press straight up beside the head and finish with the weights over the shoulders.',
      },
      {
        id: 'short_range',
        label: 'Cutting the bottom off',
        description: 'The dumbbells stop above the ears, so the shoulder never works from length.',
        ruleId: 'bottom_depth',
        correction: 'Lower until the elbows are level with the shoulders and the forearms are vertical.',
      },
      {
        id: 'wrist_break',
        label: 'Wrists bending back',
        description: 'The wrists extend under the load and the dumbbells drift behind the forearm.',
        ruleId: 'wrist_neutral_l',
        correction: 'Keep the knuckles up and the dumbbell stacked over the forearm.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe in as the dumbbells come down, out as you press overhead.',
    },

    camera: {
      preset: 'three_quarter',
      position: vec3(2.4, 1.6, 2.8),
      target: vec3(0, 1.35, 0),
      fov: 42,
      note: 'Framed high and wide enough to keep the lockout in shot from three-quarters.',
      ...variant.camera,
    },
  };
}
