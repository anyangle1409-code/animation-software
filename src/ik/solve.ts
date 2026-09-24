import { Vector3 } from 'three';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose, Vec3 } from '../rig/types';
import { vec3 } from '../rig/types';
import { IK_CHAINS } from './chains';
import { aimBone, solveTwoBone } from './twoBone';
import type { IKChainId, IKGoal, IKResult } from './types';
import type { BoneName } from '../rig/boneNames';

const scratchTarget = new Vector3();
const scratchPole = new Vector3();
const scratchDirection = new Vector3();
const scratchForward = new Vector3();

/**
 * Apply every enabled goal to `pose` (mutating). Chains are independent — an
 * arm solve cannot disturb a leg — so a single pass is exact.
 */
export function solveGoals(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  pose: Pose,
  goals: IKGoal[],
): IKResult[] {
  const results: IKResult[] = [];
  for (const goal of goals) {
    if (!goal.enabled) continue;
    const chain = IK_CHAINS[goal.chain];
    scratchTarget.set(goal.target.x, goal.target.y, goal.target.z);
    scratchPole.set(goal.pole.x, goal.pole.y, goal.pole.z);
    results.push(solveTwoBone(skeleton, evaluation, pose, chain, scratchTarget, scratchPole));

    if (goal.endAim) {
      scratchDirection.set(
        goal.endAim.direction.x,
        goal.endAim.direction.y,
        goal.endAim.direction.z,
      );
      const forward = goal.endAim.forward;
      aimBone(
        skeleton,
        evaluation,
        pose,
        chain.end,
        scratchDirection,
        forward ? scratchForward.set(forward.x, forward.y, forward.z) : undefined,
      );
      if (forward && chain.mid.startsWith('shin_')) {
        settleTibialRotation(skeleton, evaluation, pose, chain, scratchDirection, scratchForward);
      }
    }
  }
  return results;
}

/** How far the end bone is from the orientation it was aimed at, radians. */
function aimMiss(evaluation: PoseEvaluation, name: BoneName, direction: Vector3, forward: Vector3): number {
  const turn = evaluation.quaternion(name);
  return Math.max(
    missScratch.copy(Y_AXIS).applyQuaternion(turn).angleTo(direction),
    missScratch.copy(Z_AXIS).applyQuaternion(turn).angleTo(forward),
  );
}

/**
 * A foot held flat that its own joint cannot keep flat: turn the shin about
 * its own axis to make up the difference.
 *
 * The two-bone solve leaves the knee a pure hinge, so any change in the leg's
 * twist lands on the ankle, whose side-to-side range is ±10°. A squatting leg
 * twists by more than that as the knee bends, and the foot swivels on the
 * floor. A real knee takes that twist itself — the tibia rotates on a bent knee
 * — and the rig has the axis for it (`shin` y, ±15°). Turning the shin about its
 * own axis does not move the ankle, so the contact is untouched.
 *
 * Only runs when the ankle alone has fallen short, so a foot already reached
 * is solved exactly as before.
 */
function settleTibialRotation(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  pose: Pose,
  chain: (typeof IK_CHAINS)[IKChainId],
  direction: Vector3,
  forward: Vector3,
): void {
  if (aimMiss(evaluation, chain.end, direction, forward) < TIBIAL_TOLERANCE) return;
  const limit = skeleton.bone(chain.mid).definition.limits.y;
  if (!limit) return;
  const hinge = { ...(pose.rotations[chain.mid] ?? { x: 0, y: 0, z: 0 }) };
  const tryTwist = (degrees: number) => {
    pose.rotations[chain.mid] = { ...hinge, y: (degrees * Math.PI) / 180 };
    evaluation.apply(pose);
    aimBone(skeleton, evaluation, pose, chain.end, direction, forward);
    return aimMiss(evaluation, chain.end, direction, forward);
  };
  let best = { degrees: 0, miss: Number.POSITIVE_INFINITY };
  for (let degrees = limit.min; degrees <= limit.max + 1e-9; degrees += 1) {
    const miss = tryTwist(degrees);
    if (miss < best.miss) best = { degrees, miss };
  }
  for (let degrees = best.degrees - 1; degrees <= best.degrees + 1 + 1e-9; degrees += 0.05) {
    if (degrees < limit.min || degrees > limit.max) continue;
    const miss = tryTwist(degrees);
    if (miss < best.miss) best = { degrees, miss };
  }
  tryTwist(best.degrees);
}

/** A foot within this of its aim is left as the ankle placed it (0.05°). */
const TIBIAL_TOLERANCE = (0.05 * Math.PI) / 180;
const Y_AXIS = new Vector3(0, 1, 0);
const Z_AXIS = new Vector3(0, 0, 1);
const missScratch = new Vector3();

/**
 * A goal that holds a limb exactly where it is now, with a pole placed along
 * the limb's current bend. This is what the editor creates when IK is switched
 * on for a limb, so enabling IK never makes the pose jump.
 */
export function goalFromPose(
  evaluation: PoseEvaluation,
  pose: Pose,
  chainId: IKChainId,
): IKGoal {
  const chain = IK_CHAINS[chainId];
  evaluation.apply(pose);
  const root = evaluation.head(chain.root, new Vector3());
  const mid = evaluation.head(chain.mid, new Vector3());
  const end = evaluation.head(chain.end, new Vector3());

  const midpoint = root.clone().add(end).multiplyScalar(0.5);
  const bend = mid.clone().sub(midpoint);
  // A limb that is nearly straight has no meaningful bend plane: a two
  // millimetre offset normalises into a direction that means nothing, and
  // following it wrenches the joint sideways. Below a centimetre, use the
  // anatomical default instead — elbows point back, knees point forward.
  if (bend.length() < 0.01) {
    bend.set(0, 0, chainId.startsWith('arm') ? -1 : 1);
  }
  bend.normalize().multiplyScalar(0.45);

  return {
    chain: chainId,
    enabled: true,
    target: vec3(end.x, end.y, end.z),
    pole: vec3(mid.x + bend.x, mid.y + bend.y, mid.z + bend.z),
  };
}

/** Where a chain's effector currently is, for UI readouts and constraints. */
export function effectorPosition(
  evaluation: PoseEvaluation,
  chainId: IKChainId,
  target = new Vector3(),
): Vector3 {
  return evaluation.head(IK_CHAINS[chainId].end, target);
}

export const goalTargetVector = (goal: IKGoal): Vec3 => goal.target;
