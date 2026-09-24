import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import { vec3 } from '../../rig/types';
import { bilateralJointTarget, bilateralJoints, bilateralLock, bilateralRule } from '../mirror';
import { evenSides } from '../presets';

/**
 * The vertical-pull family: pulling the body up to a fixed bar, or a bar down to
 * the body, with the arms working overhead.
 *
 * The pull-up was the family's first exercise, written out in full and accepted
 * before families existed; it is re-expressed here without changing a value, so
 * `pullUp` is byte-identical to the accepted clip (`verticalPull.test.ts`).
 *
 * ## The reference exercise
 *
 * Strict bodyweight pull-up from the crossbar of a rack.
 *
 * Tests the one thing nothing else in the library does: the body is supported
 * entirely by two grips on a piece of equipment that never moves, with no floor
 * contact at all. The hands are held by `equipment` locks rather than world
 * locks, so the grip is resolved through the rack's own sockets — position and
 * orientation both — and the whole body is then solved backwards from them.
 *
 * The root motion is the exercise: the hands are fixed, so raising the root is
 * what pulls the body up, and the arms fold to suit. The heights below are
 * derived rather than guessed — the hang is the lowest root that still leaves a
 * few degrees in the elbow, and the top is the highest one that keeps the elbow
 * inside its anatomical range, which puts the chin level with the bar.
 */

/** Root placement at each end of the repetition. */
// The hang height is not free: the body hangs from the bar, so its height
// follows from arm length and where the shoulder sits. Stage 2's longer
// clavicle lifts the shoulder 8.1 mm in this pose, which shortened
// shoulder-to-bar to 549 mm against a 560 mm arm and bent the elbow to 22.8
// degrees. Dropping the root by that same 8.1 mm restores the dead hang.
// Arm lengths are unchanged.
const HANG = { y: -0.0631, z: -0.06 };
const TOP = { y: 0.5, z: -0.2 };

/**
 * Knees bent, feet behind. A 2.05 m bar is not high enough to hang from with
 * the legs straight, which is exactly why people cross their ankles behind them.
 */
const legs = bilateralJoints({
  thigh_l: { x: -10 },
  shin_l: { x: -70 },
  foot_l: { x: -20 },
});

export interface VerticalPullVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

