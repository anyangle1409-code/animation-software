import { Euler, Quaternion, Vector3 } from 'three';
import type { BoneName } from '../rig/boneNames';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose, Vec3 } from '../rig/types';
import { EULER_ORDER } from '../rig/types';
import { clampRotation } from '../rig/pose';

const BONE_AXIS = new Vector3(0, 1, 0);
const FLEXION_AXIS = new Vector3(1, 0, 0);

const scratch = {
  rest: new Quaternion(),
  swing: new Quaternion(),
  delta: new Quaternion(),
  twist: new Quaternion(),
  current: new Vector3(),
  inverseRest: new Quaternion(),
  euler: new Euler(0, 0, 0, EULER_ORDER),
};

/** The world orientation a bone would have if its own rotation were zero. */
export function restWorldQuaternion(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  name: BoneName,
  target = new Quaternion(),
): Quaternion {
  const bone = skeleton.bone(name);
  if (!bone.parent) return target.copy(bone.restLocalQuaternion);
  return target.copy(evaluation.quaternion(bone.parent)).multiply(bone.restLocalQuaternion);
}

/**
 * Unclamped local rotation that points a bone's +Y along `direction`, with an
 * explicit twist about the bone's own axis.
 *
 * Solved directly from the Euler order rather than by converting a quaternion:
 * a quaternion conversion is free to put the rotation anywhere the axes allow,
 * including large amounts of twist the joint does not have, which the limits
 * then clamp away. Here the swing lands entirely in flexion and abduction, and
 * the twist is exactly what the caller asked for.
 *
 * With order XZY, applying the rotation to the bone axis gives
 *   d = (-sin z, cos x · cos z, sin x · cos z)
 * which inverts to the two lines below.
 */
export function swingFor(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  name: BoneName,
  direction: Vector3,
  twist = 0,
): Vec3 {
  void skeleton;
  restWorldQuaternion(skeleton, evaluation, name, scratch.rest);
  scratch.current
    .copy(direction)
    .normalize()
    .applyQuaternion(scratch.inverseRest.copy(scratch.rest).invert());

  const abduction = Math.asin(Math.max(-1, Math.min(1, -scratch.current.x)));
  const flexion = Math.atan2(scratch.current.z, scratch.current.y);
  return { x: flexion, y: twist, z: abduction };
}

/**
 * Local rotation that points a bone's +Y along `direction`, clamped to the
 * joint's anatomical limits.
 *
 * Clamping here is what stops an IK solve driving a joint somewhere a body
 * could not go — it simply falls short, which the solver reports as an
 * unreached target.
 */
export function localRotationForDirection(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  name: BoneName,
  direction: Vector3,
  twist = 0,
): Vec3 {
  return clampRotation(
    skeleton.bone(name),
    swingFor(skeleton, evaluation, name, direction, twist),
  );
}

/**
 * Local rotation for a *hinge* joint — an elbow or a knee — that points the
 * bone as close to `direction` as one axis allows.
 *
 * A hinge must be solved directly rather than by decomposing a swing into Euler
 * angles: the decomposition spills rotation into the joint's twist axis, the
 * anatomical limit clamps it away, and the chain silently comes apart. Solving
 * for the flexion angle itself keeps the joint a hinge by construction.
 */
export function hingeRotationForDirection(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  name: BoneName,
  direction: Vector3,
): Vec3 {
  const bone = skeleton.bone(name);
  restWorldQuaternion(skeleton, evaluation, name, scratch.rest);
  const restDirection = BONE_AXIS.clone().applyQuaternion(scratch.rest);
  const flexionAxis = FLEXION_AXIS.clone().applyQuaternion(scratch.rest);

  const projected = direction
    .clone()
    .normalize()
    .addScaledVector(flexionAxis, -direction.dot(flexionAxis) / direction.length());
  if (projected.lengthSq() < 1e-10) return clampRotation(bone, { x: 0, y: 0, z: 0 });
  projected.normalize();

  const angle = Math.atan2(
    restDirection.clone().cross(projected).dot(flexionAxis),
    restDirection.dot(projected),
  );
  return clampRotation(bone, { x: angle, y: 0, z: 0 });
}

/** Write a bone rotation straight into a pose object (mutating). */
export function setRotation(pose: Pose, name: BoneName, rotation: Vec3): void {
  pose.rotations[name] = rotation;
}
