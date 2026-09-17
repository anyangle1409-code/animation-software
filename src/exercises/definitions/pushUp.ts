import { SHOULDER_WIDENING } from '../../rig/humanoid';
import type { ExerciseDefinition } from '../types';
import { vec3 } from '../../rig/types';

/**
 * Standard push-up.
 *
 * Tests the hardest part of the engine: the body is supported on four contacts
 * at once, so the root moves and the limbs are solved backwards from hands and
 * feet that must not move at all. The root placement is computed so the toes
 * stay pinned while the body pivots on them, and world locks hold the hands.
 */

/** Where the toes are planted, and the root placement that pins them there. */
const TOP = { pitch: 74, root: { y: 0.1758, z: -0.0004 } };
const BOTTOM = { pitch: 84, root: { y: 0.2025, z: 0.0327 } };

/**
 * Hands stay exactly here for the whole repetition. The placement is not a
 * guess: it is where the forearms come out vertical at the bottom with the
 * elbows at about 40° from the torso, which is the technique this exercise is
 * defined by.
 */
// Forward placement is derived, not inherited. On the locked Stage 2 anatomy the
// old z of 1.24 put true wrist extension at 92.1°, past the roughly 70-80° the
// human wrist has, and the forearm read as a flattened strap. Measured through
// the twist/swing decomposition that accounts for the 14.62° hand-to-forearm
// bind offset, extension falls monotonically as the hands move forward:
// 1.24 -> 92.1°, 1.30 -> 80.3°, 1.34 -> 73.9°, 1.36 -> 71.0°, 1.42 -> 63.6°.
//
// 1.34 is the smallest move that sits inside the 70-75° working band with margin
// at both ends. That is +100 mm, NOT the historical ~200 mm estimate, which this
// measurement does not support.
const HAND_L = vec3(-0.3, 0.055, 1.295);
const HAND_R = vec3(0.3, 0.055, 1.295);

/** Elbows are pulled back towards the feet and out, giving the 30–45° flare. */
const ELBOW_POLE_L = vec3(-0.55, 0.34, 1.05);
const ELBOW_POLE_R = vec3(0.55, 0.34, 1.05);

const bodyJoints = {
  // The trunk is held rigid: a push-up is one unit, not a spine exercise.
  spine_01: { x: 0 },
  spine_02: { x: 0 },
  spine_03: { x: 0 },
  neck: { x: -25 },
  head: { x: -10 },
  // Toes tucked under, which is what puts the body on the balls of the feet.
  foot_l: { x: 25 },
  foot_r: { x: 25 },
  // A starting guess for the arms; the hand locks solve them exactly.
  upperarm_l: { x: 85, z: -14 },
  upperarm_r: { x: 85, z: 14 },
};

