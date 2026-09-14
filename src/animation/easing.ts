import type { EasingKind } from '../exercises/types';
import { clamp } from '../core/math';

/**
 * Easing curves for resistance training.
 *
 * Constant-speed interpolation looks robotic and, worse, is wrong: a lift
 * decelerates into the contracted position and accelerates out of the stretched
 * one. `lift` is the default for that reason — it has zero velocity at both
 * ends, so phases join without a visible kick and a loop closes cleanly.
 */
export const EASINGS: Record<EasingKind, (t: number) => number> = {
  linear: (t) => t,
  easeIn: (t) => t * t,
  easeOut: (t) => 1 - (1 - t) * (1 - t),
  easeInOut: (t) => (t < 0.5 ? 2 * t * t : 1 - 2 * (1 - t) * (1 - t)),
  lift: (t) => (1 - Math.cos(Math.PI * t)) / 2,
  // Fifth-order minimum-jerk trajectory. Unlike the cosine lift curve, both
  // velocity and acceleration are zero at each end. That matters when a
  // secondary joint starts part-way through a phase: it eases out of a held
  // position without a visible acceleration step.
  minimumJerk: (t) => t * t * t * (10 + t * (-15 + 6 * t)),
  grind: (t) => {
    // Slow through the mid-range sticking point, smooth at both ends.
    const shaped = t + (0.5 * Math.sin(2 * Math.PI * t)) / (2 * Math.PI);
    return (1 - Math.cos(Math.PI * shaped)) / 2;
  },
  hold: () => 0,
};

export function ease(kind: EasingKind, t: number): number {
  return EASINGS[kind](clamp(t, 0, 1));
}

export const EASING_LABELS: Record<EasingKind, string> = {
  linear: 'Linear',
  easeIn: 'Ease in',
  easeOut: 'Ease out',
  easeInOut: 'Ease in-out',
  lift: 'Lift (smooth)',
  minimumJerk: 'Natural (minimum jerk)',
  grind: 'Grind (slow mid-range)',
  hold: 'Hold',
};