import type { ExerciseDefinition } from '../../exercises/types';
import type { ReferenceCheckSpec, ReferenceSpec } from '../types';

export function carryReferenceFor(exercise: ExerciseDefinition): ReferenceSpec {
  const checks: ReferenceCheckSpec[] = [
    {
      kind: 'phaseOrder',
      id: 'carry_phase_order',
      label: 'Carry alternates right and left steps',
      order: ['right_step', 'left_step'],
    },
    {
      kind: 'segmentAngleEnvelope',
      id: 'carry_tall',
      label: 'Trunk stays upright',
      bone: 'spine_02',
      worldAxis: 'y',
      envelope: { min: 0, max: 8 },
    },
    {
      kind: 'jointEnvelope',
      id: 'carry_hips_level',
      label: 'Pelvis does not side-bend',
      bone: 'pelvis',
      axis: 'z',
      envelope: { min: -5, max: 5 },
    },
    {
      kind: 'jointEnvelope',
      id: 'carry_shoulder_down',
      label: 'Shoulder stays down under the load',
      bone: 'clavicle_l',
      axis: 'z',
      envelope: { min: -8, max: 8 },
    },
    {
      kind: 'jointEnvelope',
      id: 'carry_arm_long',
      label: 'Elbow stays nearly straight',
      bone: 'forearm_l',
      axis: 'x',
      envelope: { min: 0, max: 18 },
    },
    {
      kind: 'jointEnvelope',
      id: 'carry_neutral_grip',
      label: 'Forearm remains neutral',
      bone: 'forearm_l',
      axis: 'y',
      envelope: { min: -15, max: 20 },
    },
    {
      kind: 'jointEnvelope',
      id: 'carry_wrist_neutral',
      label: 'Wrist stays neutral',
      bone: 'hand_l',
      axis: 'z',
      envelope: { min: -15, max: 18 },
    },
    {
      kind: 'landmarkDistanceEnvelope',
      id: 'carry_hands_level',
      label: 'Both carried weights stay level',
      from: 'hand_l',
      to: 'hand_r',
      axis: 'y',
      envelope: { min: 0, max: 0.035 },
    },
    {
      kind: 'bilateralSymmetry',
      id: 'carry_arm_symmetry',
      label: 'Both carried arms remain matched',
      left: 'forearm_l',
      right: 'forearm_r',
      axis: 'x',
      toleranceDeg: 1.0,
    },
  ];

  return {
    schemaVersion: 1,
    id: 'carry.farmers_walk.v1',
    referenceVersion: 1,
    family: 'carry',
    status: 'draft',
    applicability: { handOrientation: exercise.hands.orientation, support: 'walking' },
    provenance:
      "HOME GYM PT internal farmer's-walk reference draft. Independent review required before certification.",
    reviewViews: [
      { id: 'side', label: 'Side', preset: 'right', target: 'full_body' },
      { id: 'front', label: 'Front', preset: 'front', target: 'full_body' },
      { id: 'three_quarter', label: 'Three-quarter', preset: 'three_quarter', target: 'full_body' },
      { id: 'hands', label: 'Grip close-up', preset: 'focus', target: 'hands' },
    ],
    checks,
  };
}
