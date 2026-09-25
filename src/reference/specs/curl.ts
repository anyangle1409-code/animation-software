import type { ExerciseDefinition } from '../../exercises/types';
import type { ReferenceCheckSpec, ReferenceSpec } from '../types';

const GRIP_ENVELOPES = {
  supinated: { min: 55, max: 90 },
  neutral: { min: -15, max: 20 },
  pronated: { min: -80, max: -45 },
} as const;

/**
 * Independent v1 curl envelope.
 *
 * These are deliberately broader than any one authored curl. They describe the
 * movement family, not the current builder's exact values: nearly straight at
 * the bottom, strongly flexed at peak, a quiet upper arm, a held forearm
 * orientation, neutral wrist and a stable torso.
 *
 * Before this reference can move from "draft" to "certified", the numeric
 * envelopes must be reviewed as reference data in their own right. Runtime code
 * must never populate them from curlFamily().
 */
export function curlReferenceFor(exercise: ExerciseDefinition): ReferenceSpec {
  const incline = exercise.equipment.required.includes('incline_bench');
  const orientation = exercise.hands.orientation;
  if (orientation === 'rotating') {
    throw new Error('curl reference v1 does not certify a rotating forearm grip');
  }

  const grip = GRIP_ENVELOPES[orientation];
  const checks: ReferenceCheckSpec[] = [
    {
      kind: 'phaseOrder',
      id: 'curl_phase_order',
      label: 'Curl phases follow lift, squeeze, lower, reset',
      order: ['concentric', 'squeeze', 'eccentric', 'reset'],
    },
    {
      kind: 'jointEnvelope',
      id: 'elbow_bottom',
      label: 'Elbow returns close to extension',
      bone: 'forearm_l',
      axis: 'x',
      phases: ['reset'],
      envelope: { min: 5, max: 30 },
    },
    {
      kind: 'jointEnvelope',
      id: 'elbow_peak',
      label: 'Elbow reaches a full curl',
      bone: 'forearm_l',
      axis: 'x',
      phases: ['squeeze'],
      envelope: { min: 115, max: 140 },
    },
    {
      kind: 'jointExcursion',
      id: 'elbow_rom',
      label: 'Elbow uses a substantial curl range',
      bone: 'forearm_l',
      axis: 'x',
      envelope: { min: 90, max: 130 },
    },
    {
      kind: 'jointEnvelope',
      id: 'upper_arm_sagittal',
      label: incline ? 'Upper arm hangs behind the inclined torso' : 'Upper arm stays close to vertical',
      bone: 'upperarm_l',
      axis: 'x',
      envelope: incline ? { min: -50, max: -30 } : { min: -5, max: 15 },
    },
    {
      kind: 'jointExcursion',
      id: 'upper_arm_excursion',
      label: 'Upper arm does not take over the curl',
      bone: 'upperarm_l',
      axis: 'x',
      envelope: { min: 0, max: 12 },
    },
    {
      kind: 'jointEnvelope',
      id: 'upper_arm_abduction',
      label: incline ? 'Arms clear the incline bench without flaring' : 'Arms stay near the torso without pinning into it',
      bone: 'upperarm_l',
      axis: 'z',
      envelope: incline ? { min: -25, max: -12 } : { min: -20, max: -2 },
    },
    {
      kind: 'jointEnvelope',
      id: 'grip_orientation',
      label: `Forearm holds the declared ${orientation} grip`,
      bone: 'forearm_l',
      axis: 'y',
      envelope: grip,
    },
    {
      kind: 'jointEnvelope',
      id: 'wrist_flexion',
      label: 'Wrist stays neutral in flexion and extension',
      bone: 'hand_l',
      axis: 'x',
      envelope: { min: -10, max: 10 },
    },
    {
      kind: 'jointEnvelope',
      id: 'wrist_deviation',
      label: 'Wrist stays neutral side to side',
      bone: 'hand_l',
      axis: 'z',
      envelope: { min: -12, max: 15 },
    },
    {
      kind: 'jointEnvelope',
      id: 'torso_local',
      label: 'Spine stays quiet through the repetition',
      bone: 'spine_02',
      axis: 'x',
      envelope: { min: -8, max: 8 },
    },
    {
      kind: 'jointEnvelope',
      id: 'shoulder_relaxed',
      label: 'Clavicle does not shrug through the repetition',
      bone: 'clavicle_l',
      axis: 'z',
      envelope: { min: 0, max: 10 },
    },
    {
      kind: 'rootEnvelope',
      id: 'support_angle',
      label: incline ? 'Body remains on an incline support' : 'Standing curl remains upright',
      axis: 'x',
      envelope: incline ? { min: -50, max: -40 } : { min: -5, max: 5 },
    },
    {
      kind: 'bilateralSymmetry',
      id: 'elbow_symmetry',
      label: 'Both elbows flex together',
      left: 'forearm_l',
      right: 'forearm_r',
      axis: 'x',
      toleranceDeg: 0.25,
    },
    {
      kind: 'bilateralSymmetry',
      id: 'grip_symmetry',
      label: 'Both forearms hold mirrored grip angles',
      left: 'forearm_l',
      right: 'forearm_r',
      axis: 'y',
      toleranceDeg: 0.25,
    },
    {
      kind: 'bilateralSymmetry',
      id: 'upper_arm_symmetry',
      label: 'Both upper arms follow the same sagittal motion',
      left: 'upperarm_l',
      right: 'upperarm_r',
      axis: 'x',
      toleranceDeg: 0.25,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'hand_rises',
      label: 'Held dumbbell rises without a mid-lift reversal',
      bone: 'hand_l',
      axis: 'y',
      phase: 'concentric',
      direction: 'increasing',
      tolerance: 0.02,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'hand_lowers',
      label: 'Held dumbbell lowers without a mid-lowering reversal',
      bone: 'hand_l',
      axis: 'y',
      phase: 'eccentric',
      direction: 'decreasing',
      tolerance: 0.02,
    },
  ];

  return {
    schemaVersion: 1,
    id: incline ? `curl.incline.${orientation}.v1` : `curl.standing.${orientation}.v1`,
    referenceVersion: 1,
    family: 'curl',
    status: 'draft',
    applicability: { handOrientation: orientation, support: incline ? 'incline' : 'standing' },
    provenance:
      'HOME GYM PT internal reference draft. Values are stored independently of curlFamily and require explicit reference review before certification.',
    checks,
  };
}
