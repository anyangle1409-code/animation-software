import type { StudioClip } from '../animation/clip';
import type { BoneName } from '../rig/boneNames';
import type { Skeleton } from '../rig/skeleton';
import { bodyNormalization, normalizePoint } from './normalize';
import { sampleLandmarks } from './landmarks';

export type NormalizationScale = 'standingHeight' | 'shoulderWidth' | 'armLength' | 'torsoLength';

export interface NormalizedTrajectoryPoint {
  t: number;
  x: number;
  y: number;
  z: number;
}

export interface TrajectoryComparison {
  rms: number;
  max: number;
  maxAt: number;
  samples: number;
}

/**
 * Sample one landmark relative to another body landmark and normalize it by a
 * stable body scale. This is the basic unit for character-independent motion
 * references: e.g. elbow relative to shoulder in shoulder-width units.
 */
export function sampleNormalizedRelativeTrajectory(
  rig: Skeleton,
  clip: StudioClip,
  bone: BoneName,
  originBone: BoneName,
  scale: NormalizationScale,
  samples = 41,
): NormalizedTrajectoryPoint[] {
  const count = Math.max(2, samples);
  const scaleValue = bodyNormalization(rig)[scale];

  return Array.from({ length: count }, (_, index) => {
    const t = index / (count - 1);
    // Do not sample the exact loop end through modulo wrapping: use the final
    // authored instant just inside the duration, which is the returned pose.
    const time = index === count - 1
      ? Math.max(0, clip.duration - 1e-9)
      : t * clip.duration;
    const landmarks = sampleLandmarks(rig, clip, time, [bone, originBone]);
    const normalized = normalizePoint(landmarks[bone]!, landmarks[originBone]!, scaleValue);
    return { t, ...normalized };
  });
}

/** Compare two equally sampled normalized trajectories. */
export function compareNormalizedTrajectories(
  candidate: NormalizedTrajectoryPoint[],
  reference: NormalizedTrajectoryPoint[],
): TrajectoryComparison {
  if (candidate.length !== reference.length) {
    throw new Error(`Trajectory sample count differs: candidate ${candidate.length}, reference ${reference.length}`);
  }
  if (candidate.length === 0) return { rms: 0, max: 0, maxAt: 0, samples: 0 };

  let sumSq = 0;
  let max = 0;
  let maxAt = 0;

  for (let index = 0; index < candidate.length; index += 1) {
    const a = candidate[index];
    const b = reference[index];
    if (Math.abs(a.t - b.t) > 1e-6) {
      throw new Error(`Trajectory sample time differs at index ${index}: ${a.t} vs ${b.t}`);
    }
    const distance = Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
    sumSq += distance * distance;
    if (distance > max) {
      max = distance;
      maxAt = a.t;
    }
  }

  return {
    rms: Math.sqrt(sumSq / candidate.length),
    max,
    maxAt,
    samples: candidate.length,
  };
}
