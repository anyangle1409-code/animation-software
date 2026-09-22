import type { Tempo } from '../types';
import type { ExerciseDefinition, HandSpec, MuscleInvolvement } from '../types';
import type { CameraRecommendation } from '../types';
import type { CommonError } from '../types';
import { vec3 } from '../../rig/types';
import {
  bilateralJoints,
  bilateralJointTarget,
  bilateralLock,
  bilateralRule,
  bilateralTiming,
} from '../mirror';
import { evenSides, plantedContact } from '../presets';

/**
 * The curl family.
 *
 * Everything a curl is, in one place: the elbow does the work, the upper arm
 * stays quiet beside a still torso, the feet stay planted and the wrist stays
 * neutral. A variant says what makes it that variant — the grip, the load, the
 * range, the tempo — and inherits the rest.
 *
 * ## Why a builder rather than a base object to merge into
 *
 * Most of an `ExerciseDefinition` is arrays: technique rules, joint targets,
 * phases, common errors. Deep-merging arrays has no good answer — override by
 * index is brittle, by id needs every entry to carry one, concatenation cannot
 * remove anything — and every one of those answers makes it harder to see what a
 * variant actually does. A typed variant passed to a function has none of that
 * ambiguity: the variant's fields are exactly its differences, and the type says
 * what may differ.
 *
 * It is also the shape the generator needs. A `CurlVariant` is close to what an
 * intent parser produces from "a standing hammer curl with 12 kg dumbbells" —
 * far closer than a partial `ExerciseDefinition` would be — so the same object
 * serves authoring now and generation later.
 *
 * ## Grip drives the motion, not just the caption
 *
 * `hands.orientation` used to be documentation: one reader in the whole
 * codebase, a display string in the exercise panel. The forearm's actual
 * rotation came from a joint target authored separately, so nothing stopped an
 * exercise claiming a neutral grip while its forearms supinated 72°. That
 * matters more than it sounds — "hammer" *is* the grip, and an intent parser
 * setting `grip: neutral` would have produced a supinated curl.
 *
 * Here the variant names the grip once and the family derives both the caption
 * and the forearm rotation from it. The two cannot disagree because they come
 * from the same place.
 */

/** How the palms are held through the repetition. */
export type CurlGrip = 'supinated' | 'neutral' | 'pronated';

interface GripSpec {
  /** Forearm axial rotation at the bottom and the peak, degrees, left side. */
  rotation: { start: number; peak: number };
  /** The band the technique rule holds it inside, degrees, left side. */
  allowed: { min: number; max: number };
  /** `HandSpec.orientation`, so the caption is the same fact as the motion. */
  orientation: HandSpec['orientation'];
  /** Reads in the technique rule's label. */
  palm: string;
}

/**
 * Forearm supination is +y on the left, pronation −y, and the rig's forearm
 * allows ±85°. A curl holds its grip rather than rotating through it, so the
 * start and peak differ only by the few degrees the biceps adds as it shortens.
 */
const GRIPS: Record<CurlGrip, GripSpec> = {
  // The classic curl: palms up from the bottom, and the biceps supinates a
  // little further as it contracts.
  supinated: {
    rotation: { start: 72, peak: 80 },
    allowed: { min: 65, max: 90 },
    orientation: 'supinated',
    palm: 'supinated',
  },
  // A hammer curl: palms face each other, which is the rig's neutral forearm.
  // The small drift towards supination at the peak is what a lifter's forearm
  // actually does under load; holding a dead 0° reads mechanical.
  neutral: {
    rotation: { start: 0, peak: 6 },
    allowed: { min: -12, max: 15 },
    orientation: 'neutral',
    palm: 'neutral, thumbs up',
  },
  // A reverse curl: palms down, which takes the biceps out of its best leverage
  // and puts the work into the forearm extensors.
  pronated: {
    rotation: { start: -66, peak: -60 },
    allowed: { min: -80, max: -50 },
    orientation: 'pronated',
    palm: 'pronated',
  },
};

