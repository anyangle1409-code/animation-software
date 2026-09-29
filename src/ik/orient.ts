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

interface QuaternionTarget {
  x: number;
  y: number;
  z: number;
  w: number;
  set(x: number, y: number, z: number, w: number): unknown;
}

/** World rest orientation on the project-owned FK/math path. */
export function restWorldQuaternion<T extends QuaternionTarget = HgQuat>(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  name: BoneName,
  target?: T,
): T {
  const result = hgRestWorldQuaternion(
    skeleton.firstParty,
    evaluation.firstPartyEvaluation,
    name,
    quaternionScratch,
  );
  const output = (target ?? new HgQuat()) as T;
  output.set(result.x, result.y, result.z, result.w);
  return output;
}

/** Analytic XZY swing on the project-owned FK/math path. */
export function swingFor(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  name: BoneName,
  direction: Vec3,
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
  direction: Vec3,
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
  direction: Vec3,
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
