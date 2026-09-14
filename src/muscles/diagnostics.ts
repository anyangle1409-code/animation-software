import type { MuscleInvolvement } from '../exercises/types';
import type { PoseEvaluation } from '../rig/skeleton';
import type { Side } from '../rig/boneNames';
import { activationMap, activationOf } from './activation';
import type { ActivationLevel } from './activation';
import { MUSCLE_GROUP_IDS, MUSCLE_GROUPS } from './groups';
import type { MuscleGroupId } from './groups';
import { MUSCLES, createMuscleTransform, resolveMuscle } from './model';

export type MuscleLengthState = 'shortened' | 'neutral' | 'lengthened';

export interface MuscleReading {
  side: Side | null;
  /** Functional path length divided by the rest-pose path length. */
  stretch: number;
  /** Percentage difference from rest length. Negative means shorter. */
  deltaPercent: number;
  state: MuscleLengthState;
  /** Origin + optional anatomical via points + insertion. */
  pathPoints: number;
}

export interface MuscleGroupDiagnostic {
  id: MuscleGroupId;
  label: string;
  region: (typeof MUSCLE_GROUPS)[MuscleGroupId]['region'];
  activation: ActivationLevel;
  readings: MuscleReading[];
}

/**
 * A small dead-band stops tiny numerical/postural changes being presented as a
 * meaningful contraction. This describes geometric length relative to the rest
 * pose; it deliberately does not claim to measure force or EMG activity.
 */
export function muscleLengthState(stretch: number): MuscleLengthState {
  if (stretch < 0.985) return 'shortened';
  if (stretch > 1.015) return 'lengthened';
  return 'neutral';
}

/**
 * Resolve every trainer-level muscle group for one finished canonical pose.
 * Activation comes from the exercise definition; length state comes from the
 * actual joint-spanning functional path. Keeping those two concepts separate is
 * important: a stabiliser can be highly active while remaining near-isometric.
 */
export function diagnoseMuscles(
  evaluation: PoseEvaluation,
  involvement: MuscleInvolvement,
): MuscleGroupDiagnostic[] {
  const activation = activationMap(involvement);
  const transform = createMuscleTransform();

  return MUSCLE_GROUP_IDS.map((id) => {
    const meta = MUSCLE_GROUPS[id];
    const readings = MUSCLES.filter((muscle) => muscle.group === id)
      .map((muscle): MuscleReading => {
        resolveMuscle(evaluation, muscle, transform);
        const stretch = transform.stretch;
        return {
          side: muscle.side,
          stretch,
          deltaPercent: (stretch - 1) * 100,
          state: muscleLengthState(stretch),
          pathPoints: muscle.path.length,
        };
      })
      .sort((a, b) => {
        if (a.side === b.side) return 0;
        if (a.side === 'l') return -1;
        if (b.side === 'l') return 1;
        if (a.side === 'r') return -1;
        return 1;
      });

    return {
      id,
      label: meta.label,
      region: meta.region,
      activation: activationOf(activation, id),
      readings,
    };
  });
}

export const MUSCLE_ACTIVATION_ORDER: Record<ActivationLevel, number> = {
  primary: 0,
  secondary: 1,
  stabiliser: 2,
  inactive: 3,
};
