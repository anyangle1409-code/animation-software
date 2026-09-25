import type { ExerciseDefinition } from '../../exercises/types';
import type { ReferenceCheckSpec, ReferenceSpec } from '../types';

/**
 * Independent draft envelope for the strict pronated pull-up.
 *
 * The values are intentionally broader than the current authored pullUp. They
 * describe the movement: hands fixed to a bar, full hang, strong elbow flexion
 * at the top, quiet hips and a mostly vertical trunk.
 */
export function verticalPullReferenceFor(exercise: ExerciseDefinition): ReferenceSpec {
  const checks: ReferenceCheckSpec[] = [
    {
      kind: 'phaseOrder',
      id: 'pullup_phase_order',
      label: 'Pull-up follows pull, top, lower, hang',
      order: ['concentric', 'top', 'eccentric', 'hang'],
    },
    {
      kind: 'landmarkStationary',
      id: 'left_grip_fixed',
      label: 'Left hand stays fixed on the bar',
      bone: 'hand_l',
      tolerance: 0.008,
    },
    {
      kind: 'landmarkStationary',
      id: 'right_grip_fixed',
      label: 'Right hand stays fixed on the bar',
      bone: 'hand_r',
      tolerance: 0.008,
    },
    {
      kind: 'landmarkDistanceEnvelope',
      id: 'pullup_grip_width',
      label: 'Grip remains around shoulder width or a little wider',
      from: 'hand_l',
      to: 'hand_r',
      axis: 'x',
      normalizeBy: 'shoulderWidth',
      envelope: { min: 1.05, max: 1.65 },
    },
    {
      kind: 'jointEnvelope',
      id: 'pullup_dead_hang',
      label: 'Elbows return close to straight in the hang',
      bone: 'forearm_l',
      axis: 'x',
      phases: ['hang'],
      envelope: { min: 0, max: 30 },
    },
    {
      kind: 'jointEnvelope',
      id: 'pullup_top_flexion',
      label: 'Elbows bend strongly at the top',
      bone: 'forearm_l',
      axis: 'x',
      phases: ['top'],
      envelope: { min: 105, max: 150 },
    },
    {
      kind: 'jointExcursion',
      id: 'pullup_elbow_rom',
      label: 'Elbows use a full pull-up range',
      bone: 'forearm_l',
      axis: 'x',
      envelope: { min: 90, max: 150 },
    },
    {
      kind: 'jointEnvelope',
      id: 'pullup_shoulder_motion',
      label: 'Shoulders move from elevated hang to depressed top',
      bone: 'clavicle_l',
      axis: 'z',
      envelope: { min: -20, max: 15 },
    },
    {
      kind: 'rootPositionEnvelope',
      id: 'pullup_hang_height',
      label: 'Body reaches a full hanging position',
      axis: 'y',
      phases: ['hang'],
      normalizeBy: 'standingHeight',
      envelope: { min: -0.10, max: 0.05 },
    },
    {
      kind: 'rootPositionEnvelope',
      id: 'pullup_top_height',
      label: 'Body rises substantially at the top',
      axis: 'y',
      phases: ['top'],
      normalizeBy: 'standingHeight',
      envelope: { min: 0.18, max: 0.38 },
    },
    {
      kind: 'relativeLandmarkEnvelope',
      id: 'pullup_no_kip',
      label: 'Hips stay behind or close to the bar line',
      point: 'pelvis',
      relativeTo: 'hand_l',
      axis: 'z',
      normalizeBy: 'standingHeight',
      envelope: { min: -0.22, max: 0.05 },
    },
    {
      kind: 'jointEnvelope',
      id: 'pullup_hips_quiet',
      label: 'Hip position stays quiet rather than driving the rep',
      bone: 'thigh_l',
      axis: 'x',
      envelope: { min: -22, max: 8 },
    },
    {
      kind: 'segmentAngleEnvelope',
      id: 'pullup_trunk_line',
      label: 'Trunk remains close to vertical',
      bone: 'spine_02',
      worldAxis: 'y',
      envelope: { min: 0, max: 22 },
    },
    {
      kind: 'bilateralSymmetry',
      id: 'pullup_elbow_symmetry',
      label: 'Both elbows pull together',
      left: 'forearm_l',
      right: 'forearm_r',
      axis: 'x',
      toleranceDeg: 1.0,
    },
    {
      kind: 'bilateralSymmetry',
      id: 'pullup_shoulder_symmetry',
      label: 'Both shoulders move together',
      left: 'clavicle_l',
      right: 'clavicle_r',
      axis: 'z',
      toleranceDeg: 1.0,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'pullup_body_rises',
      label: 'Pelvis rises through the pull without a reversal',
      bone: 'pelvis',
      axis: 'y',
      phase: 'concentric',
      direction: 'increasing',
      tolerance: 0.015,
    },
    {
      kind: 'landmarkMonotonic',
      id: 'pullup_body_lowers',
      label: 'Pelvis lowers under control without a reversal',
      bone: 'pelvis',
      axis: 'y',
      phase: 'eccentric',
      direction: 'decreasing',
      tolerance: 0.015,
    },
  ];

  return {
    schemaVersion: 1,
    id: 'vertical_pull.strict_pronated_pullup.v1',
    referenceVersion: 1,
    family: 'vertical_pull',
    status: 'draft',
    applicability: { handOrientation: exercise.hands.orientation, support: 'hanging' },
    provenance:
      'HOME GYM PT internal strict pull-up reference draft. It is stored independently from verticalPullFamily() and must be reviewed before certification.',
    reviewViews: [
      { id: 'front', label: 'Front', preset: 'front', target: 'full_body' },
      { id: 'side', label: 'Side', preset: 'right', target: 'full_body' },
      { id: 'three_quarter', label: 'Three-quarter', preset: 'three_quarter', target: 'full_body' },
      { id: 'grip_closeup', label: 'Grip close-up', preset: 'focus', target: 'hands' },
    ],
    checks,
  };
}
