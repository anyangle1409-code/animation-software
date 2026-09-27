import type { BoneName } from './boneNames';
import type { Pose, Vec3 } from './types';
import { vec3 } from './types';
import { lerpAngle } from '../core/math';
import { HgQuat, HgVec3 } from '../core/linearMath';

const ZERO: Vec3 = Object.freeze(vec3(0, 0, 0));

const blankPose = (): Pose => ({
  rotations: {},
  rootPosition: vec3(),
  rootRotation: vec3(),
});

/**
 * First-party equivalent of pose.ts blendPoses.
 *
 * Kept separate during migration so every existing animation can be parity
 * checked before the production implementation drops Three.js.
 */
export function hgBlendPoses(a: Pose, b: Pose, t: number, pivot?: Vec3): Pose {
  const out = blankPose();
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
      new HgVec3(pivot.x, pivot.y, pivot.z).applyQuaternion(
        new HgQuat().setFromEulerXZY(rotation.x, rotation.y, rotation.z),
      );

    const from = turned(a.rootRotation).add(
      new HgVec3(a.rootPosition.x, a.rootPosition.y, a.rootPosition.z),
    );
    const to = turned(b.rootRotation).add(
      new HgVec3(b.rootPosition.x, b.rootPosition.y, b.rootPosition.z),
    );
    const position = from.lerp(to, t).sub(turned(out.rootRotation));
    out.rootPosition = vec3(position.x, position.y, position.z);
  }

  return out;
}
