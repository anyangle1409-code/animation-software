import { Euler, Quaternion, Vector3 } from 'three';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose } from '../rig/types';
import { EULER_ORDER } from '../rig/types';
import { clamp } from '../core/math';
import {
  hingeRotationForDirection,
  localRotationForDirection,
  restWorldQuaternion,
  setRotation,
  swingFor,
} from './orient';
import type { IKChain, IKResult } from './types';

const EPSILON = 1e-6;
const X_AXIS = new Vector3(1, 0, 0);
const Y_AXIS = new Vector3(0, 1, 0);
const Z_AXIS = new Vector3(0, 0, 1);

const tmp = {
  rootHead: new Vector3(),
  midHead: new Vector3(),
  effector: new Vector3(),
  toTarget: new Vector3(),
  direction: new Vector3(),
  poleVector: new Vector3(),
  poleOrtho: new Vector3(),
  upperDirection: new Vector3(),
  lowerDirection: new Vector3(),
  clampedTarget: new Vector3(),
  restQuaternion: new Quaternion(),
  swing: new Quaternion(),
  world: new Quaternion(),
  euler: new Euler(0, 0, 0, EULER_ORDER),
};

/**
 * Analytic two-bone IK.
 *
 * The triangle formed by the two bone lengths and the root-to-target distance
 * fixes the bend angle; the pole target fixes which way the hinge points. The
 * upper bone is then twisted about its own axis so that the hinge's flexion
 * plane contains the target — without that step the elbow or knee would need
 * an abduction it does not anatomically have, and clamping it away would break
 * the chain.
 *
 * `pose` is mutated in place; the caller owns cloning.
 */
export function solveTwoBone(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  pose: Pose,
  chain: IKChain,
  target: Vector3,
  pole: Vector3,
): IKResult {
  const upperBone = skeleton.bone(chain.root);
  const midBone = skeleton.bone(chain.mid);
  const upperLength = upperBone.length;
  const lowerLength = midBone.length;

  evaluation.apply(pose);
  evaluation.head(chain.root, tmp.rootHead);
  evaluation.head(chain.mid, tmp.midHead);

  tmp.toTarget.subVectors(target, tmp.rootHead);
  const rawDistance = tmp.toTarget.length();
  const overExtended = rawDistance > upperLength + lowerLength;

  if (rawDistance < EPSILON) {
    return { chain: chain.id, error: rawDistance, reached: false, overExtended: false };
  }
  tmp.direction.copy(tmp.toTarget).divideScalar(rawDistance);

  // Keep the triangle solvable: never fully locked out, never folded through itself.
  const minReach = Math.abs(upperLength - lowerLength) + 1e-4;
  const maxReach = (upperLength + lowerLength) * 0.9995;
  const distance = clamp(rawDistance, minReach, maxReach);
  tmp.clampedTarget.copy(tmp.rootHead).addScaledVector(tmp.direction, distance);

  // Pole direction, orthogonalised against the root-to-target line.
  tmp.poleVector.subVectors(pole, tmp.rootHead);
  tmp.poleOrtho
    .copy(tmp.poleVector)
    .addScaledVector(tmp.direction, -tmp.poleVector.dot(tmp.direction));
  if (tmp.poleOrtho.lengthSq() < 1e-8) {
    // Degenerate pole (on the line): fall back to the limb's current bend plane.
    tmp.poleOrtho
      .subVectors(tmp.midHead, tmp.rootHead)
      .addScaledVector(tmp.direction, -tmp.poleVector.dot(tmp.direction));
    if (tmp.poleOrtho.lengthSq() < 1e-8) {
      tmp.poleOrtho.copy(Z_AXIS).addScaledVector(tmp.direction, -tmp.direction.z);
    }
  }
  tmp.poleOrtho.normalize();

  // Angle between the upper bone and the root-to-target line (law of cosines).
  const cosShoulder =
    (upperLength * upperLength + distance * distance - lowerLength * lowerLength) /
    (2 * upperLength * distance);
  const shoulderAngle = Math.acos(clamp(cosShoulder, -1, 1));

  tmp.upperDirection
    .copy(tmp.direction)
    .multiplyScalar(Math.cos(shoulderAngle))
    .addScaledVector(tmp.poleOrtho, Math.sin(shoulderAngle))
    .normalize();

  const midPositionX = tmp.rootHead.x + tmp.upperDirection.x * upperLength;
  const midPositionY = tmp.rootHead.y + tmp.upperDirection.y * upperLength;
  const midPositionZ = tmp.rootHead.z + tmp.upperDirection.z * upperLength;
  tmp.lowerDirection
    .set(
      tmp.clampedTarget.x - midPositionX,
      tmp.clampedTarget.y - midPositionY,
      tmp.clampedTarget.z - midPositionZ,
    )
    .normalize();

  // Twist the upper bone so the hinge's flexion plane contains the lower bone.
  const twist = hingeTwist(skeleton, evaluation, chain, tmp.upperDirection, tmp.lowerDirection);

  setRotation(
    pose,
    chain.root,
    localRotationForDirection(skeleton, evaluation, chain.root, tmp.upperDirection, twist),
  );
  evaluation.apply(pose);

  // Re-aim the lower bone from where the upper bone actually ended up, which
  // may differ from the ideal if a joint limit clamped the solve.
  evaluation.head(chain.mid, tmp.midHead);
  tmp.lowerDirection.subVectors(target, tmp.midHead);
  if (tmp.lowerDirection.lengthSq() < EPSILON) tmp.lowerDirection.copy(tmp.upperDirection);
  tmp.lowerDirection.normalize();

  setRotation(
    pose,
    chain.mid,
    hingeRotationForDirection(skeleton, evaluation, chain.mid, tmp.lowerDirection),
  );
  evaluation.apply(pose);

  evaluation.head(chain.end, tmp.effector);
  const error = tmp.effector.distanceTo(target);
  return { chain: chain.id, error, reached: error < 2e-3, overExtended };
}

