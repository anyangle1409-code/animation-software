import { Quaternion, Vector3 } from 'three';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose, Vec3 } from '../rig/types';
import { vec3 } from '../rig/types';
import { IK_CHAINS } from '../ik/chains';
import { goalFromPose } from '../ik/solve';
import type { IKGoal, IKResult } from '../ik/types';
import { solveGoals } from '../ik/solve';
import type { EffectorLock } from './types';

/** Where an equipment socket currently is, supplied by the equipment layer. */
export interface SocketTransform {
  position: Vector3;
  quaternion: Quaternion;
}

export type SocketResolver = (equipmentId: string, socket: string) => SocketTransform | null;

const scratchDirection = new Vector3();
const scratchForward = new Vector3();
const Y_AXIS = new Vector3(0, 1, 0);
const Z_AXIS = new Vector3(0, 0, 1);

/**
 * Turn locks into IK goals for the current frame.
 *
 * A lock is the difference between equipment that loosely follows a hand and a
 * hand that is genuinely held to the equipment: the effector's target comes
 * from the lock, so the solve has no choice but to honour it.
 */
export function resolveLocks(
  evaluation: PoseEvaluation,
  pose: Pose,
  locks: EffectorLock[],
  resolveSocket?: SocketResolver,
  anchors?: Map<string, Vec3>,
): IKGoal[] {
  const goals: IKGoal[] = [];
  evaluation.apply(pose);

  for (const lock of locks) {
    if (!lock.enabled) continue;
    const base = goalFromPose(evaluation, pose, lock.chain);
    const goal: IKGoal = { ...base, pole: lock.pole ?? base.pole };

    switch (lock.mode) {
      case 'world': {
        if (!lock.position) continue;
        goal.target = { ...lock.position };
        break;
      }
      case 'floor': {
        // Hold the contact exactly where the repetition started. Deriving the
        // height from the mesh instead would ask the leg to reach somewhere it
        // cannot, and the foot would visibly sink and slide.
        const anchor = lock.position ?? anchors?.get(lock.id);
        const current = evaluation.head(IK_CHAINS[lock.chain].end, new Vector3());
        goal.target = vec3(
          anchor?.x ?? current.x,
          anchor?.y ?? current.y,
          anchor?.z ?? current.z,
        );
        break;
      }
      case 'equipment': {
        if (!resolveSocket || !lock.equipmentId || !lock.socket) continue;
        const transform = resolveSocket(lock.equipmentId, lock.socket);
        if (!transform) continue;
        goal.target = vec3(transform.position.x, transform.position.y, transform.position.z);
        // A gripped hand takes the socket's orientation, not just its position.
        scratchDirection.copy(Y_AXIS).applyQuaternion(transform.quaternion);
        scratchForward.copy(Z_AXIS).applyQuaternion(transform.quaternion);
        goal.endAim = {
          direction: vec3(scratchDirection.x, scratchDirection.y, scratchDirection.z),
          forward: vec3(scratchForward.x, scratchForward.y, scratchForward.z),
        };
        break;
      }
    }

    if (lock.aim) goal.endAim = lock.aim;
    goals.push(goal);
  }
  return goals;
}

/**
 * Where each lock's effector sits in the clip's opening pose. Computed once per
 * clip and reused for every frame, which is what actually stops feet sliding.
 */
export function lockAnchors(
  evaluation: PoseEvaluation,
  pose: Pose,
  locks: EffectorLock[],
): Map<string, Vec3> {
  evaluation.apply(pose);
  const anchors = new Map<string, Vec3>();
  const position = new Vector3();
  for (const lock of locks) {
    if (lock.mode !== 'floor') continue;
    evaluation.head(IK_CHAINS[lock.chain].end, position);
    anchors.set(lock.id, vec3(position.x, position.y, position.z));
  }
  return anchors;
}

/** Resolve locks and solve them in one step. `pose` is mutated. */
export function applyLocks(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  pose: Pose,
  locks: EffectorLock[],
  resolveSocket?: SocketResolver,
  anchors?: Map<string, Vec3>,
): IKResult[] {
  const goals = resolveLocks(evaluation, pose, locks, resolveSocket, anchors);
  return solveGoals(skeleton, evaluation, pose, goals);
}

/** A lock that pins an effector wherever it currently is. */
export function lockFromPose(
  evaluation: PoseEvaluation,
  pose: Pose,
  lock: Omit<EffectorLock, 'position' | 'pole'>,
): EffectorLock {
  const goal = goalFromPose(evaluation, pose, lock.chain);
  const position: Vec3 = { ...goal.target };
  return { ...lock, position, pole: goal.pole };
}
