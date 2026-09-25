import type { ExerciseDefinition } from '../../exercises/types';
import type { ReferenceCheckSpec, ReferenceSpec } from '../types';

export function trunkFlexionReferenceFor(exercise: ExerciseDefinition): ReferenceSpec {
  const situp = /sit_up/.test(exercise.id) || /sit_up/.test(exercise.clipName);
  const checks: ReferenceCheckSpec[] = [
    {
      kind: 'phaseOrder',
      id: 'trunk_phase_order',
      label: 'Trunk flexion follows rise, top, lower, bottom',
      order: ['concentric', 'top', 'eccentric', 'bottom'],
    },
    {
      kind: 'jointEnvelope',
      id: 'trunk_neck_control',
      label: 'Neck stays controlled rather than folding into the chest',
      bone: 'neck',
      axis: 'x',
      envelope: { min: -25, max: 12 },
    },
    {
      kind: 'landmarkStationary',
      id: 'trunk_left_foot_fixed',
      label: 'Left foot stays planted',
      bone: 'foot_l',
      normalizeBy: 'standingHeight',
      tolerance: 0.012,
    },
    {
      kind: 'landmarkStationary',
      id: 'trunk_right_foot_fixed',
      label: 'Right foot stays planted',
      bone: 'foot_r',
      normalizeBy: 'standingHeight',
      tolerance: 0.012,
    },
    {
      kind: 'bilateralSymmetry',
      id: 'trunk_arm_symmetry',
      label: 'Both arms move symmetrically',
      left: 'upperarm_l',
      right: 'upperarm_r',
      axis: 'x',
      toleranceDeg: 1.0,
    },
  ];

  if (situp) {
    checks.push(
      {
        kind: 'segmentAngleEnvelope',
        id: 'situp_top_angle',
        label: 'Sit-up reaches near-upright sitting',
        bone: 'spine_02',
        worldAxis: 'y',
        phases: ['top'],
        envelope: { min: 0, max: 32 },
      },
      {
        kind: 'segmentAngleEnvelope',
        id: 'situp_bottom_angle',
        label: 'Sit-up returns fully to the floor',
        bone: 'spine_02',
        worldAxis: 'y',
        phases: ['bottom'],
        envelope: { min: 72, max: 95 },
      },
      {
        kind: 'landmarkStationary',
        id: 'situp_pelvis_grounded',
        label: 'Pelvis stays close to its floor contact',
        bone: 'pelvis',
        normalizeBy: 'standingHeight',
        tolerance: 0.025,
      },
    );
  } else {
    checks.push(
      {
        kind: 'landmarkStationary',
        id: 'crunch_pelvis_grounded',
        label: 'Pelvis stays down during the crunch',
        bone: 'pelvis',
        normalizeBy: 'standingHeight',
        tolerance: 0.008,
      },
      {
        kind: 'segmentAngleEnvelope',
        id: 'crunch_lower_back_down',
        label: 'Lower back remains close to the floor',
        bone: 'spine_01',
        worldAxis: 'y',
        envelope: { min: 70, max: 95 },
      },
      {
        kind: 'relativeLandmarkEnvelope',
        id: 'crunch_shoulder_lift',
        label: 'Shoulders lift clearly above the pelvis at the top',
        point: 'upperarm_l',
        relativeTo: 'pelvis',
        axis: 'y',
        phases: ['top'],
        normalizeBy: 'standingHeight',
        envelope: { min: 0.05, max: 0.5 },
      },
    );
  }

  return {
    schemaVersion: 1,
    id: situp ? 'trunk_flexion.situp.v1' : 'trunk_flexion.crunch.v1',
    referenceVersion: 1,
    family: 'trunk_flexion',
    status: 'draft',
    applicability: { support: 'floor' },
    provenance:
      'HOME GYM PT internal floor trunk-flexion reference draft. Independent review required before certification.',
    reviewViews: [
      { id: 'side', label: 'Side', preset: 'right', target: 'full_body' },
      { id: 'three_quarter', label: 'Three-quarter', preset: 'three_quarter', target: 'full_body' },
      { id: 'front', label: 'Front', preset: 'front', target: 'full_body' },
    ],
    checks,
  };
}
