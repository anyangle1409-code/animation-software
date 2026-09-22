import type { ExerciseDefinition } from '../types';
import { vec3 } from '../../rig/types';
import { bilateralJointTarget, bilateralLock, bilateralRule } from '../mirror';

/**
 * Standing two-arm dumbbell overhead press.
 *
 * Tests the shoulder through nearly its whole range: the humerus travels from
 * 72° of abduction to almost fully overhead while the elbow extends, with a
 * dumbbell rigidly held in each hand the entire way. The curl exercises the
 * arm below the shoulder; this exercises the shoulder itself, at the end of
 * its abduction range where the joint limits are tightest.
 */

/** Held by both poses: the trunk is braced, so nothing above the hips moves. */
const braced = {
  pelvis: { x: 2 },
  spine_01: { x: 2 },
  spine_02: { x: -2 },
  spine_03: { x: -2 },
  neck: { x: -2 },
};

export const shoulderPress: ExerciseDefinition = {
  id: 'dumbbell_shoulder_press',
  name: 'Dumbbell Shoulder Press',
  clipName: 'shoulder_press',
  category: 'upper_push',
  description:
    'Standing dumbbell overhead press. The dumbbells start beside the head ' +
    'with the elbows under the wrists and finish stacked over the shoulders.',

  equipment: {
    required: ['dumbbell'],
    instances: [
      {
        id: 'dumbbell_l',
        kind: 'dumbbell',
        label: 'Left dumbbell',
        mass: 12,
        position: vec3(0, 0, 0),
        rotation: vec3(0, 0, 0),
        visible: true,
        attachment: { mode: 'hand', side: 'l', socket: 'grip' },
      },
      {
        id: 'dumbbell_r',
        kind: 'dumbbell',
        label: 'Right dumbbell',
        mass: 12,
        position: vec3(0, 0, 0),
        rotation: vec3(0, 0, 0),
        visible: true,
        attachment: { mode: 'hand', side: 'r', socket: 'grip' },
      },
    ],
  },

  startPose: { label: 'Racked', joints: { ...braced } },
  peakPose: { label: 'Overhead', joints: { ...braced } },

  /**
   * The press is entirely shoulder and elbow. Abduction is the prime mover;
   * the external rotation that holds the forearms vertical unwinds as the arms
   * come overhead, which is what stops the dumbbells finishing out to the side.
   */
  jointTargets: [
    ...bilateralJointTarget({ bone: 'upperarm_l', axis: 'z', start: -72, peak: -170, role: 'prime', range: { min: -175, max: -30 } }),
    ...bilateralJointTarget({ bone: 'forearm_l', axis: 'x', start: 100, peak: 8, role: 'prime', range: { min: 0, max: 120 } }),
    ...bilateralJointTarget({ bone: 'upperarm_l', axis: 'y', start: 70, peak: 10, role: 'support' }),
    ...bilateralJointTarget({ bone: 'upperarm_l', axis: 'x', start: 14, peak: 4, role: 'support' }),
  ],

  phases: [
    { id: 'concentric', label: 'Press', to: 'peak', easing: 'grind', contraction: 'concentric' },
    { id: 'lockout', label: 'Lockout', to: 'peak', easing: 'hold', contraction: 'isometric' },
    { id: 'eccentric', label: 'Lower', to: 'start', easing: 'lift', contraction: 'eccentric' },
    { id: 'racked', label: 'Reset', to: 'start', easing: 'hold', contraction: 'isometric' },
  ],

  tempo: { eccentric: 2, pauseStretched: 0.5, concentric: 1.6, pauseContracted: 0.6 },

  hands: { grip: 'dumbbell', orientation: 'pronated', closure: 0.85, width: 1.027 },
  feet: { width: 0.32, toeOut: 6, planted: true },

  locks: [
    ...bilateralLock({ id: 'foot_l', chain: 'leg_l', mode: 'floor', enabled: true }),
  ],

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
  },

  technique: [
    ...bilateralRule({
      kind: 'stationary',
      id: 'foot_planted_l',
      label: 'Left foot stays planted',
      point: { bone: 'foot_l' },
      tolerance: 0.012,
      severity: 'error',
    }),
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
    {
      kind: 'symmetry',
      id: 'even_press',
      label: 'Both dumbbells stay level with one another',
      left: { bone: 'hand_l', along: 1 },
      right: { bone: 'hand_r', along: 1 },
      tolerance: 0.02,
      severity: 'error',
    },],

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
  },
};