/**
 * How far the upper bone must twist about its own axis for the hinge bone's
 * flexion plane to contain `lowerDirection`.
 *
 * The mid bone's flexion axis must end up perpendicular to the lower bone. With
 * `U` the upper bone's untwisted world frame and `M` the mid bone's rest offset
 * from it, that axis is `U · Ry(theta) · M · x`, so the condition
 * `(U · Ry(theta) · M · x) · L = 0` gives
 *
 *     A·cos(theta) + B·sin(theta) + C = 0
 *
 * which is solved in closed form. Two solutions exist — one bends the joint
 * forwards, one backwards — and the joint's own limits pick the branch.
 */
function hingeTwist(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  chain: IKChain,
  upperDirection: Vector3,
  lowerDirection: Vector3,
): number {
  // The untwisted reference must be the same decomposition the solve will
  // ultimately write, or the twist solved here lands against a different frame.
  restWorldQuaternion(skeleton, evaluation, chain.root, tmp.restQuaternion);
  const swing = swingFor(skeleton, evaluation, chain.root, upperDirection, 0);
  tmp.swing.setFromEuler(tmp.euler.set(swing.x, swing.y, swing.z, EULER_ORDER));
  const untwisted = tmp.world.copy(tmp.restQuaternion).multiply(tmp.swing);
  const midRest = skeleton.bone(chain.mid).restLocalQuaternion;

  const m = X_AXIS.clone().applyQuaternion(midRest);
  const u = lowerDirection.clone().applyQuaternion(untwisted.clone().invert());

  const a = m.x * u.x + m.z * u.z;
  const b = m.z * u.x - m.x * u.z;
  const c = m.y * u.y;
  const radius = Math.hypot(a, b);
  if (radius < 1e-9) return 0;

  const phase = Math.atan2(a, b);
  const base = Math.asin(clamp(-c / radius, -1, 1));
  const candidates = [normaliseAngle(base - phase), normaliseAngle(Math.PI - base - phase)];

  const preferPositive = flexesPositive(skeleton, chain.mid);
  let best = candidates[0];
  let bestScore = -Infinity;
  for (const candidate of candidates) {
    const flexion = midFlexionFor(candidate, untwisted, midRest, lowerDirection);
    // Prefer the branch that bends the joint the way it is built to bend, and
    // among equals the one asking for least twist.
    const correctSide = preferPositive === flexion >= 0 ? 1 : 0;
    const score = correctSide * 10 - Math.abs(candidate);
    if (score > bestScore) {
      bestScore = score;
      best = candidate;
    }
  }
  return best;
}

/** Flexion angle the hinge would take for a given upper-bone twist. */
function midFlexionFor(
  twist: number,
  untwisted: Quaternion,
  midRest: Quaternion,
  lowerDirection: Vector3,
): number {
  const frame = new Quaternion()
    .copy(untwisted)
    .multiply(new Quaternion().setFromAxisAngle(Y_AXIS, twist))
    .multiply(midRest);
  const restDirection = Y_AXIS.clone().applyQuaternion(frame);
  const axis = X_AXIS.clone().applyQuaternion(frame);
  const projected = lowerDirection
    .clone()
    .addScaledVector(axis, -lowerDirection.dot(axis));
  if (projected.lengthSq() < 1e-10) return 0;
  projected.normalize();
  return Math.atan2(
    restDirection.clone().cross(projected).dot(axis),
    restDirection.dot(projected),
  );
}

function normaliseAngle(angle: number): number {
  let value = angle % (Math.PI * 2);
  if (value > Math.PI) value -= Math.PI * 2;
  if (value < -Math.PI) value += Math.PI * 2;
  return value;
}

/** True when the joint's flexion range lies mostly on the positive x side. */
function flexesPositive(skeleton: Skeleton, name: IKChain['mid']): boolean {
  const limit = skeleton.bone(name).definition.limits.x;
  if (!limit) return true;
  return limit.max >= -limit.min;
}

/**
 * Point a bone's +Y along `direction`, optionally rolling it about that axis so
 * its +Z faces `forward`. Used to keep a hand square to a bar or a foot flat.
 */
export function aimBone(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  pose: Pose,
  name: Parameters<Skeleton['bone']>[0],
  direction: Vector3,
  forward?: Vector3,
): void {
  setRotation(pose, name, localRotationForDirection(skeleton, evaluation, name, direction));
  if (!forward) {
    evaluation.apply(pose);
    return;
  }
  evaluation.apply(pose);
  const current = Z_AXIS.clone().applyQuaternion(evaluation.quaternion(name));
  const normal = direction.clone().normalize();
  const desired = forward.clone().addScaledVector(normal, -forward.dot(normal));
  if (desired.lengthSq() < 1e-8) return;
  desired.normalize();
  current.addScaledVector(normal, -current.dot(normal));
  if (current.lengthSq() < 1e-8) return;
  current.normalize();
  const angle = Math.atan2(current.clone().cross(desired).dot(normal), current.dot(desired));
  setRotation(
    pose,
    name,
    localRotationForDirection(skeleton, evaluation, name, direction, angle),
  );
  evaluation.apply(pose);
}
