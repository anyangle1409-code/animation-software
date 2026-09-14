import { describe, expect, it } from 'vitest';
import type { StudioClip } from '../animation/clip';
import { restPose } from '../rig/pose';
import { vec3 } from '../rig/types';
import { measureJointCoordination } from './coordinationDiagnostics';

const delayedSupportClip = (): StudioClip => {
  const start = restPose();
  start.rotations.forearm_l = vec3(0, 0, 0);
  start.rotations.upperarm_l = vec3(0, 0, 0);
  const end = restPose();
  end.rotations.forearm_l = vec3(Math.PI / 2, 0, 0);
  end.rotations.upperarm_l = vec3((20 * Math.PI) / 180, 0, 0);
  return {
    id: 'coordination-diagnostic',
    name: 'coordination_diagnostic',
    exerciseId: 'diagnostic',
    duration: 1,
    fps: 30,
    loop: false,
    keyframes: [
      {
        id: 'start',
        time: 0,
        pose: start,
        ik: {},
        easing: 'linear',
        jointTiming: { upperarm_l: { delay: 0.5, finish: 1, easing: 'linear' } },
      },
      { id: 'end', time: 1, pose: end, ik: {}, easing: 'hold' },
    ],
    locks: [],
    equipment: [],
  };
};

describe('joint coordination diagnostics', () => {
  it('shows a delayed parent/support joint starting after the lead elbow', () => {
    const result = measureJointCoordination(delayedSupportClip(), 'forearm_l', 'upperarm_l', 0, 1);
    expect(result.lead.excursionDeg).toBeCloseTo(90, 6);
    expect(result.support.excursionDeg).toBeCloseTo(20, 6);
    expect(result.lead.onsetPercent).not.toBeNull();
    expect(result.support.onsetPercent).not.toBeNull();
    expect(result.onsetLagSeconds).not.toBeNull();
    expect(result.onsetLagSeconds!).toBeGreaterThan(0.45);
    expect(result.support.onsetPercent!).toBeGreaterThan(0.5);
  });

  it('reports near-isometric support without inventing an onset', () => {
    const clip = delayedSupportClip();
    clip.keyframes[1].pose.rotations.upperarm_l = vec3(0, 0, 0);
    const result = measureJointCoordination(clip, 'forearm_l', 'upperarm_l', 0, 1);
    expect(result.support.excursionDeg).toBeLessThan(0.25);
    expect(result.support.onsetTime).toBeNull();
    expect(result.onsetLagSeconds).toBeNull();
  });
});
