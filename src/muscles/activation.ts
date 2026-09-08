import type { MuscleInvolvement } from '../exercises/types';
import type { MuscleGroupId } from './groups';

export type ActivationLevel = 'primary' | 'secondary' | 'stabiliser' | 'inactive';

export interface ActivationStyle {
  colour: string;
  emissive: number;
  opacity: number;
  label: string;
}

/**
 * How strongly each group is shown. The levels come straight from the exercise
 * definition — nothing here inspects the animation and guesses, which is what
 * keeps the studio's overlay and Home Gym PT's exercise database in agreement.
 */
export const ACTIVATION_STYLES: Record<ActivationLevel, ActivationStyle> = {
  primary: { colour: '#e8402f', emissive: 0.55, opacity: 0.97, label: 'Primary' },
  secondary: { colour: '#f0873a', emissive: 0.3, opacity: 0.92, label: 'Secondary' },
  stabiliser: { colour: '#e0c65a', emissive: 0.12, opacity: 0.82, label: 'Stabiliser' },
  inactive: { colour: '#8d6f74', emissive: 0, opacity: 0.55, label: 'Not targeted' },
};

export function activationMap(
  involvement: MuscleInvolvement,
): Map<MuscleGroupId, ActivationLevel> {
  const map = new Map<MuscleGroupId, ActivationLevel>();
  for (const group of involvement.stabilisers) map.set(group, 'stabiliser');
  for (const group of involvement.secondary) map.set(group, 'secondary');
  // Primary wins if a group is listed more than once.
  for (const group of involvement.primary) map.set(group, 'primary');
  return map;
}

export const activationOf = (
  map: Map<MuscleGroupId, ActivationLevel>,
  group: MuscleGroupId,
): ActivationLevel => map.get(group) ?? 'inactive';
