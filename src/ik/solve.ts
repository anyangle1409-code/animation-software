import { HgQuat, HgVec3 } from '../core/linearMath';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose, Vec3 } from '../rig/types';
import { vec3 } from '../rig/types';
import { IK_CHAINS } from './chains';
import { aimBone, solveTwoBone } from './twoBone';
import type { IKChainId, IKGoal, IKResult } from './types';
import type { BoneName } from '../rig/boneNames';

const scratchTarget = new HgVec3();
const scratchPole = new HgVec3();
const scratchDirection = new HgVec3();
const scratchForward = new HgVec3();

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
    if (goal.ball) {
      results.push(standOnBall(skeleton, evaluation, pose, chain, goal));
      continue;
    }
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
function aimMiss(evaluation: PoseEvaluation, name: BoneName, direction: Vec3, forward: Vec3): number {
  const turn = evaluation.firstPartyEvaluation.quaternion(name);
  return Math.max(
    missScratch.copy(HG_Y_AXIS).applyQuaternion(turn).angleTo(
      aimDirection.set(direction.x, direction.y, direction.z),
    ),
    missScratch.copy(HG_Z_AXIS).applyQuaternion(turn).angleTo(
      aimForward.set(forward.x, forward.y, forward.z),
    ),
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
  direction: Vec3,
  forward: Vec3,
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
const HG_X_AXIS = new HgVec3(1, 0, 0);
const HG_Y_AXIS = new HgVec3(0, 1, 0);
const HG_Z_AXIS = new HgVec3(0, 0, 1);
const missScratch = new HgVec3();
const aimDirection = new HgVec3();
const aimForward = new HgVec3();

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
  const fk = evaluation.firstPartyEvaluation;
  const root = fk.head(chain.root, new HgVec3());
  const mid = fk.head(chain.mid, new HgVec3());
  const end = fk.head(chain.end, new HgVec3());

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

export const goalTargetVector = (goal: IKGoal): Vec3 => goal.target;

/**
 * A foot standing on its ball: the ball stays put, the toes lie flat, and the
 * heel rises about the ball until the ankle is at the angle asked.
 *
 * The heel's height is the one unknown. Raising it pitches the foot further
 * down, which plantarflexes the ankle for a given shin, so the ankle angle falls
 * steadily as the heel rises and a bisection finds it. The heel rises no higher
 * than the toes can bend back to stay flat; past that the ankle bends further
 * instead, which is what a real back foot does at the bottom of a lunge. Each trial places the
 * ankle where that heel height puts it, solves the leg to it, and holds the foot
 * at that pitch, with the shin taking any twist the ankle cannot, as it does
 * for a flat foot.
 */
function standOnBall(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  pose: Pose,
  chain: (typeof IK_CHAINS)[IKChainId],
  goal: IKGoal,
): IKResult {
  const ball = goal.ball!;
  const foot = skeleton.bone(chain.end);
  const toe = skeleton.bones.find((bone) => bone.parent === chain.end);
  const side = chain.end.endsWith('_r') ? -1 : 1;
  const yaw = new HgQuat().setFromAxisAngle(HG_Y_AXIS, (-side * ball.toeOut * Math.PI) / 180);
  const anchor = new HgVec3(ball.anchor.x, ball.anchor.y, ball.anchor.z);
  const pole = new HgVec3(goal.pole.x, goal.pole.y, goal.pole.z);
  const direction = new HgVec3();
  const forward = new HgVec3();
  const ankle = new HgVec3();
  let result: IKResult = { chain: chain.id, error: Infinity, reached: false, overExtended: false };

  const place = (raise: number) => {
    const turn = new HgQuat()
      .copy(yaw)
      .multiply(new HgQuat().setFromAxisAngle(HG_X_AXIS, (raise * Math.PI) / 180))
      .multiply(skeleton.firstParty.bone(chain.end).restWorldQuaternion);
    direction.copy(HG_Y_AXIS).applyQuaternion(turn);
    forward.copy(HG_Z_AXIS).applyQuaternion(turn);
    ankle.copy(anchor).addScaledVector(direction, -foot.length);
    result = solveTwoBone(skeleton, evaluation, pose, chain, ankle, pole);
    aimBone(skeleton, evaluation, pose, chain.end, direction, forward);
    settleTibialRotation(skeleton, evaluation, pose, chain, direction, forward);
    return ((pose.rotations[chain.end]?.x ?? 0) * 180) / Math.PI;
  };

  // The heel rises no further than the toes can bend back to stay flat under
  // it; past that the ankle bends instead.
  const toeReach = toe?.definition.limits.x?.max ?? 85;
  let low = 0;
  let high = Math.min(85, toeReach - 1);
  // Raising the heel lowers the foot's angle to the shin and, lifting the
  // ankle towards the hip, bends the knee; either can be held.
  const knee = () => ((pose.rotations[chain.mid]?.x ?? 0) * 180) / Math.PI;
  for (let step = 0; step < 24; step += 1) {
    const middle = (low + high) / 2;
    const ankleAngle = place(middle);
    if (ball.knee !== undefined ? knee() > ball.knee : ankleAngle > ball.ankle) low = middle;
    else high = middle;
  }
  place((low + high) / 2);

  if (toe) {
    // The toes lie flat on the floor, turned out with the foot.
    const flat = new HgQuat().copy(yaw).multiply(skeleton.firstParty.bone(toe.name).restWorldQuaternion);
    const toeDirection = HG_Y_AXIS.clone().applyQuaternion(flat);
    const toeForward = HG_Z_AXIS.clone().applyQuaternion(flat);
    aimBone(
      skeleton,
      evaluation,
      pose,
      toe.name,
      toeDirection,
      toeForward,
    );
  }
  evaluation.apply(pose);
  const reachedBall = evaluation.firstPartyEvaluation.tail(chain.end, new HgVec3()).distanceTo(anchor);
  return { ...result, error: Math.max(result.error, reachedBall), reached: result.reached && reachedBall < 2e-3 };
}
