import { describe, expect, it } from 'vitest';
import { Euler, Quaternion, Vector3 } from 'three';
import { blendPoses, poseFromDegrees, restPose, ZERO } from './pose';
import type { BoneName } from './boneNames';
import type { Pose, Vec3 } from './types';
import { vec3 } from './types';
import { lerpAngle } from '../core/math';

const EPS = 2e-11;

function threeBlendPoses(a: Pose, b: Pose, t: number, pivot?: Vec3): Pose {
  const out = restPose();
  const names = new Set<BoneName>([
    ...(Object.keys(a.rotations) as BoneName[]),
    ...(Object.keys(b.rotations) as BoneName[]),
  ]);
  for (const name of names) {
    const from = a.rotations[name] ?? ZERO;
    const to = b.rotations[name] ?? ZERO;
    out.rotations[name] = vec3(
      lerpAngle(from.x, to.x, t),
      lerpAngle(from.y, to.y, t),
      lerpAngle(from.z, to.z, t),
    );
  }

  out.rootPosition = vec3(
    a.rootPosition.x + (b.rootPosition.x - a.rootPosition.x) * t,
    a.rootPosition.y + (b.rootPosition.y - a.rootPosition.y) * t,
    a.rootPosition.z + (b.rootPosition.z - a.rootPosition.z) * t,
  );
  out.rootRotation = vec3(
    lerpAngle(a.rootRotation.x, b.rootRotation.x, t),
    lerpAngle(a.rootRotation.y, b.rootRotation.y, t),
    lerpAngle(a.rootRotation.z, b.rootRotation.z, t),
  );

  if (pivot) {
    const turned = (rotation: Vec3) =>
      new Vector3(pivot.x, pivot.y, pivot.z).applyQuaternion(
        new Quaternion().setFromEuler(new Euler(rotation.x, rotation.y, rotation.z, 'XZY')),
      );
    const from = turned(a.rootRotation).add(
      new Vector3(a.rootPosition.x, a.rootPosition.y, a.rootPosition.z),
    );
    const to = turned(b.rootRotation).add(
      new Vector3(b.rootPosition.x, b.rootPosition.y, b.rootPosition.z),
    );
    const position = from.lerp(to, t).sub(turned(out.rootRotation));
    out.rootPosition = vec3(position.x, position.y, position.z);
  }

  return out;
}

function expectPoseClose(actual: Pose, expected: Pose) {
  const names = new Set([...Object.keys(actual.rotations), ...Object.keys(expected.rotations)]);
  for (const name of names) {
    const a = actual.rotations[name as BoneName] ?? ZERO;
    const b = expected.rotations[name as BoneName] ?? ZERO;
    expect(Math.abs(a.x - b.x), `${name}.x`).toBeLessThan(EPS);
    expect(Math.abs(a.y - b.y), `${name}.y`).toBeLessThan(EPS);
    expect(Math.abs(a.z - b.z), `${name}.z`).toBeLessThan(EPS);
  }

  for (const axis of ['x', 'y', 'z'] as const) {
    expect(
      Math.abs(actual.rootPosition[axis] - expected.rootPosition[axis]),
      `rootPosition.${axis}`,
    ).toBeLessThan(EPS);
    expect(
      Math.abs(actual.rootRotation[axis] - expected.rootRotation[axis]),
      `rootRotation.${axis}`,
    ).toBeLessThan(EPS);
  }
}

describe('production first-party pose blending parity against Three.js', () => {
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
      expectPoseClose(blendPoses(a, b, t), threeBlendPoses(a, b, t));
    }
  });

  it('matches Three pivot-aware root interpolation', () => {
    const pivots = [
      { x: 0, y: 0.95, z: 0 },
      { x: 0.15, y: 0.8, z: -0.1 },
    ];
    for (const pivot of pivots) {
      for (const t of [0, 0.13, 0.42, 0.75, 1]) {
        expectPoseClose(
          blendPoses(a, b, t, pivot),
          threeBlendPoses(a, b, t, pivot),
        );
      }
    }
  });
});