export function verticalPullFamily(variant: VerticalPullVariant): ExerciseDefinition {
  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'upper_pull',
    description: variant.description,

    equipment: {
      required: ['squat_rack'],
      instances: [
        {
          id: 'rack',
          kind: 'squat_rack',
          label: 'Rack',
          mass: 0,
          position: vec3(0, 0, 0),
          rotation: vec3(0, 0, 0),
          visible: true,
          attachment: { mode: 'static' },
        },
      ],
    },

    startPose: {
      label: 'Dead hang',
      joints: {
        ...legs,
        ...bilateralJoints({
          // Shoulders ride up at the bottom of a hang; they are pulled down and
          // back on the way up, which is where the movement actually starts.
          clavicle_l: { z: -14 },
          spine_01: { x: 2 },
          spine_02: { x: 0 },
          spine_03: { x: 0 },
          neck: { x: -4 },
          // A starting guess only: the grip locks solve both arms exactly.
          upperarm_l: { z: -170 },
          forearm_l: { x: 6 },
        }),
      },
      root: { position: { y: HANG.y, z: HANG.z } },
    },

    peakPose: {
      label: 'Chin to the bar',
      joints: {
        ...legs,
        ...bilateralJoints({
          clavicle_l: { z: 10 },
          // The chest opens towards the bar and the head comes back to clear it.
          spine_01: { x: -6 },
          spine_02: { x: -8 },
          spine_03: { x: -6 },
          neck: { x: -26 },
          head: { x: -14 },
          upperarm_l: { z: -140 },
          forearm_l: { x: 120 },
        }),
      },
      root: { position: { y: TOP.y, z: TOP.z } },
    },

    jointTargets: [
      // What the grip locks produce, written down because it is what a coach
      // would describe and what the technique rules below check.
      ...bilateralJointTarget({
        bone: 'forearm_l', axis: 'x', start: 12, peak: 144, role: 'prime', range: { min: 0, max: 150 },
      }),
      ...bilateralJointTarget({ bone: 'clavicle_l', axis: 'z', start: -14, peak: 10, role: 'support' }),
    ],

    phases: [
      { id: 'concentric', label: 'Pull', to: 'peak', easing: 'grind', contraction: 'concentric' },
      { id: 'top', label: 'Top', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'eccentric', label: 'Lower', to: 'start', easing: 'lift', contraction: 'eccentric' },
      { id: 'hang', label: 'Hang', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { eccentric: 2, pauseStretched: 0.5, concentric: 1.4, pauseContracted: 0.5 },

    hands: { grip: 'bar', orientation: 'pronated', closure: 0.95, width: 0.547 },
    feet: { width: 0.2, toeOut: 0, planted: false },

    locks: [
      ...bilateralLock({
        id: 'grip_l',
        chain: 'arm_l',
        mode: 'equipment',
        equipmentId: 'rack',
        socket: 'pullup_l',
        // The elbows track down and out, which is what keeps the pull in the lats
        // rather than turning it into a shrug.
        pole: vec3(-0.5, 1.05, 0.02),
        enabled: true,
      }),
    ],

    muscles: {
      primary: ['latissimus', 'biceps'],
      secondary: ['trapezius_mid', 'deltoid_posterior', 'forearm_flexors', 'trapezius_upper'],
      stabilisers: ['rectus_abdominis', 'obliques', 'erector_mid', 'gluteus'],
      ...variant.muscles,
    },

    technique: [
      ...bilateralRule({
        kind: 'stationary',
        id: 'grip_fixed_l',
        label: 'Left hand does not move on the bar',
        point: { bone: 'hand_l' },
        tolerance: 0.005,
        severity: 'error',
      }),
      {
        kind: 'distance',
        id: 'grip_width',
        label: 'Grip stays just wider than the shoulders',
        from: { bone: 'hand_l' },
        to: { bone: 'hand_r' },
        axis: 'x',
        min: 0.487,
        max: 0.627,
      },
      {
        kind: 'relativePosition',
        id: 'chin_over_bar',
        label: 'Chin reaches the bar at the top',
        point: { bone: 'head', offset: { x: 0, y: 0.03, z: 0.085 } },
        relativeTo: { bone: 'hand_l' },
        axis: 'y',
        // The bar sits 8 cm above the wrist the arm chain solves for, so this is
        // the chin genuinely clearing the bar rather than reaching its underside.
        min: 0.08,
        phases: ['top'],
        severity: 'error',
      },
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'full_hang_l',
        label: 'Left elbow straightens at the bottom',
        bone: 'forearm_l',
        axis: 'x',
        max: 20,
        phases: ['hang'],
        severity: 'error',
      }),
      {
        kind: 'relativePosition',
        id: 'hang_depth',
        label: 'The hang is a full arm below the bar, not a half rep',
        point: { bone: 'upperarm_l' },
        relativeTo: { bone: 'hand_l' },
        axis: 'y',
        max: -0.5,
        phases: ['hang'],
        severity: 'error',
      },
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'top_flexion_l',
        label: 'Left elbow finishes fully bent',
        bone: 'forearm_l',
        axis: 'x',
        min: 105,
        phases: ['top'],
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'relativePosition',
        id: 'elbows_below_hands_l',
        label: 'Left elbow stays below the hand — the arm pulls, it does not shrug',
        point: { bone: 'forearm_l' },
        relativeTo: { bone: 'hand_l' },
        axis: 'y',
        max: -0.15,
        severity: 'error',
      }),
      {
        kind: 'relativePosition',
        id: 'no_swing',
        label: 'Hips stay behind the bar and never swing forward into a kip',
        point: { bone: 'pelvis' },
        relativeTo: { bone: 'hand_l' },
        axis: 'z',
        min: -0.26,
        max: 0.02,
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'hips_quiet',
        label: 'Hips stay quiet — the knees never drive the rep',
        bone: 'thigh_l',
        axis: 'x',
        min: -20,
        max: 5,
        severity: 'error',
      },
      evenSides({
        id: 'even_pull',
        label: 'Both sides pull evenly',
        point: { bone: 'forearm_l' },
        tolerance: 0.02,
      }),
      {
        kind: 'segmentAngle',
        id: 'trunk_line',
        label: 'Trunk holds a slight lean, never folding at the hips',
        bone: 'spine_02',
        reference: 'vertical',
        max: 18,
      },
    ],

    commonErrors: [
      {
        id: 'kipping',
        label: 'Kipping',
        description: 'The hips and knees swing to throw the body up the bar.',
        ruleId: 'no_swing',
        correction: 'Squeeze the glutes and hold the legs still; drop the reps rather than the standard.',
      },
      {
        id: 'half_rep',
        label: 'Not returning to a dead hang',
        description: 'The elbows stay bent at the bottom, so the lats never work from length.',
        ruleId: 'full_hang_l',
        correction: 'Lower until the arms are straight and the shoulders rise towards the ears.',
      },
      {
        id: 'chin_reach',
        label: 'Reaching with the chin',
        description: 'The neck cranes forward to clear the bar the arms did not.',
        ruleId: 'top_flexion_l',
        correction: 'Pull the chest towards the bar; the chin clears it as a result, not instead.',
      },
      {
        id: 'shrugging',
        label: 'Shrugging at the bottom',
        description: 'The shoulders stay up by the ears through the whole rep.',
        ruleId: 'elbows_below_hands_l',
        correction: 'Set the shoulders down and back before the elbows start to bend.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe out as you pull, in as you lower under control.',
    },

    camera: {
      preset: 'right',
      position: vec3(3.0, 1.5, 0.75),
      target: vec3(0, 1.3, 0),
      fov: 40,
      note: 'Almost side-on, between the rack uprights: the only angle that shows the body line, the lean and the chin clearing the bar at once.',
      ...variant.camera,
    },
  };
}
