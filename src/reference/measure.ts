import { sampleClip, sortedKeyframes } from '../animation/clip';
import type { StudioClip } from '../animation/clip';
import { toDeg } from '../core/math';
import type { BoneName } from '../rig/boneNames';
import type { Axis } from '../rig/types';

export interface AxisMeasurement {
  min: number;
  max: number;
  excursion: number;
  samples: number;
}

export interface PhaseTimingMeasurement {
  id: string;
  start: number;
  end: number;
  duration: number;
  fraction: number;
}

function sampled(clip: StudioClip, count: number) {
  const samples = Math.max(8, count);
  return Array.from({ length: samples }, (_, index) => {
    const time = (index / samples) * clip.duration;
    const frame = sampleClip(clip, time);
    return { time, phaseId: frame.phaseId, pose: frame.pose };
  });
}

/**
 * Diagnostic-only measurement of one generated joint axis.
 *
 * This is useful while authoring independent reference envelopes, but its output
 * must not automatically become the envelope. Current exercise behaviour is
 * evidence, not the reference truth.
 */
export function measureJointAxis(
  clip: StudioClip,
  bone: BoneName,
  axis: Axis,
  options: { phases?: string[]; samples?: number } = {},
): AxisMeasurement {
  const rows = sampled(clip, options.samples ?? 101).filter(
    (row) => !options.phases || (row.phaseId !== undefined && options.phases.includes(row.phaseId)),
  );
  if (rows.length === 0) return { min: 0, max: 0, excursion: 0, samples: 0 };
  const values = rows.map((row) => toDeg(row.pose.rotations[bone]?.[axis] ?? 0));
  const min = Math.min(...values);
  const max = Math.max(...values);
  return { min, max, excursion: max - min, samples: values.length };
}

export function measureRootAxis(
  clip: StudioClip,
  axis: Axis,
  options: { phases?: string[]; samples?: number } = {},
): AxisMeasurement {
  const rows = sampled(clip, options.samples ?? 101).filter(
    (row) => !options.phases || (row.phaseId !== undefined && options.phases.includes(row.phaseId)),
  );
  if (rows.length === 0) return { min: 0, max: 0, excursion: 0, samples: 0 };
  const values = rows.map((row) => toDeg(row.pose.rootRotation[axis]));
  const min = Math.min(...values);
  const max = Math.max(...values);
  return { min, max, excursion: max - min, samples: values.length };
}

/**
 * Semantic phase timing taken from the clip itself. Adjacent keyframes define
 * each phase's span.
 */
export function measurePhaseTiming(clip: StudioClip): PhaseTimingMeasurement[] {
  const keyframes = sortedKeyframes(clip);
  const result: PhaseTimingMeasurement[] = [];
  for (let index = 0; index < keyframes.length - 1; index += 1) {
    const from = keyframes[index];
    const to = keyframes[index + 1];
    if (!from.phaseId) continue;
    const duration = to.time - from.time;
    result.push({
      id: from.phaseId,
      start: from.time,
      end: to.time,
      duration,
      fraction: clip.duration <= 0 ? 0 : duration / clip.duration,
    });
  }
  return result;
}

/** Worst left/right mirrored rotation error, degrees. */
export function measureBilateralRotationError(
  clip: StudioClip,
  left: BoneName,
  right: BoneName,
  axis: Axis,
  options: { phases?: string[]; samples?: number } = {},
): { worst: number; time: number } {
  const rows = sampled(clip, options.samples ?? 101).filter(
    (row) => !options.phases || (row.phaseId !== undefined && options.phases.includes(row.phaseId)),
  );
  let worst = 0;
  let time = 0;
  for (const row of rows) {
    const l = toDeg(row.pose.rotations[left]?.[axis] ?? 0);
    const r = toDeg(row.pose.rotations[right]?.[axis] ?? 0);
    const expected = axis === 'x' ? l : -l;
    const error = Math.abs(r - expected);
    if (error > worst) {
      worst = error;
      time = row.time;
    }
  }
  return { worst, time };
}
