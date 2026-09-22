import type { ExerciseDefinition } from '../types';
import { vec3 } from '../../rig/types';
import { bilateralJointTarget, bilateralJoints, bilateralRule } from '../mirror';
import { evenSides, plantedContact } from '../presets';

/**
 * Bodyweight squat.
 *
 * Tests the lower body: hips, knees and ankles working together while the feet
 * stay exactly where they started. The descent is authored as root motion — the
 * body sinks — and the foot locks then solve the legs, which is why the feet
 * never slide even as the whole body moves half a metre.
 */

const STANCE = { width: 0.42, toeOut: 12 };

/** Arms come forward as a counterweight, which is what keeps the squat upright. */
const armsDown = bilateralJoints({ upperarm_l: { x: 8, z: -2 } });
const armsForward = bilateralJoints({
  upperarm_l: { x: 78, z: -6 },
  forearm_l: { x: 14 },
});

export const airSquat: ExerciseDefinition = {
  id: 'air_squat',
  name: 'Bodyweight Squat',
  clipName: 'air_squat',
  category: 'legs',
  description:
    'Bodyweight squat to depth with a shoulder-width stance. The feet stay ' +
    'planted, the heels stay down, and the hips and knees bend together.',

  equipment: { required: [], instances: [] },

  startPose: {
    label: 'Standing',
    joints: {
      ...armsDown,
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
      ...armsForward,
      // The trunk folds forward over the hips; the spine itself stays neutral.
      pelvis: { x: 14 },
      spine_01: { x: 10 },
      spine_02: { x: 8 },
      spine_03: { x: 4 },
      neck: { x: -14 },
      head: { x: -8 },
    },
    /**
     * The root placement is derived, not guessed: it is the position that puts
     * the ankles exactly back on their standing contact points for these hip,
     * knee and ankle angles. The foot locks then have nothing left to correct,
     * which is why the feet do not slide by even a millimetre.
     */
    root: { position: { y: -0.44, z: -0.23 } },
  },

  jointTargets: [
    ...bilateralJointTarget({ bone: 'thigh_l', axis: 'x', start: 2, peak: 100, role: 'prime', range: { min: -5, max: 120 } }),
    ...bilateralJointTarget({ bone: 'shin_l', axis: 'x', start: -2, peak: -114, role: 'prime', range: { min: -125, max: 0 } }),
    // The shin travels forward over a planted foot, so the ankle must follow it.
    ...bilateralJointTarget({ bone: 'foot_l', axis: 'x', start: 0, peak: 26, role: 'support' }),
  ],

  phases: [
    { id: 'eccentric', label: 'Descend', to: 'peak', easing: 'lift', contraction: 'eccentric' },
    { id: 'bottom', label: 'Bottom', to: 'peak', easing: 'hold', contraction: 'isometric' },
    { id: 'concentric', label: 'Stand', to: 'start', easing: 'grind', contraction: 'concentric' },
    { id: 'top', label: 'Reset', to: 'start', easing: 'hold', contraction: 'isometric' },
  ],

  tempo: { eccentric: 2, pauseStretched: 0.4, concentric: 1.6, pauseContracted: 0.4 },

  hands: { grip: 'none', orientation: 'neutral', closure: 0.15 },
  feet: { width: STANCE.width, toeOut: STANCE.toeOut, planted: true },

  locks: [
    // No explicit pole: the knees already bend the right way, so the solver
    // follows the pose's own bend plane rather than a hard-coded direction.
    { id: 'foot_l', chain: 'leg_l', mode: 'floor', enabled: true },
    { id: 'foot_r', chain: 'leg_r', mode: 'floor', enabled: true },
  ],

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
  },

  technique: [
    ...plantedContact({ point: { bone: 'foot_l' }, tolerance: 0.015, label: 'Left foot stays planted' }),
    ...bilateralRule({
      kind: 'stationary',
      id: 'heel_down_l',
      label: 'Left heel stays on the floor',
      point: { bone: 'foot_l', offset: { x: 0, y: -0.04, z: 0 } },
      tolerance: 0.025,
      severity: 'error',
    }),
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
  },
};
