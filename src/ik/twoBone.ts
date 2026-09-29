import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose, Vec3 } from '../rig/types';
import { HgQuat, HgVec3 } from '../core/linearMath';
import { clamp } from '../core/math';
import { setRotation } from './orient';
import {
  hgHingeRotationForDirection,
  hgLocalRotationForDirection,
  hgRestWorldQuaternion,
  hgSwingFor,
} from './firstPartyOrient';
import type { IKChain, IKResult } from './types';

const EPSILON = 1e-6;
const HG_Z_AXIS = new HgVec3(0, 0, 1);

const tmp = {
  rootHead: new HgVec3(),
  midHead: new HgVec3(),
  effector: new HgVec3(),
  target: new HgVec3(),
  pole: new HgVec3(),
  toTarget: new HgVec3(),
  direction: new HgVec3(),
  poleVector: new HgVec3(),
  poleOrtho: new HgVec3(),
  upperDirection: new HgVec3(),
  lowerDirection: new HgVec3(),
  clampedTarget: new HgVec3(),
  restQuaternion: new HgQuat(),
  swing: new HgQuat(),
  world: new HgQuat(),
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
  target: Vec3,
  pole: Vec3,
): IKResult {
  const upperBone = skeleton.bone(chain.root);
  const midBone = skeleton.bone(chain.mid);
  const upperLength = upperBone.length;
  const lowerLength = midBone.length;

  evaluation.apply(pose);
  const fk = evaluation.firstPartyEvaluation;
  fk.head(chain.root, tmp.rootHead);
  fk.head(chain.mid, tmp.midHead);
  tmp.target.set(target.x, target.y, target.z);
  tmp.pole.set(pole.x, pole.y, pole.z);

  tmp.toTarget.subVectors(tmp.target, tmp.rootHead);
  const rawDistance = tmp.toTarget.length();
  const overExtended = rawDistance > upperLength + lowerLength;

  if (rawDistance < EPSILON) {
    return { chain: chain.id, error: rawDistance, reached: false, overExtended: false };
  }
  tmp.direction.copy(tmp.toTarget).multiplyScalar(1 / rawDistance);

  // Keep the triangle solvable: never fully locked out, never folded through itself.
  const minReach = Math.abs(upperLength - lowerLength) + 1e-4;
  const maxReach = (upperLength + lowerLength) * 0.9995;
  const distance = clamp(rawDistance, minReach, maxReach);
  tmp.clampedTarget.copy(tmp.rootHead).addScaledVector(tmp.direction, distance);

  // Pole direction, orthogonalised against the root-to-target line.
  tmp.poleVector.subVectors(tmp.pole, tmp.rootHead);
  tmp.poleOrtho
    .copy(tmp.poleVector)
    .addScaledVector(tmp.direction, -tmp.poleVector.dot(tmp.direction));
  if (tmp.poleOrtho.lengthSq() < 1e-8) {
    // Degenerate pole (on the line): fall back to the limb's current bend plane.
    tmp.poleOrtho
      .subVectors(tmp.midHead, tmp.rootHead)
      .addScaledVector(tmp.direction, -tmp.poleVector.dot(tmp.direction));
    if (tmp.poleOrtho.lengthSq() < 1e-8) {
      tmp.poleOrtho.copy(HG_Z_AXIS).addScaledVector(tmp.direction, -tmp.direction.z);
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
    hgLocalRotationForDirection(skeleton.firstParty, fk, chain.root, tmp.upperDirection, twist),
  );
  evaluation.apply(pose);

  // Re-aim the lower bone from where the upper bone actually ended up, which
  // may differ from the ideal if a joint limit clamped the solve.
  fk.head(chain.mid, tmp.midHead);
  tmp.lowerDirection.subVectors(tmp.target, tmp.midHead);
  if (tmp.lowerDirection.lengthSq() < EPSILON) tmp.lowerDirection.copy(tmp.upperDirection);
  tmp.lowerDirection.normalize();

  setRotation(
    pose,
    chain.mid,
    hgHingeRotationForDirection(skeleton.firstParty, fk, chain.mid, tmp.lowerDirection),
  );
  evaluation.apply(pose);

  fk.head(chain.end, tmp.effector);
  const error = tmp.effector.distanceTo(tmp.target);
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
  upperDirection: HgVec3,
  lowerDirection: HgVec3,
): number {
  // The untwisted reference must be the same decomposition the solve will
  // ultimately write, or the twist solved here lands against a different frame.
  hgRestWorldQuaternion(skeleton.firstParty, evaluation.firstPartyEvaluation, chain.root, tmp.restQuaternion);
  const swing = hgSwingFor(
    skeleton.firstParty,
    evaluation.firstPartyEvaluation,
    chain.root,
    upperDirection,
    0,
  );
  tmp.swing.setFromEulerXZY(swing.x, swing.y, swing.z);
  const untwisted = tmp.world.copy(tmp.restQuaternion).multiply(tmp.swing);
  const midRest = skeleton.firstParty.bone(chain.mid).restLocalQuaternion;

  const m = new HgVec3(1, 0, 0).applyQuaternion(midRest);
  const u = lowerDirection.clone()
    .applyQuaternion(untwisted.clone().invert());

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
  untwisted: HgQuat,
  midRest: HgQuat,
  lowerDirection: HgVec3,
): number {
  const frame = new HgQuat()
    .copy(untwisted)
    .multiply(new HgQuat().setFromAxisAngle(new HgVec3(0, 1, 0), twist))
    .multiply(midRest);
  const restDirection = new HgVec3(0, 1, 0).applyQuaternion(frame);
  const axis = new HgVec3(1, 0, 0).applyQuaternion(frame);
  const projected = lowerDirection.clone().addScaledVector(axis, -lowerDirection.dot(axis));
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
  direction: Vec3,
  forward?: Vec3,
): void {
  const aimedDirection = new HgVec3(direction.x, direction.y, direction.z);
  const fk = evaluation.firstPartyEvaluation;
  setRotation(
    pose,
    name,
    hgLocalRotationForDirection(skeleton.firstParty, fk, name, aimedDirection),
  );
  if (!forward) {
    evaluation.apply(pose);
    return;
  }
  evaluation.apply(pose);
  const current = HG_Z_AXIS.clone().applyQuaternion(fk.quaternion(name));
  const normal = aimedDirection.clone().normalize();
  const desired = new HgVec3(forward.x, forward.y, forward.z);
  desired.addScaledVector(normal, -desired.dot(normal));
  if (desired.lengthSq() < 1e-8) return;
  desired.normalize();
  current.addScaledVector(normal, -current.dot(normal));
  if (current.lengthSq() < 1e-8) return;
  current.normalize();
  const angle = Math.atan2(current.clone().cross(desired).dot(normal), current.dot(desired));
  setRotation(
    pose,
    name,
    hgLocalRotationForDirection(skeleton.firstParty, fk, name, aimedDirection, angle),
  );
  evaluation.apply(pose);
}
