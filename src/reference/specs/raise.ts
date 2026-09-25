import type { ExerciseDefinition } from '../../exercises/types';
import type { ReferenceCheckSpec, ReferenceSpec } from '../types';

export function raiseReferenceFor(exercise: ExerciseDefinition): ReferenceSpec {
  const front = /front_raise/.test(exercise.id) || /front_raise/.test(exercise.clipName);
  const grip = front ? { min: -85, max: -55 } : { min: -15, max: 20 };

  const checks: ReferenceCheckSpec[] = [
    {
      kind: 'phaseOrder',
      id: 'raise_phase_order',
      label: 'Raise follows lift, top, lower, reset',
      order: ['concentric', 'top', 'eccentric', 'bottom'],
    },
    {
      kind: 'segmentAngleEnvelope',
      id: 'raise_top_height',
      label: 'Upper arm reaches shoulder height',
      bone: 'upperarm_l',
      worldAxis: 'y',
      phases: ['top'],
      envelope: { min: 72, max: 100 },
    },
    {
      kind: 'jointEnvelope',
      id: 'raise_soft_elbow',
      label: 'Elbow stays softly bent',
      bone: 'forearm_l',
      axis: 'x',
      envelope: { min: 5, max: 30 },
    },
    {
      kind: 'segmentAngleEnvelope',
      id: 'raise_torso_upright',
      label: 'Torso stays upright',
      bone: 'spine_02',
      worldAxis: 'y',
      envelope: { min: 0, max: 10 },
    },
    {
      kind: 'jointEnvelope',
      id: 'raise_no_shrug',
      label: 'Clavicle stays down',
      bone: 'clavicle_l',
      axis: 'z',
      envelope: { min: -8, max: 8 },
    },
    {
      kind: 'jointEnvelope',
      id: 'raise_grip_orientation',
      label: front ? 'Front raise keeps a pronated grip' : 'Lateral raise keeps a neutral grip',
      bone: 'forearm_l',
      axis: 'y',
      envelope: grip,
    },
    {
      kind: 'bilateralSymmetry',
      id: 'raise_arm_x_symmetry',
      label: 'Both arms match in flexion',
      left: 'upperarm_l',
      right: 'upperarm_r',
      axis: 'x',
      toleranceDeg: 0.75,
    },
    {
      kind: 'bilateralSymmetry',
      id: 'raise_arm_z_symmetry',
      label: 'Both arms match in abduction',
      left: 'upperarm_l',
      right: 'upperarm_r',
      axis: 'z',
      toleranceDeg: 0.75,
    },
    {
      kind: 'landmarkDistanceEnvelope',
      id: 'raise_hands_level',
      label: 'Hands stay level',
      from: 'hand_l',
      to: 'hand_r',
      axis: 'y',
      envelope: { min: 0, max: 0.04 },
    },
    {
      kind: 'landmarkStationary',
      id: 'raise_left_foot_still',
      label: 'Left foot stays planted',
      bone: 'foot_l',
      normalizeBy: 'standingHeight',
      tolerance: 0.01,
    },
    {
      kind: 'landmarkStationary',
      id: 'raise_right_foot_still',
      label: 'Right foot stays planted',
      bone: 'foot_r',
      normalizeBy: 'standingHeight',
      tolerance: 0.01,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'raise_hand_rises',
      label: 'Hand rises without reversal',
      bone: 'hand_l',
      axis: 'y',
      phase: 'concentric',
      direction: 'increasing',
      tolerance: 0.015,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'raise_hand_lowers',
      label: 'Hand lowers without reversal',
      bone: 'hand_l',
      axis: 'y',
      phase: 'eccentric',
      direction: 'decreasing',
      tolerance: 0.015,
    },
  ];

  return {
    schemaVersion: 1,
    id: front ? 'raise.front_dumbbell.v1' : 'raise.lateral_dumbbell.v1',
    referenceVersion: 1,
    family: 'raise',
    status: 'draft',
    applicability: { handOrientation: exercise.hands.orientation, support: 'standing' },
    provenance:
      'HOME GYM PT internal shoulder-raise reference draft. Independent review required before certification.',
    reviewViews: [
      { id: 'front', label: 'Front', preset: 'front', target: 'full_body' },
      { id: 'side', label: 'Side', preset: 'right', target: 'full_body' },
      { id: 'three_quarter', label: 'Three-quarter', preset: 'three_quarter', target: 'upper_body' },
      { id: 'shoulders', label: 'Shoulder close-up', preset: 'focus', target: 'shoulders' },
    ],
    checks,
  };
}
