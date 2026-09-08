import type { ExerciseDefinition } from '../types';
import { vec3 } from '../../rig/types';

/**
 * Standing two-arm dumbbell curl.
 *
 * Tests the arm side of the engine: shoulder, elbow and wrist working together
 * with a rigidly held implement in each hand.
 */
export const bicepCurl: ExerciseDefinition = {
  id: 'dumbbell_bicep_curl',
  name: 'Dumbbell Bicep Curl',
  clipName: 'bicep_curl',
  category: 'arms',
  description:
    'Standing two-arm dumbbell curl with a supinated grip. The upper arms stay ' +
    'still beside the torso and the forearms do the work.',

  equipment: {
    required: ['dumbbell'],
    instances: [
      {
        id: 'dumbbell_l',
        kind: 'dumbbell',
        label: 'Left dumbbell',
        mass: 10,
        position: vec3(0, 0, 0),
        rotation: vec3(0, 0, 0),
        visible: true,
        attachment: { mode: 'hand', side: 'l', socket: 'grip' },
      },
      {
        id: 'dumbbell_r',
        kind: 'dumbbell',
        label: 'Right dumbbell',
        mass: 10,
        position: vec3(0, 0, 0),
        rotation: vec3(0, 0, 0),
        visible: true,
        attachment: { mode: 'hand', side: 'r', socket: 'grip' },
      },
    ],
  },

  startPose: {
    label: 'Arms extended',
    joints: {
      spine_01: { x: 2 },
      spine_02: { x: -1 },
      neck: { x: -2 },
      // Upper arms hang just clear of the torso.
      upperarm_l: { x: 2, z: -6 },
      upperarm_r: { x: 2, z: 6 },
      hand_l: { z: 4 },
      hand_r: { z: -4 },
    },
  },

  peakPose: {
    label: 'Contracted',
    joints: {
      spine_01: { x: 2 },
      spine_02: { x: -1 },
      neck: { x: -2 },
      // Elbows travel forward a few degrees, which is normal, not a fault.
      upperarm_l: { x: 12, z: -8 },
      upperarm_r: { x: 12, z: 8 },
      hand_l: { z: 2 },
      hand_r: { z: -2 },
    },
  },

  /**
   * The joints that actually produce the movement. Everything else is held by
   * the poses above, which keeps the interesting numbers in one short list.
   */
  jointTargets: [
    { bone: 'forearm_l', axis: 'x', start: 6, peak: 138, role: 'prime', range: { min: 0, max: 145 } },
    { bone: 'forearm_r', axis: 'x', start: 6, peak: 138, role: 'prime', range: { min: 0, max: 145 } },
    // Supination is held throughout: the palms face up from the bottom.
    { bone: 'forearm_l', axis: 'y', start: 72, peak: 80, role: 'support' },
    { bone: 'forearm_r', axis: 'y', start: -72, peak: -80, role: 'support' },
  ],

  phases: [
    { id: 'concentric', label: 'Curl up', to: 'peak', easing: 'lift', contraction: 'concentric' },
    { id: 'squeeze', label: 'Squeeze', to: 'peak', easing: 'hold', contraction: 'isometric' },
    { id: 'eccentric', label: 'Lower', to: 'start', easing: 'lift', contraction: 'eccentric' },
    { id: 'reset', label: 'Reset', to: 'start', easing: 'hold', contraction: 'isometric' },
  ],

  tempo: { eccentric: 2, pauseStretched: 0.5, concentric: 2, pauseContracted: 1 },

  hands: { grip: 'dumbbell', orientation: 'supinated', closure: 0.85, width: 0.42 },
  feet: { width: 0.32, toeOut: 6, planted: true },

  locks: [
    { id: 'foot_l', chain: 'leg_l', mode: 'floor', enabled: true },
    { id: 'foot_r', chain: 'leg_r', mode: 'floor', enabled: true },
  ],

  muscles: {
    primary: ['biceps'],
    secondary: ['forearm_flexors', 'deltoid_anterior'],
    stabilisers: ['trapezius_upper', 'erector_lower', 'rectus_abdominis', 'obliques'],
  },

  technique: [
    {
      kind: 'stationary',
      id: 'feet_planted_l',
      label: 'Left foot stays planted',
      point: { bone: 'foot_l' },
      tolerance: 0.012,
      severity: 'error',
    },
    {
      kind: 'stationary',
      id: 'feet_planted_r',
      label: 'Right foot stays planted',
      point: { bone: 'foot_r' },
      tolerance: 0.012,
      severity: 'error',
    },
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
    {
      kind: 'jointAngle',
      id: 'upper_arm_clear_l',
      label: 'Left upper arm stays slightly clear of the torso',
      bone: 'upperarm_l',
      axis: 'z',
      min: -20,
      max: -3,
    },
    {
      kind: 'jointAngle',
      id: 'upper_arm_clear_r',
      label: 'Right upper arm stays slightly clear of the torso',
      bone: 'upperarm_r',
      axis: 'z',
      min: 3,
      max: 20,
    },
    {
      kind: 'relativePosition',
      id: 'elbow_not_inward_l',
      label: 'Left elbow does not tuck in towards the chest',
      point: { bone: 'forearm_l' },
      relativeTo: { bone: 'spine_03' },
      axis: 'x',
      max: -0.13,
    },
    {
      kind: 'relativePosition',
      id: 'elbow_not_inward_r',
      label: 'Right elbow does not tuck in towards the chest',
      point: { bone: 'forearm_r' },
      relativeTo: { bone: 'spine_03' },
      axis: 'x',
      min: 0.13,
    },
    {
      kind: 'relativePosition',
      id: 'elbow_under_shoulder_l',
      label: 'Left elbow stays roughly below the shoulder',
      point: { bone: 'forearm_l' },
      relativeTo: { bone: 'upperarm_l' },
      axis: 'z',
      min: -0.06,
      max: 0.12,
    },
    {
      kind: 'relativePosition',
      id: 'elbow_under_shoulder_r',
      label: 'Right elbow stays roughly below the shoulder',
      point: { bone: 'forearm_r' },
      relativeTo: { bone: 'upperarm_r' },
      axis: 'z',
      min: -0.06,
      max: 0.12,
    },
    {
      kind: 'jointAngle',
      id: 'shoulder_quiet_l',
      label: 'Left shoulder does not take over the lift',
      bone: 'upperarm_l',
      axis: 'x',
      min: -5,
      max: 25,
    },
    {
      kind: 'jointAngle',
      id: 'shoulder_quiet_r',
      label: 'Right shoulder does not take over the lift',
      bone: 'upperarm_r',
      axis: 'x',
      min: -5,
      max: 25,
    },
    {
      kind: 'jointAngle',
      id: 'wrist_neutral_l',
      label: 'Left wrist stays neutral',
      bone: 'hand_l',
      axis: 'z',
      min: -12,
      max: 15,
    },
    {
      kind: 'jointAngle',
      id: 'wrist_neutral_r',
      label: 'Right wrist stays neutral',
      bone: 'hand_r',
      axis: 'z',
      min: -15,
      max: 12,
    },
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
    {
      kind: 'symmetry',
      id: 'dumbbells_aligned',
      label: 'Both dumbbells stay level with one another',
      left: { bone: 'hand_l', along: 1 },
      right: { bone: 'hand_r', along: 1 },
      tolerance: 0.03,
      severity: 'error',
    },
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
      id: 'elbow_drift',
      label: 'Elbows drifting forward',
      description: 'The elbows travel forward so the front delts take the work.',
      ruleId: 'elbow_under_shoulder_l',
      correction: 'Keep the elbows pinned under the shoulders through the whole range.',
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
  },
};
