import type { Quaternion, Vector3 } from 'three';
import { HgQuat, HgVec3 } from '../core/linearMath';
import type { BoneName } from '../rig/boneNames';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose, Vec3 } from '../rig/types';
import {
  hgHingeRotationForDirection,
  hgLocalRotationForDirection,
  hgRestWorldQuaternion,
  hgSwingFor,
} from './firstPartyOrient';

const directionScratch = new HgVec3();
const quaternionScratch = new HgQuat();

/** World rest orientation; Three output remains for existing IK callers. */
export function restWorldQuaternion(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  name: BoneName,
  target: Quaternion = evaluation.quaternion(name).clone(),
): Quaternion {
  const result = hgRestWorldQuaternion(
    skeleton.firstParty,
    evaluation.firstPartyEvaluation,
    name,
    quaternionScratch,
  );
  return target.set(result.x, result.y, result.z, result.w);
}

/** Analytic XZY swing on the project-owned FK/math path. */
export function swingFor(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  name: BoneName,
  direction: Vector3,
  twist = 0,
): Vec3 {
  return hgSwingFor(
    skeleton.firstParty,
    evaluation.firstPartyEvaluation,
    name,
    directionScratch.set(direction.x, direction.y, direction.z),
    twist,
  );
}

/** Anatomically clamped local swing. */
export function localRotationForDirection(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  name: BoneName,
  direction: Vector3,
  twist = 0,
): Vec3 {
  return hgLocalRotationForDirection(
    skeleton.firstParty,
    evaluation.firstPartyEvaluation,
    name,
    directionScratch.set(direction.x, direction.y, direction.z),
    twist,
  );
}

/** One-axis elbow/knee hinge solve. */
export function hingeRotationForDirection(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  name: BoneName,
  direction: Vector3,
): Vec3 {
  return hgHingeRotationForDirection(
    skeleton.firstParty,
    evaluation.firstPartyEvaluation,
    name,
    directionScratch.set(direction.x, direction.y, direction.z),
  );
}

/** Write a bone rotation straight into a pose object (mutating). */
export function setRotation(pose: Pose, name: BoneName, rotation: Vec3): void {
  pose.rotations[name] = rotation;
}