export const pushUp: ExerciseDefinition = {
  id: 'push_up',
  name: 'Push-Up',
  clipName: 'push_up',
  category: 'upper_push',
  description:
    'Bodyweight push-up with the hands slightly wider than the shoulders. The ' +
    'body travels as one rigid unit between four fixed contacts.',

  equipment: { required: [], instances: [] },

  startPose: {
    label: 'Top',
    joints: bodyJoints,
    root: { position: { y: TOP.root.y, z: TOP.root.z }, rotation: { x: TOP.pitch } },
  },

  peakPose: {
    label: 'Bottom',
    joints: { ...bodyJoints, upperarm_l: { x: 62, z: -34 }, upperarm_r: { x: 62, z: 34 } },
    root: { position: { y: BOTTOM.root.y, z: BOTTOM.root.z }, rotation: { x: BOTTOM.pitch } },
  },

  jointTargets: [
    // The elbow angles the hand locks produce; listed because they are what a
    // coach would describe, and checked by the technique rules below.
    { bone: 'forearm_l', axis: 'x', start: 18, peak: 90, role: 'prime' },
    { bone: 'forearm_r', axis: 'x', start: 18, peak: 90, role: 'prime' },
  ],

  phases: [
    { id: 'eccentric', label: 'Lower', to: 'peak', easing: 'lift', contraction: 'eccentric' },
    { id: 'bottom', label: 'Bottom', to: 'peak', easing: 'hold', contraction: 'isometric' },
    { id: 'concentric', label: 'Press', to: 'start', easing: 'lift', contraction: 'concentric' },
    { id: 'top', label: 'Lockout', to: 'start', easing: 'hold', contraction: 'isometric' },
  ],

  tempo: { eccentric: 1.6, pauseStretched: 0.4, concentric: 1.2, pauseContracted: 0.3 },

  hands: { grip: 'floor', orientation: 'pronated', closure: 0.05, width: 0.667 },
  feet: { width: 0.18, toeOut: 0, planted: true },

  locks: [
    {
      id: 'hand_l',
      chain: 'arm_l',
      mode: 'world',
      position: HAND_L,
      pole: ELBOW_POLE_L,
      // Palms flat: fingers point forward, thumbs turned slightly inward.
      aim: { direction: vec3(0, 0, 1), forward: vec3(1, 0, 0) },
      enabled: true,
    },
    {
      id: 'hand_r',
      chain: 'arm_r',
      mode: 'world',
      position: HAND_R,
      pole: ELBOW_POLE_R,
      aim: { direction: vec3(0, 0, 1), forward: vec3(-1, 0, 0) },
      enabled: true,
    },
  ],

  muscles: {
    primary: ['pectoralis', 'triceps', 'deltoid_anterior'],
    secondary: ['rectus_abdominis', 'deltoid_medial'],
    stabilisers: [
      'obliques',
      'erector_lower',
      'erector_mid',
      'gluteus',
      'quadriceps',
      'trapezius_mid',
      'forearm_flexors',
    ],
  },

  technique: [
    {
      kind: 'stationary',
      id: 'hand_planted_l',
      label: 'Left hand stays planted',
      point: { bone: 'hand_l' },
      tolerance: 0.01,
      severity: 'error',
    },
    {
      kind: 'stationary',
      id: 'hand_planted_r',
      label: 'Right hand stays planted',
      point: { bone: 'hand_r' },
      tolerance: 0.01,
      severity: 'error',
    },
    {
      kind: 'stationary',
      id: 'toes_planted_l',
      label: 'Left foot stays planted',
      point: { bone: 'toe_l', along: 1 },
      tolerance: 0.012,
      severity: 'error',
    },
    {
      kind: 'stationary',
      id: 'toes_planted_r',
      label: 'Right foot stays planted',
      point: { bone: 'toe_r', along: 1 },
      tolerance: 0.012,
      severity: 'error',
    },
    {
      kind: 'distance',
      id: 'hands_width',
      label: 'Hands are shoulder-width or slightly wider',
      from: { bone: 'hand_l' },
      to: { bone: 'hand_r' },
      axis: 'x',
      min: 0.547,
      max: 0.747,
    },
    {
      kind: 'relativePosition',
      id: 'elbow_flare_l',
      label: 'Left elbow stays 30–45° from the torso, not flared wide',
      point: { bone: 'forearm_l' },
      relativeTo: { bone: 'upperarm_l' },
      axis: 'x',
      min: -0.26,
      max: -0.07,
    },
    {
      kind: 'relativePosition',
      id: 'elbow_flare_r',
      label: 'Right elbow stays 30–45° from the torso, not flared wide',
      point: { bone: 'forearm_r' },
      relativeTo: { bone: 'upperarm_r' },
      axis: 'x',
      min: 0.07,
      max: 0.26,
    },
    {
      kind: 'relativePosition',
      id: 'elbow_behind_l',
      label: 'Left elbow tracks back towards the feet',
      point: { bone: 'forearm_l' },
      relativeTo: { bone: 'upperarm_l' },
      axis: 'z',
      min: -0.3,
      max: -0.04,
    },
    {
      kind: 'relativePosition',
      id: 'elbow_behind_r',
      label: 'Right elbow tracks back towards the feet',
      point: { bone: 'forearm_r' },
      relativeTo: { bone: 'upperarm_r' },
      axis: 'z',
      min: -0.3,
      max: -0.04,
    },
    {
      kind: 'distance',
      id: 'forearm_vertical_l',
      label: 'Left forearm is near vertical at the bottom',
      from: { bone: 'forearm_l' },
      to: { bone: 'hand_l' },
      axis: 'z',
      max: 0.06,
      phases: ['bottom'],
    },
    {
      kind: 'distance',
      id: 'forearm_vertical_r',
      label: 'Right forearm is near vertical at the bottom',
      from: { bone: 'forearm_r' },
      to: { bone: 'hand_r' },
      axis: 'z',
      max: 0.06,
      phases: ['bottom'],
    },
    {
      kind: 'alignment',
      id: 'body_line',
      label: 'Head, hips and ankles stay in one line',
      // Shoulder, hip and ankle: the line a coach actually looks down.
      points: [{ bone: 'upperarm_l' }, { bone: 'thigh_l' }, { bone: 'foot_l' }],
      // All three points are left-side, so the deviation carries a constant
      // lateral term — a shoulder is simply wider than a hip — on top of the
      // sagittal sag or pike the rule exists to catch. Measured, the sagittal
      // deviation is 0.0000 at every frame and the whole 0.0669 is that lateral
      // constant, which Stage 2 grew by exactly SHOULDER_WIDENING. Carrying the
      // same amount into the tolerance leaves the sagittal margin at 26.8 mm,
      // precisely what it was before the shoulder moved.
      tolerance: 0.06 + SHOULDER_WIDENING,
      severity: 'error',
    },
    {
      kind: 'jointAngle',
      id: 'no_hip_sag',
      label: 'Hips neither sag nor pike',
      bone: 'spine_01',
      axis: 'x',
      min: -6,
      max: 6,
      severity: 'error',
    },
    {
      kind: 'jointAngle',
      id: 'trunk_rigid',
      label: 'Trunk stays rigid through the movement',
      bone: 'spine_02',
      axis: 'x',
      min: -6,
      max: 6,
    },
    {
      kind: 'symmetry',
      id: 'even_press',
      label: 'Both sides press evenly',
      left: { bone: 'forearm_l' },
      right: { bone: 'forearm_r' },
      tolerance: 0.02,
      severity: 'error',
    },
  ],

  commonErrors: [
    {
      id: 'hip_sag',
      label: 'Hips sagging',
      description: 'The lower back gives way and the hips drop below the body line.',
      ruleId: 'no_hip_sag',
      correction: 'Brace the abdominals and squeeze the glutes to hold one straight line.',
    },
    {
      id: 'elbow_flare',
      label: 'Elbows flared to 90°',
      description: 'The upper arms go straight out sideways, loading the shoulder joint.',
      ruleId: 'elbow_flare_l',
      correction: 'Point the elbows back at roughly 45°, so the forearms stay vertical.',
    },
    {
      id: 'partial_depth',
      label: 'Stopping short',
      description: 'The chest never approaches the floor, so the range is cut.',
      correction: 'Lower until the upper arms are at least parallel with the floor.',
    },
    {
      id: 'head_drop',
      label: 'Leading with the head',
      description: 'The chin reaches for the floor before the chest does.',
      ruleId: 'body_line',
      correction: 'Keep the head in line with the spine and let the chest lead.',
    },
  ],

  breathing: {
    inhale: 'eccentric',
    exhale: 'concentric',
    cue: 'Breathe in on the way down, out as you press away from the floor.',
  },

  camera: {
    preset: 'right',
    position: vec3(3.1, 0.85, 1.1),
    target: vec3(0, 0.35, 0.75),
    fov: 40,
    note: 'A side view is the only angle that shows the body line and elbow position together.',
  },
};
