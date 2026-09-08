import { Vector3 } from 'three';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose, Vec3 } from '../rig/types';
import { vec3 } from '../rig/types';
import { IK_CHAINS } from './chains';
import { aimBone, solveTwoBone } from './twoBone';
import type { IKChainId, IKGoal, IKResult } from './types';

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
    }
  }
  return results;
}

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
