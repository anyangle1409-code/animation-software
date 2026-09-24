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
import { heelDown, plantedStance } from '../stance';

/**
 * The squat family.
 *
 * The third family, and the first below the waist. The curl and the press both
 * move a limb against a body that stays put; a squat moves the *body*, and
 * everything that follows from that is what this file had to absorb.
 *
 * ## What is different about a lower-body movement
 *
 * **The descent is root motion, and the root is the only control.** The peak
 * pose carries a root translation — down 44 cm and back 23 cm — and the legs are
 * then solved backwards from feet that must not move.
 *
 * Measured, that is more literally true than it sounds, and it is worth being
 * exact because the obvious reading is wrong. The hip and knee `jointTargets`
 * are **outputs, not inputs**. Authoring the hip at 85° instead of 100° changes
 * the resolved angle by 0.6°, to 100.9°; authoring the knee at −95° instead of
 * −114° changes it by nothing at all, staying at −112.8°. The IK solves both
 * from the root placement and the locked feet, and overrides whatever they say.
 * Moving the root alone, from −44 cm to −34 cm, moves the pelvis from 510 mm to
 * 610 mm and takes the hip and knee with it, to 88.5° and −97.8°.
 *
 * The ankle is the exception and does drive: 26° resolves to 26.0°, 16° to
 * 16.0°. A `floor` lock constrains where the foot is, not which way it points,
 * so the ankle angle is left free for the pose to set.
 *
 * The shipped bundle is consistent — it asks 100/−114/26 and resolves to
 * 101.5/−112.8/26.0 — because those angles were derived to match the root
 * placement rather than chosen independently. That consistency is load-bearing
 * and invisible: the hip and knee numbers are what the definition *documents*,
 * what the technique rules read, and what a coach would recognise, so a variant
 * that changed them without the root would describe a movement different from
 * the one it plays. `squat.test.ts` measures the agreement so it cannot drift.
 *
 * What the feet do *not* do is slide. Foot drift stays at 0.25 mm through every
 * one of those probes, including the inconsistent ones, because the locks hold
 * the contact and pay for it in joint angles instead.
 *
 * **Three joints move as one.** Hip, knee and ankle are not independent: the
 * shin travels forward over a planted foot, so the ankle has to follow it, and
 * the trunk folds over the hips to keep the centre of mass over the feet. They
 * are authored as one coordinated set for that reason.
 *
 * **The rules are about where the body is, not where a limb is.** Depth is the
 * pelvis against the knee, knee tracking is the knee against the foot, and the
 * heel is checked separately from the foot it belongs to — a heel lifts while
 * the foot as a whole stays perfectly planted, so the foot lock cannot see it.
 *
 * ## What is shared, and what is not
 *
 * The stance comes from `stance.ts` — but its numbers do not. A squat stands
 * 42 cm wide with 12° of toe-out and allows 15 mm of foot drift, against the
 * upper body's 32 cm, 6° and 12 mm, and correcting that assumption is what
 * building this family turned up.
 *
 * Nothing else was extracted at first, deliberately: heel contact, knee
 * tracking, depth and shin angle all looked like lower-body primitives, but one
 * lower-body exercise cannot tell a shared rule from a local one. The hinge
 * settled it. The heel rule is identical in both and now comes from
 * `stance.ts`; depth, shin angle and the torso rule share only their shape —
 * the hinge holds the hips *above* the line this family pushes them below — and
 * knee tracking is the squat's alone. See `families/hinge.ts`.
 */

export interface SquatVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  /** Distance between the feet, metres, and how far the toes turn out. */
  stance?: { width: number; toeOut: number };
  /**
   * Hip, knee and ankle flexion at the bottom, degrees, with the root placement
   * that produces them.
   *
   * All four travel together, but not symmetrically: the root is what actually
   * sets the depth, and the hip and knee are what the solver returns. Passing
   * angles that do not match the root does not change the motion and does not
   * move the feet — it changes what the definition *claims*, while the body does
   * something else. Derive the angles from the placement, or leave the bundle
   * alone; `squat.test.ts` measures that they still agree.
   */
  depth?: { hip: number; knee: number; ankle: number; root: { y: number; z: number } };
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

/** To parallel, with the root placement that pins the ankles at that depth. */
const DEPTH = { hip: 100, knee: -114, ankle: 26, root: { y: -0.44, z: -0.23 } };

/** Arms come forward as a counterweight, which is what keeps the squat upright. */
const ARMS_DOWN = bilateralJoints({ upperarm_l: { x: 8, z: -2 } });
const ARMS_FORWARD = bilateralJoints({
  upperarm_l: { x: 78, z: -6 },
  forearm_l: { x: 14 },
});

