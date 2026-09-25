import type { ExerciseDefinition } from '../../exercises/types';
import type { ReferenceCheckSpec, ReferenceSpec } from '../types';

export function lungeReferenceFor(exercise: ExerciseDefinition): ReferenceSpec {
  const stepping = exercise.id === 'forward_lunge' || exercise.id === 'reverse_lunge' || exercise.clipName.includes('lunge');
  const forward = exercise.id === 'forward_lunge';
  const reverse = exercise.id === 'reverse_lunge';
  const order = stepping ? ['step', 'bottom', 'drive', 'stand'] : ['eccentric', 'bottom', 'concentric', 'top'];

  const checks: ReferenceCheckSpec[] = [
    {
      kind: 'phaseOrder',
      id: 'lunge_phase_order',
      label: 'Lunge phases follow the certified variant',
      order,
    },
    {
      kind: 'segmentAngleEnvelope',
      id: 'lunge_torso',
      label: 'Torso remains upright',
      bone: 'spine_02',
      worldAxis: 'y',
      envelope: { min: 0, max: 15 },
    },
    {
      kind: 'jointEnvelope',
      id: 'lunge_spine_neutral',
      label: 'Lower back remains neutral',
      bone: 'spine_01',
      axis: 'x',
      envelope: { min: -6, max: 12 },
    },
    {
      kind: 'jointEnvelope',
      id: 'lunge_hips_square',
      label: 'Pelvis stays square to the front',
      bone: 'pelvis',
      axis: 'y',
      envelope: { min: -8, max: 8 },
    },
    {
      kind: 'relativeLandmarkEnvelope',
      id: 'lunge_depth',
      label: 'Back knee reaches close to floor height',
      point: 'shin_r',
      relativeTo: 'foot_l',
      axis: 'y',
      phases: ['bottom'],
      normalizeBy: 'standingHeight',
      envelope: { min: -0.03, max: 0.08 },
    },
    {
      kind: 'relativeLandmarkEnvelope',
      id: 'lunge_front_knee_track',
      label: 'Front knee tracks near the front foot',
      point: 'shin_l',
      relativeTo: 'foot_l',
      axis: 'x',
      phases: ['bottom'],
      normalizeBy: 'shoulderWidth',
      envelope: { min: -0.2, max: 0.2 },
    },
    {
      kind: 'relativeLandmarkEnvelope',
      id: 'lunge_front_knee_foreaft',
      label: 'Front knee does not travel excessively beyond the foot',
      point: 'shin_l',
      relativeTo: 'foot_l',
      axis: 'z',
      phases: ['bottom'],
      normalizeBy: 'standingHeight',
      envelope: { min: -0.15, max: 0.09 },
    },
  ];

  if (!forward) {
    checks.push({
      kind: 'landmarkStationary',
      id: 'lunge_front_foot_still',
      label: 'Front foot stays planted',
      bone: 'foot_l',
      normalizeBy: 'standingHeight',
      tolerance: 0.015,
    });
  }
  if (!reverse) {
    checks.push({
      kind: 'landmarkStationary',
      id: 'lunge_back_contact_still',
      label: 'Back contact stays planted',
      bone: 'toe_r',
      normalizeBy: 'standingHeight',
      tolerance: 0.015,
    });
  }
  if (forward) {
    checks.push({
      kind: 'relativeLandmarkEnvelope',
      id: 'lunge_step_length',
      label: 'Forward lunge uses a long step',
      point: 'foot_l',
      relativeTo: 'toe_r',
      axis: 'z',
      phases: ['bottom'],
      normalizeBy: 'standingHeight',
      envelope: { min: 0.35, max: 0.65 },
    });
  }
  if (reverse) {
    checks.push({
      kind: 'relativeLandmarkEnvelope',
      id: 'lunge_step_length',
      label: 'Reverse lunge uses a long step back',
      point: 'toe_r',
      relativeTo: 'foot_l',
      axis: 'z',
      phases: ['bottom'],
      normalizeBy: 'standingHeight',
      envelope: { min: -0.65, max: -0.35 },
    });
  }

  const variant = forward ? 'forward' : reverse ? 'reverse' : 'split_squat';
  return {
    schemaVersion: 1,
    id: `lunge.${variant}.v1`,
    referenceVersion: 1,
    family: 'lunge',
    status: 'draft',
    applicability: { support: 'standing' },
    provenance:
      'HOME GYM PT internal lunge reference draft. Static and stepping variants use separate phase expectations and require independent review.',
    reviewViews: [
      { id: 'side', label: 'Side', preset: 'right', target: 'full_body' },
      { id: 'front', label: 'Front', preset: 'front', target: 'full_body' },
      { id: 'three_quarter', label: 'Three-quarter', preset: 'three_quarter', target: 'full_body' },
      { id: 'feet', label: 'Feet and knees', preset: 'focus', target: 'feet' },
    ],
    checks,
  };
}
