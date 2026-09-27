import type { BoneName } from '../rig/boneNames';
import type { Vec3 } from '../rig/types';
import { AXES, vec3 } from '../rig/types';
import { clamp, toRad } from '../core/math';
import { HgQuat, HgVec3 } from '../core/linearMath';
import type { HgPoseEvaluation, HgRigBone, HgSkeleton } from '../rig/firstPartySkeleton';

const BONE_AXIS = new HgVec3(0, 1, 0);
const FLEXION_AXIS = new HgVec3(1, 0, 0);

const scratch = {
  rest: new HgQuat(),
  current: new HgVec3(),
  inverseRest: new HgQuat(),
};

export function hgClampRotation(bone: HgRigBone, rotation: Vec3): Vec3 {
  const out = vec3();
  for (const axis of AXES) {
    const limit = bone.definition.limits[axis];
    out[axis] = limit
      ? clamp(rotation[axis], toRad(limit.min), toRad(limit.max))
      : 0;
  }
  return out;
}

/** World orientation a bone would have if its own authored rotation were zero. */
export function hgRestWorldQuaternion(
  skeleton: HgSkeleton,
  evaluation: HgPoseEvaluation,
  name: BoneName,
  target = new HgQuat(),
): HgQuat {
  const bone = skeleton.bone(name);
  if (!bone.parent) return target.copy(bone.restLocalQuaternion);
  return target
    .copy(evaluation.quaternion(bone.parent))
    .multiply(bone.restLocalQuaternion);
}

/**
 * Project-owned XZY swing solve. Mirrors the current analytic implementation:
 * d = (-sin z, cos x cos z, sin x cos z).
 */
export function hgSwingFor(
  skeleton: HgSkeleton,
  evaluation: HgPoseEvaluation,
  name: BoneName,
  direction: HgVec3,
  twist = 0,
): Vec3 {
  hgRestWorldQuaternion(skeleton, evaluation, name, scratch.rest);
  scratch.current
    .copy(direction)
    .normalize()
    .applyQuaternion(scratch.inverseRest.copy(scratch.rest).invert());

  const abduction = Math.asin(Math.max(-1, Math.min(1, -scratch.current.x)));
  const flexion = Math.atan2(scratch.current.z, scratch.current.y);
  return { x: flexion, y: twist, z: abduction };
}

export function hgLocalRotationForDirection(
  skeleton: HgSkeleton,
  evaluation: HgPoseEvaluation,
  name: BoneName,
  direction: HgVec3,
  twist = 0,
): Vec3 {
  return hgClampRotation(
    skeleton.bone(name),
    hgSwingFor(skeleton, evaluation, name, direction, twist),
  );
}

/** Project-owned one-axis hinge solve for elbows/knees. */
export function hgHingeRotationForDirection(
  skeleton: HgSkeleton,
  evaluation: HgPoseEvaluation,
  name: BoneName,
  direction: HgVec3,
): Vec3 {
  const bone = skeleton.bone(name);
  hgRestWorldQuaternion(skeleton, evaluation, name, scratch.rest);

  const restDirection = BONE_AXIS.clone().applyQuaternion(scratch.rest);
  const flexionAxis = FLEXION_AXIS.clone().applyQuaternion(scratch.rest);
  const unitDirection = direction.clone().normalize();

  const projected = unitDirection
    .clone()
    .addScaledVector(flexionAxis, -unitDirection.dot(flexionAxis));

  if (projected.lengthSq() < 1e-10) {
    return hgClampRotation(bone, { x: 0, y: 0, z: 0 });
  }
  projected.normalize();

  const angle = Math.atan2(
    restDirection.clone().cross(projected).dot(flexionAxis),
    restDirection.dot(projected),
  );
  return hgClampRotation(bone, { x: angle, y: 0, z: 0 });
}
