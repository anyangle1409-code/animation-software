import type { ExerciseDefinition } from '../../exercises/types';
import type { ReferenceCheckSpec, ReferenceSpec } from '../types';

export function calfReferenceFor(exercise: ExerciseDefinition): ReferenceSpec {
  const loaded = exercise.equipment.required.includes('dumbbell');
  const checks: ReferenceCheckSpec[] = [
    {
      kind: 'phaseOrder',
      id: 'calf_phase_order',
      label: 'Calf raise follows rise, squeeze, lower, heels down',
      order: ['concentric', 'top', 'eccentric', 'stretch'],
    },
    {
      kind: 'rootPositionEnvelope',
      id: 'calf_root_rise',
      label: 'Body rises substantially onto the balls of the feet',
      axis: 'y',
      phases: ['top'],
      normalizeBy: 'standingHeight',
      envelope: { min: 0.025, max: 0.065 },
    },
    {
      kind: 'rootPositionEnvelope',
      id: 'calf_root_return',
      label: 'Body returns to its original height',
      axis: 'y',
      phases: ['stretch'],
      normalizeBy: 'standingHeight',
      envelope: { min: -0.01, max: 0.01 },
    },
    {
      kind: 'landmarkStationary',
      id: 'calf_left_ball_fixed',
      label: 'Left ball of the foot remains the pivot',
      bone: { bone: 'foot_l', along: 1 },
      normalizeBy: 'standingHeight',
      tolerance: 0.003,
    },
    {
      kind: 'landmarkStationary',
      id: 'calf_right_ball_fixed',
      label: 'Right ball of the foot remains the pivot',
      bone: { bone: 'foot_r', along: 1 },
      normalizeBy: 'standingHeight',
      tolerance: 0.003,
    },
    {
      kind: 'jointEnvelope',
      id: 'calf_knee_quiet',
      label: 'Knee stays soft but nearly straight',
      bone: 'shin_l',
      axis: 'x',
      envelope: { min: -12, max: 3 },
    },
    {
      kind: 'jointExcursion',
      id: 'calf_knee_excursion',
      label: 'Knee does not pump the body up',
      bone: 'shin_l',
      axis: 'x',
      envelope: { min: 0, max: 2 },
    },
    {
      kind: 'segmentAngleEnvelope',
      id: 'calf_torso_upright',
      label: 'Torso remains upright',
      bone: 'spine_02',
      worldAxis: 'y',
      envelope: { min: 0, max: 8 },
    },
    {
      kind: 'bilateralSymmetry',
      id: 'calf_knee_symmetry',
      label: 'Both knees remain matched',
      left: 'shin_l',
      right: 'shin_r',
      axis: 'x',
      toleranceDeg: 0.75,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'calf_body_rises',
      label: 'Body rises without a mid-lift reversal',
      bone: 'pelvis',
      axis: 'y',
      phase: 'concentric',
      direction: 'increasing',
      tolerance: 0.005,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'calf_body_lowers',
      label: 'Body lowers without a mid-lowering reversal',
      bone: 'pelvis',
      axis: 'y',
      phase: 'eccentric',
      direction: 'decreasing',
      tolerance: 0.005,
    },
    ...(loaded
      ? [
          {
            kind: 'jointEnvelope' as const,
            id: 'calf_loaded_grip',
            label: 'Dumbbells remain in a neutral grip at the sides',
            bone: 'forearm_l' as const,
            axis: 'y' as const,
            envelope: { min: -15, max: 15 },
          },
          {
            kind: 'jointEnvelope' as const,
            id: 'calf_loaded_wrist',
            label: 'Loaded wrist stays neutral',
            bone: 'hand_l' as const,
            axis: 'z' as const,
            envelope: { min: -15, max: 15 },
          },
        ]
      : []),
  ];

  return {
    schemaVersion: 1,
    id: `calf.${loaded ? 'dumbbell' : 'bodyweight'}.v1`,
    referenceVersion: 1,
    family: 'calf',
    status: 'draft',
    applicability: { ...(loaded ? { handOrientation: exercise.hands.orientation } : {}), support: 'standing' },
    provenance:
      'HOME GYM PT internal standing-calf-raise reference draft. The ball-of-foot pivot uses PointRef tail semantics and requires independent review before certification.',
    reviewViews: [
      { id: 'side', label: 'Side', preset: 'right', target: 'full_body' },
      { id: 'front', label: 'Front', preset: 'front', target: 'full_body' },
      { id: 'three_quarter', label: 'Three-quarter', preset: 'three_quarter', target: 'full_body' },
      { id: 'feet', label: 'Feet and ankles', preset: 'focus', target: 'feet' },
    ],
    checks,
  };
}
