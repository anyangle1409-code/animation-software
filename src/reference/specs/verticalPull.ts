import type { ExerciseDefinition } from '../../exercises/types';
import type { ReferenceCheckSpec, ReferenceSpec } from '../types';

export function verticalPullReferenceFor(exercise: ExerciseDefinition): ReferenceSpec {
  const checks: ReferenceCheckSpec[] = [
    {
      kind: 'phaseOrder',
      id: 'pull_phase_order',
      label: 'Pull-up follows pull, top, lower, hang',
      order: ['concentric', 'top', 'eccentric', 'hang'],
    },
    {
      kind: 'jointEnvelope',
      id: 'pull_full_hang',
      label: 'Elbows return close to straight at the hang',
      bone: 'forearm_l',
      axis: 'x',
      phases: ['hang'],
      envelope: { min: 0, max: 25 },
    },
    {
      kind: 'jointEnvelope',
      id: 'pull_top_flexion',
      label: 'Elbows reach strong flexion at the top',
      bone: 'forearm_l',
      axis: 'x',
      phases: ['top'],
      envelope: { min: 105, max: 150 },
    },
    {
      kind: 'jointExcursion',
      id: 'pull_elbow_rom',
      label: 'Elbows use a full pulling range',
      bone: 'forearm_l',
      axis: 'x',
      envelope: { min: 90, max: 150 },
    },
    {
      kind: 'segmentAngleEnvelope',
      id: 'pull_trunk_line',
      label: 'Trunk stays close to vertical',
      bone: 'spine_02',
      worldAxis: 'y',
      envelope: { min: 0, max: 20 },
    },
    {
      kind: 'jointEnvelope',
      id: 'pull_hips_quiet',
      label: 'Hips stay quiet without a kip',
      bone: 'thigh_l',
      axis: 'x',
      envelope: { min: -22, max: 8 },
    },
    {
      kind: 'landmarkStationary',
      id: 'pull_left_hand_fixed',
      label: 'Left hand stays fixed on the bar',
      bone: 'hand_l',
      normalizeBy: 'armLength',
      tolerance: 0.02,
    },
    {
      kind: 'landmarkStationary',
      id: 'pull_right_hand_fixed',
      label: 'Right hand stays fixed on the bar',
      bone: 'hand_r',
      normalizeBy: 'armLength',
      tolerance: 0.02,
    },
    {
      kind: 'bilateralSymmetry',
      id: 'pull_elbow_symmetry',
      label: 'Both elbows flex together',
      left: 'forearm_l',
      right: 'forearm_r',
      axis: 'x',
      toleranceDeg: 1,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'pull_body_rises',
      label: 'Body rises continuously during the pull',
      bone: 'pelvis',
      axis: 'y',
      phase: 'concentric',
      direction: 'increasing',
      tolerance: 0.02,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'pull_body_lowers',
      label: 'Body lowers continuously during the eccentric',
      bone: 'pelvis',
      axis: 'y',
      phase: 'eccentric',
      direction: 'decreasing',
      tolerance: 0.02,
    },
  ];

  return {
    schemaVersion: 1,
    id: 'vertical_pull.strict_pullup.v1',
    referenceVersion: 1,
    family: 'vertical_pull',
    status: 'draft',
    applicability: { handOrientation: exercise.hands.orientation, support: 'hanging' },
    provenance:
      'HOME GYM PT internal strict-pull-up reference draft. Independent review required before certification.',
    reviewViews: [
      { id: 'front', label: 'Front', preset: 'front', target: 'full_body' },
      { id: 'side', label: 'Side', preset: 'right', target: 'full_body' },
      { id: 'three_quarter', label: 'Three-quarter', preset: 'three_quarter', target: 'full_body' },
      { id: 'hands', label: 'Grip close-up', preset: 'focus', target: 'hands' },
    ],
    checks,
  };
}
