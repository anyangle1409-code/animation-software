import type { ExerciseDefinition } from '../../exercises/types';
import type { ReferenceCheckSpec, ReferenceSpec } from '../types';

export function calfReferenceFor(exercise: ExerciseDefinition): ReferenceSpec {
  const loaded = exercise.equipment.required.includes('dumbbell');
  const checks: ReferenceCheckSpec[] = [
    {
      kind: 'phaseOrder',
      id: 'calf_phase_order',
      label: 'Calf raise follows rise, top, lower, heels down',
      order: ['concentric', 'top', 'eccentric', 'stretch'],
    },
    {
      kind: 'jointEnvelope',
      id: 'calf_top_plantarflexion',
      label: 'Foot reaches a high heel-raised position',
      bone: 'foot_l',
      axis: 'x',
      phases: ['top'],
      envelope: { min: -50, max: -20 },
    },
    {
      kind: 'jointEnvelope',
      id: 'calf_bottom_heel',
      label: 'Heel returns near the floor',
      bone: 'foot_l',
      axis: 'x',
      phases: ['stretch'],
      envelope: { min: -8, max: 8 },
    },
    {
      kind: 'jointEnvelope',
      id: 'calf_knee_quiet',
      label: 'Knee stays nearly straight',
      bone: 'shin_l',
      axis: 'x',
      envelope: { min: -12, max: 4 },
    },
    {
      kind: 'segmentAngleEnvelope',
      id: 'calf_torso_upright',
      label: 'Torso stays upright',
      bone: 'spine_02',
      worldAxis: 'y',
      envelope: { min: 0, max: 8 },
    },
    {
      kind: 'landmarkStationary',
      id: 'calf_left_toe_fixed',
      label: 'Left ball/toe contact stays planted',
      bone: 'toe_l',
      normalizeBy: 'standingHeight',
      tolerance: 0.008,
    },
    {
      kind: 'landmarkStationary',
      id: 'calf_right_toe_fixed',
      label: 'Right ball/toe contact stays planted',
      bone: 'toe_r',
      normalizeBy: 'standingHeight',
      tolerance: 0.008,
    },
    {
      kind: 'bilateralSymmetry',
      id: 'calf_foot_symmetry',
      label: 'Both ankles rise together',
      left: 'foot_l',
      right: 'foot_r',
      axis: 'x',
      toleranceDeg: 1.0,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'calf_body_rises',
      label: 'Body rises without reversal',
      bone: 'pelvis',
      axis: 'y',
      phase: 'concentric',
      direction: 'increasing',
      tolerance: 0.008,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'calf_body_lowers',
      label: 'Body lowers without reversal',
      bone: 'pelvis',
      axis: 'y',
      phase: 'eccentric',
      direction: 'decreasing',
      tolerance: 0.008,
    },
  ];

  return {
    schemaVersion: 1,
    id: loaded ? 'calf.dumbbell_standing.v1' : 'calf.bodyweight_standing.v1',
    referenceVersion: 1,
    family: 'calf',
    status: 'draft',
    applicability: { handOrientation: exercise.hands.orientation, support: 'standing' },
    provenance:
      'HOME GYM PT internal standing-calf-raise reference draft. Independent review required before certification.',
    reviewViews: [
      { id: 'side', label: 'Side', preset: 'right', target: 'full_body' },
      { id: 'front', label: 'Front', preset: 'front', target: 'full_body' },
      { id: 'three_quarter', label: 'Three-quarter', preset: 'three_quarter', target: 'full_body' },
      { id: 'feet', label: 'Feet and heels', preset: 'focus', target: 'feet' },
    ],
    checks,
  };
}
