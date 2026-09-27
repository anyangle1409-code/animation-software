import { describe, expect, it } from 'vitest';
import { blendPoses, poseFromDegrees } from './pose';
import { hgBlendPoses } from './firstPartyPose';

const EPS = 2e-11;

function expectPoseClose(
  actual: ReturnType<typeof hgBlendPoses>,
  expected: ReturnType<typeof blendPoses>,
) {
  const names = new Set([...Object.keys(actual.rotations), ...Object.keys(expected.rotations)]);
  for (const name of names) {
    const a = actual.rotations[name as keyof typeof actual.rotations] ?? { x: 0, y: 0, z: 0 };
    const b = expected.rotations[name as keyof typeof expected.rotations] ?? { x: 0, y: 0, z: 0 };
    expect(Math.abs(a.x - b.x), `${name}.x`).toBeLessThan(EPS);
    expect(Math.abs(a.y - b.y), `${name}.y`).toBeLessThan(EPS);
    expect(Math.abs(a.z - b.z), `${name}.z`).toBeLessThan(EPS);
  }

  for (const axis of ['x', 'y', 'z'] as const) {
    expect(Math.abs(actual.rootPosition[axis] - expected.rootPosition[axis]), `rootPosition.${axis}`).toBeLessThan(EPS);
    expect(Math.abs(actual.rootRotation[axis] - expected.rootRotation[axis]), `rootRotation.${axis}`).toBeLessThan(EPS);
  }
}

describe('first-party pose blending parity', () => {
  const a = poseFromDegrees(
    {
      spine_01: { x: -8, y: 4, z: 2 },
      upperarm_l: { x: 20, y: -15, z: 12 },
    },
    {
      position: { x: 0.1, y: 0.2, z: -0.3 },
      rotation: { x: 12, y: -8, z: 5 },
    },
  );

  const b = poseFromDegrees(
    {
      spine_01: { x: 24, y: -9, z: -4 },
      upperarm_l: { x: 95, y: 20, z: -35 },
      forearm_l: { x: 112 },
    },
    {
      position: { x: -0.25, y: 0.6, z: 0.4 },
      rotation: { x: -18, y: 16, z: -11 },
    },
  );

  it('matches ordinary root/angle interpolation', () => {
    for (const t of [0, 0.1, 0.37, 0.5, 0.83, 1]) {
      expectPoseClose(hgBlendPoses(a, b, t), blendPoses(a, b, t));
    }
  });

  it('matches pivot-aware root interpolation', () => {
    const pivots = [
      { x: 0, y: 0.95, z: 0 },
      { x: 0.15, y: 0.8, z: -0.1 },
    ];
    for (const pivot of pivots) {
      for (const t of [0, 0.13, 0.42, 0.75, 1]) {
        expectPoseClose(
          hgBlendPoses(a, b, t, pivot),
          blendPoses(a, b, t, pivot),
        );
      }
    }
  });
});