export function squatFamily(variant: SquatVariant): ExerciseDefinition {
  const depth = variant.depth ?? DEPTH;
  const stance = plantedStance({
    width: variant.stance?.width ?? 0.42,
    toeOut: variant.stance?.toeOut ?? 12,
    // A foot carrying the whole body through half a metre of travel deforms
    // more than one standing still under a curl.
    tolerance: 0.015,
  });

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'legs',
    description: variant.description,

    equipment: { required: [], instances: [] },

    startPose: {
      label: 'Standing',
      joints: {
        ...ARMS_DOWN,
        pelvis: { x: 2 },
        spine_01: { x: 2 },
        spine_02: { x: 0 },
        spine_03: { x: -1 },
        neck: { x: -2 },
      },
    },

    peakPose: {
      label: 'Bottom',
      joints: {
        ...ARMS_FORWARD,
        // The trunk folds forward over the hips; the spine itself stays neutral.
        pelvis: { x: 14 },
        spine_01: { x: 10 },
        spine_02: { x: 8 },
        spine_03: { x: 4 },
        neck: { x: -14 },
        head: { x: -8 },
      },
      root: { position: { y: depth.root.y, z: depth.root.z } },
    },

    jointTargets: [
      ...bilateralJointTarget({
        bone: 'thigh_l', axis: 'x', start: 2, peak: depth.hip, role: 'prime',
        range: { min: -5, max: 120 },
      }),
      ...bilateralJointTarget({
        bone: 'shin_l', axis: 'x', start: -2, peak: depth.knee, role: 'prime',
        range: { min: -125, max: 0 },
      }),
      // The shin travels forward over a planted foot, so the ankle must follow it.
      ...bilateralJointTarget({
        bone: 'foot_l', axis: 'x', start: 0, peak: depth.ankle, role: 'support',
      }),
    ],

    phases: [
      { id: 'eccentric', label: 'Descend', to: 'peak', easing: 'lift', contraction: 'eccentric' },
      { id: 'bottom', label: 'Bottom', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'concentric', label: 'Stand', to: 'start', easing: 'grind', contraction: 'concentric' },
      { id: 'top', label: 'Reset', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { eccentric: 2, pauseStretched: 0.4, concentric: 1.6, pauseContracted: 0.4 },

    hands: { grip: 'none', orientation: 'neutral', closure: 0.15 },
    feet: stance.feet,
    // No explicit pole: the knees already bend the right way, so the solver
    // follows the pose's own bend plane rather than a hard-coded direction.
    locks: stance.locks,

    muscles: {
      primary: ['quadriceps', 'gluteus'],
      secondary: ['hamstrings', 'erector_lower', 'calves'],
      stabilisers: [
        'rectus_abdominis',
        'obliques',
        'hip_adductors',
        'hip_abductors',
        'erector_mid',
        'deltoid_anterior',
      ],
      ...variant.muscles,
    },

    technique: [
      ...stance.technique,
      ...heelDown(),
      {
        kind: 'segmentAngle',
        id: 'torso_angle',
        label: 'Torso leans forward but never folds over',
        bone: 'spine_02',
        reference: 'vertical',
        max: 50,
        severity: 'error',
      },
      ...bilateralRule({
        kind: 'relativePosition',
        id: 'knee_tracking_l',
        label: 'Left knee tracks over the foot, never caving inwards',
        point: { bone: 'shin_l' },
        relativeTo: { bone: 'foot_l' },
        axis: 'x',
        // A stance wider than the hips always leaves the knee slightly inside
        // the ankle; valgus is when it keeps going, towards the midline.
        min: -0.06,
        max: 0.09,
        severity: 'error',
      }),
      {
        kind: 'relativePosition',
        id: 'depth',
        label: 'Hips reach at least parallel with the knees',
        point: { bone: 'pelvis' },
        relativeTo: { bone: 'shin_l' },
        axis: 'y',
        max: 0.1,
        phases: ['bottom'],
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'neutral_spine',
        label: 'Lower back stays neutral, not rounded',
        bone: 'spine_01',
        axis: 'x',
        min: -4,
        max: 16,
        severity: 'error',
      },
      evenSides({
        id: 'even_knees',
        label: 'Both knees bend evenly',
        point: { bone: 'shin_l' },
        tolerance: 0.02,
      }),
      {
        kind: 'distance',
        id: 'stance_width',
        label: 'Stance stays about shoulder-width',
        from: { bone: 'foot_l' },
        to: { bone: 'foot_r' },
        axis: 'x',
        min: 0.3,
        max: 0.55,
      },
      {
        kind: 'segmentAngle',
        id: 'shin_angle',
        label: 'Shins stay within a workable forward angle',
        bone: 'shin_l',
        reference: 'vertical',
        max: 45,
      },
    ],

    commonErrors: [
      {
        id: 'heels_lifting',
        label: 'Heels lifting',
        description: 'Limited ankle range pulls the heels off the floor at depth.',
        ruleId: 'heel_down_l',
        correction: 'Work on ankle mobility, widen the stance slightly, or squat to a box.',
      },
      {
        id: 'knee_valgus',
        label: 'Knees caving in',
        description: 'The knees collapse towards each other as the hips rise.',
        ruleId: 'knee_tracking_l',
        correction: 'Push the knees out over the middle of each foot throughout.',
      },
      {
        id: 'rounding',
        label: 'Rounding the lower back',
        description: 'The pelvis tucks under at the bottom and the spine rounds.',
        ruleId: 'neutral_spine',
        correction: 'Stop at the depth you can hold a neutral spine, and brace before descending.',
      },
      {
        id: 'shallow',
        label: 'Cutting the depth',
        description: 'Stopping well above parallel, so the glutes barely work.',
        ruleId: 'depth',
        correction: 'Descend until the hip crease reaches at least knee height.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe in and brace at the top, out as you drive back up.',
    },

    camera: {
      preset: 'three_quarter',
      position: vec3(2.4, 1.15, 2.6),
      target: vec3(0, 0.75, 0),
      fov: 40,
      note: 'Three-quarter view shows depth and knee tracking at the same time.',
      ...variant.camera,
    },
  };
}
