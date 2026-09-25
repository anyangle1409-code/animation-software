import type { ExerciseDefinition } from '../../exercises/types';
import type { ReferenceCheckSpec, ReferenceSpec } from '../types';

export function supineReferenceFor(exercise: ExerciseDefinition): ReferenceSpec {
  const fly = /fly/.test(exercise.id) || /fly/.test(exercise.clipName);
  const checks: ReferenceCheckSpec[] = [
    {
      kind: 'phaseOrder',
      id: 'supine_phase_order',
      label: 'Supine movement follows lower/open, bottom, return, top',
      order: ['eccentric', 'bottom', 'concentric', 'top'],
    },
    {
      kind: 'landmarkStationary',
      id: 'supine_pelvis_still',
      label: 'Hips stay on the bench',
      bone: 'pelvis',
      normalizeBy: 'standingHeight',
      tolerance: 0.012,
    },
    {
      kind: 'landmarkStationary',
      id: 'supine_left_foot_still',
      label: 'Left foot stays planted',
      bone: 'foot_l',
      normalizeBy: 'standingHeight',
      tolerance: 0.012,
    },
    {
      kind: 'landmarkStationary',
      id: 'supine_right_foot_still',
      label: 'Right foot stays planted',
      bone: 'foot_r',
      normalizeBy: 'standingHeight',
      tolerance: 0.012,
    },
    {
      kind: 'landmarkDistanceEnvelope',
      id: 'supine_dumbbells_level',
      label: 'Hands stay level with one another',
      from: 'hand_l',
      to: 'hand_r',
      axis: 'y',
      envelope: { min: 0, max: 0.04 },
    },
    {
      kind: 'bilateralSymmetry',
      id: 'supine_elbow_symmetry',
      label: 'Both elbows remain matched',
      left: 'forearm_l',
      right: 'forearm_r',
      axis: 'x',
      toleranceDeg: 1.5,
    },
  ];

  if (fly) {
    checks.push(
      {
        kind: 'jointEnvelope',
        id: 'fly_soft_elbow',
        label: 'Fly keeps a soft fixed elbow',
        bone: 'forearm_l',
        axis: 'x',
        envelope: { min: 10, max: 30 },
      },
      {
        kind: 'segmentAngleEnvelope',
        id: 'fly_bottom_depth',
        label: 'Upper arm opens to around chest level',
        bone: 'upperarm_l',
        worldAxis: 'y',
        phases: ['bottom'],
        envelope: { min: 78, max: 100 },
      },
      {
        kind: 'jointEnvelope',
        id: 'fly_neutral_grip',
        label: 'Fly keeps the palms-facing forearm turn',
        bone: 'forearm_l',
        axis: 'y',
        envelope: { min: 60, max: 90 },
      },
    );
  } else {
    checks.push(
      {
        kind: 'jointEnvelope',
        id: 'bench_top_elbow',
        label: 'Bench press finishes near elbow extension',
        bone: 'forearm_l',
        axis: 'x',
        phases: ['top'],
        envelope: { min: 5, max: 25 },
      },
      {
        kind: 'jointEnvelope',
        id: 'bench_bottom_elbow',
        label: 'Bench press reaches a deep bottom elbow angle',
        bone: 'forearm_l',
        axis: 'x',
        phases: ['bottom'],
        envelope: { min: 85, max: 120 },
      },
      {
        kind: 'jointExcursion',
        id: 'bench_elbow_rom',
        label: 'Bench press uses a substantial elbow range',
        bone: 'forearm_l',
        axis: 'x',
        envelope: { min: 70, max: 115 },
      },
    );
  }

  return {
    schemaVersion: 1,
    id: fly ? 'supine.dumbbell_fly.v1' : 'supine.dumbbell_bench_press.v1',
    referenceVersion: 1,
    family: 'supine',
    status: 'draft',
    applicability: { handOrientation: exercise.hands.orientation, support: 'bench' },
    provenance:
      'HOME GYM PT internal flat-bench supine reference draft. Independent review required before certification.',
    reviewViews: [
      { id: 'side', label: 'Side', preset: 'right', target: 'full_body' },
      { id: 'front', label: 'From the feet', preset: 'front', target: 'full_body' },
      { id: 'three_quarter', label: 'Three-quarter', preset: 'three_quarter', target: 'upper_body' },
      { id: 'hands', label: 'Hands and dumbbells', preset: 'focus', target: 'hands' },
    ],
    checks,
  };
}
