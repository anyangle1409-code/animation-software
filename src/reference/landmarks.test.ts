import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { sampleLandmarks, sampleLandmarkTrajectory } from './landmarks';

describe('reference landmark sampling', () => {
  const clip = generateClip(canonicalSkeleton, bicepCurl);

  it('resolves paired hand landmarks from the actual solved frame', () => {
    const frame = sampleLandmarks(canonicalSkeleton, clip, 0, ['hand_l', 'hand_r']);
    expect(frame.hand_l).toBeDefined();
    expect(frame.hand_r).toBeDefined();
    expect(frame.hand_l!.x).toBeLessThan(0);
    expect(frame.hand_r!.x).toBeGreaterThan(0);
  });

  it('returns a tempo-independent normalized landmark trajectory', () => {
    const trajectory = sampleLandmarkTrajectory(canonicalSkeleton, clip, 'hand_l', 21);
    expect(trajectory).toHaveLength(21);
    expect(trajectory[0].t).toBe(0);
    expect(trajectory.at(-1)!.t).toBe(1);
    const ys = trajectory.map((entry) => entry.point.y);
    expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(0.2);
  });
});
