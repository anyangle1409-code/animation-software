import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import type { ExerciseDefinition } from '../exercises/types';
import { canonicalSkeleton } from '../rig/skeleton';
import { compareNormalizedTrajectories, sampleNormalizedRelativeTrajectory } from './trajectory';

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

describe('normalized landmark trajectories', () => {
  it('is exactly stable against itself', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const trajectory = sampleNormalizedRelativeTrajectory(
      canonicalSkeleton,
      clip,
      'hand_l',
      'upperarm_l',
      'armLength',
      31,
    );
    const comparison = compareNormalizedTrajectories(trajectory, trajectory);
    expect(comparison.rms).toBe(0);
    expect(comparison.max).toBe(0);
    expect(comparison.samples).toBe(31);
  });

  it('detects a changed arm path after body-size normalization', () => {
    const altered: ExerciseDefinition = clone(bicepCurl);
    altered.peakPose.joints.upperarm_l = {
      ...(altered.peakPose.joints.upperarm_l ?? {}),
      x: 30,
    };
    altered.peakPose.joints.upperarm_r = {
      ...(altered.peakPose.joints.upperarm_r ?? {}),
      x: 30,
    };

    const reference = sampleNormalizedRelativeTrajectory(
      canonicalSkeleton,
      generateClip(canonicalSkeleton, bicepCurl),
      'hand_l',
      'upperarm_l',
      'armLength',
      31,
    );
    const candidate = sampleNormalizedRelativeTrajectory(
      canonicalSkeleton,
      generateClip(canonicalSkeleton, altered),
      'hand_l',
      'upperarm_l',
      'armLength',
      31,
    );

    const comparison = compareNormalizedTrajectories(candidate, reference);
    expect(comparison.max).toBeGreaterThan(0.02);
    expect(comparison.rms).toBeGreaterThan(0);
    expect(comparison.maxAt).toBeGreaterThan(0);
  });

  it('refuses trajectories sampled on different time grids', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const a = sampleNormalizedRelativeTrajectory(canonicalSkeleton, clip, 'hand_l', 'upperarm_l', 'armLength', 11);
    const b = sampleNormalizedRelativeTrajectory(canonicalSkeleton, clip, 'hand_l', 'upperarm_l', 'armLength', 12);
    expect(() => compareNormalizedTrajectories(a, b)).toThrow(/sample count differs/);
  });
});