export interface CurlVariant {
  id: string;
  name: string;
  /** Slug for exported clip names, e.g. `hammer_curl`. */
  clipName: string;
  description: string;
  /** What makes a hammer curl a hammer curl. */
  grip: CurlGrip;
  /** Load per hand, kilograms. */
  mass?: number;
  /** Elbow flexion at the bottom and the peak, degrees. */
  elbow?: { start: number; peak: number };
  /**
   * How far the upper arms hang clear of the torso at the bottom and the peak,
   * degrees of abduction. Wider is not a style choice: a dumbbell held neutral
   * presents its plates' full 48 mm radius towards the thigh, where a supinated
   * one presents a 17.5 mm edge, so the neutral grips need the room.
   */
  abduction?: { start: number; peak: number };
  tempo?: Tempo;
  /** Distance between the hands, metres. */
  handWidth?: number;
  /** How tightly the fingers close, 0 open to 1 shut. */
  closure?: number;
  /** Merged over the family's, so a variant names only what it changes. */
  muscles?: Partial<MuscleInvolvement>;
  /** Appended to the family's, for mistakes specific to this variant. */
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

/**
 * The elbow range shared by the family.
 *
 * 16° at the bottom, not 6°: bending the elbow is where the hanging dumbbell's
 * thigh clearance is bought, so that the corrected shoulder alignment is not
 * spent tilting the humerus forward to protect it. A soft elbow at the bottom of
 * a dumbbell curl is what a lifter actually does; locking out is the exception.
 */
const ELBOW = { start: 16, peak: 126 };

/**
 * The upper arm hangs 3 deg clear of the torso and drifts to 4 deg at the peak.
 * Abduction still reads as a shrug at the bottom, so it is kept small; the
 * `upper_arm_clear` rule holds it between 3 and 20 deg.
 */
const ABDUCTION = { start: 3, peak: 4 };

export function curlFamily(variant: CurlVariant): ExerciseDefinition {
  const grip = GRIPS[variant.grip];
  const elbow = variant.elbow ?? ELBOW;
  const abduction = variant.abduction ?? ABDUCTION;
  const mass = variant.mass ?? 10;

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'arms',
    description: variant.description,

    equipment: {
      required: ['dumbbell'],
      instances: (['l', 'r'] as const).map((side) => ({
        id: `dumbbell_${side}`,
        kind: 'dumbbell' as const,
        label: `${side === 'l' ? 'Left' : 'Right'} dumbbell`,
        mass,
        position: vec3(0, 0, 0),
        rotation: vec3(0, 0, 0),
        visible: true,
        // The implement is rigid in the hand, so the grip's own rotation carries
        // it: a neutral forearm turns the dumbbell with it and no separate
        // orientation calibration is needed.
        attachment: { mode: 'hand' as const, side, socket: 'grip' },
      })),
    },

    startPose: {
      label: 'Arms extended',
      joints: bilateralJoints({
        spine_01: { x: 2 },
        spine_02: { x: -1 },
        neck: { x: -2 },
        clavicle_l: { z: 5 },
        // Upper arms hang just clear of the torso. Abduction still reads as a
        // shrug at the bottom, so it is not the lever here either.
        //
        // The clearance the hanging dumbbell needs used to be taken forward, by
        // rebasing the whole upper-arm flexion curve 4.3°. That was measured
        // against a shoulder girdle sitting 57 mm in front of the ribcage; with
        // the clavicle's rest angle corrected the arm root is back where it
        // belongs, and buying clearance by tilting the humerus forward would
        // simply reinstate the thing that correction removes.
        //
        // So the clearance comes from the elbow instead, and the upper arm is
        // free to hang closer to vertical: 3° rather than 4.55°, which measures
        // 3.22° of true sagittal tilt against 3.87° before.
        upperarm_l: { x: 3, z: -abduction.start },
        hand_l: { z: 4 },
      }),
    },

    peakPose: {
      label: 'Contracted',
      joints: bilateralJoints({
        spine_01: { x: 2 },
        spine_02: { x: -1 },
        neck: { x: -2 },
        clavicle_l: { z: 5 },
        // A small forward drift keeps the elbows natural without letting the
        // dumbbells crowd the chest at the top of the curl.
        upperarm_l: { x: 7, z: -abduction.peak },
        hand_l: { z: 2 },
      }),
    },

    jointTargets: [
      ...bilateralJointTarget({
        bone: 'forearm_l',
        axis: 'x',
        start: elbow.start,
        peak: elbow.peak,
        role: 'prime',
        range: { min: 0, max: 145 },
      }),
      // The grip, as motion rather than as a label.
      ...bilateralJointTarget({
        bone: 'forearm_l',
        axis: 'y',
        start: grip.rotation.start,
        peak: grip.rotation.peak,
        role: 'support',
      }),
    ],

    phases: [
      {
        id: 'concentric',
        label: 'Curl up',
        to: 'peak',
        easing: 'lift',
        contraction: 'concentric',
        // The elbow leads the rep. The upper arm stays relaxed beside the torso
        // through most of the curl, then makes only the small authored 4° drift
        // near the top instead of moving in lock-step with the forearm. Minimum
        // jerk keeps the delayed shoulder from visibly "switching on".
        jointTiming: bilateralTiming({ upperarm_l: { delay: 0.55, easing: 'minimumJerk' } }),
      },
      { id: 'squeeze', label: 'Squeeze', to: 'peak', easing: 'hold', contraction: 'isometric' },
      {
        id: 'eccentric',
        label: 'Lower',
        to: 'start',
        easing: 'lift',
        contraction: 'eccentric',
        // On the way down the elbow starts opening first; the shoulder settles
        // back a fraction later so the bottom position reads loose, not shrugged.
        jointTiming: bilateralTiming({ upperarm_l: { delay: 0.2, easing: 'minimumJerk' } }),
      },
      { id: 'reset', label: 'Reset', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { eccentric: 2, pauseStretched: 0.5, concentric: 2, pauseContracted: 1 },

    hands: {
      grip: 'dumbbell',
      orientation: grip.orientation,
      closure: variant.closure ?? 0.85,
      width: variant.handWidth ?? 0.42,
    },
    feet: { width: 0.32, toeOut: 6, planted: true },

    locks: [...bilateralLock({ id: 'foot_l', chain: 'leg_l', mode: 'floor', enabled: true })],

    muscles: {
      primary: ['biceps'],
      secondary: ['forearm_flexors', 'deltoid_anterior'],
      stabilisers: ['trapezius_upper', 'erector_lower', 'rectus_abdominis', 'obliques'],
      ...variant.muscles,
    },

    technique: [
      ...plantedContact({
        point: { bone: 'foot_l' },
        tolerance: 0.012,
        label: 'Left foot stays planted',
      }),
      {
        kind: 'segmentAngle',
        id: 'torso_upright',
        label: 'Torso stays upright',
        bone: 'spine_02',
        reference: 'vertical',
        max: 10,
        severity: 'error',
      },
      {
        kind: 'stationary',
        id: 'no_swing',
        label: 'No torso swing',
        point: { bone: 'spine_03' },
        tolerance: 0.05,
        severity: 'error',
      },
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'shoulder_relaxed_l',
        label: 'Left shoulder stays relaxed, not shrugged',
        bone: 'clavicle_l',
        axis: 'z',
        min: 0,
        max: 10,
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'upper_arm_clear_l',
        label: 'Left upper arm stays slightly clear of the torso',
        bone: 'upperarm_l',
        axis: 'z',
        min: -20,
        max: -3,
      }),
      ...bilateralRule({
        kind: 'relativePosition',
        id: 'elbow_not_inward_l',
        label: 'Left elbow does not tuck in towards the chest',
        point: { bone: 'forearm_l' },
        relativeTo: { bone: 'spine_03' },
        axis: 'x',
        max: -0.13,
      }),
      ...bilateralRule({
        kind: 'relativePosition',
        id: 'elbow_under_shoulder_l',
        label: 'Left elbow stays roughly below the shoulder',
        point: { bone: 'forearm_l' },
        relativeTo: { bone: 'upperarm_l' },
        axis: 'z',
        min: -0.06,
        max: 0.12,
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'shoulder_quiet_l',
        label: 'Left shoulder does not take over the lift',
        bone: 'upperarm_l',
        axis: 'x',
        min: -5,
        max: 10,
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
        id: 'wrist_deviation_l',
        label: 'Left wrist does not deviate sideways',
        bone: 'hand_l',
        axis: 'x',
        min: -10,
        max: 10,
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
      {
        kind: 'distance',
        id: 'hands_shoulder_width',
        label: 'Hands stay about shoulder-width apart',
        from: { bone: 'hand_l' },
        to: { bone: 'hand_r' },
        axis: 'x',
        min: 0.26,
        max: 0.56,
      },
      evenSides({
        id: 'dumbbells_aligned',
        label: 'Both dumbbells stay level with one another',
        point: { bone: 'hand_l', along: 1 },
        tolerance: 0.03,
      }),
    ],

    commonErrors: [
      {
        id: 'swinging',
        label: 'Swinging the weight',
        description: 'Using hip and torso momentum to start the curl.',
        ruleId: 'no_swing',
        correction: 'Slow the tempo and reduce the load until the torso stays still.',
      },
      {
        id: 'shrugging_shoulders',
        label: 'Shrugging the shoulders',
        description: 'Lifting the shoulders towards the ears as the dumbbells rise.',
        ruleId: 'shoulder_relaxed_l',
        correction: 'Keep the shoulders down and relaxed while the elbows do the work.',
      },
      {
        id: 'elbow_drift',
        label: 'Elbows drifting forward',
        description: 'The elbows travel forward so the front delts take the work.',
        ruleId: 'elbow_under_shoulder_l',
        correction:
          'Keep the elbows roughly under the shoulders; allow only a small natural drift near the top.',
      },
      {
        id: 'partial_range',
        label: 'Cutting the range short',
        description: 'Stopping before the arm is extended, so the stretch is lost.',
        correction: 'Lower until the elbow is almost straight before curling again.',
      },
      {
        id: 'wrist_curl',
        label: 'Curling at the wrist',
        description: 'Flexing the wrist to help the weight up.',
        ruleId: 'wrist_neutral_l',
        correction: 'Keep the knuckles in line with the forearm.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe in as you lower, out as you curl.',
    },

    camera: {
      preset: 'three_quarter',
      position: vec3(2.0, 1.35, 2.4),
      target: vec3(0, 1.05, 0),
      fov: 38,
      note: 'Three-quarter view shows elbow position and the full range of both arms.',
      ...variant.camera,
    },
  };
}
