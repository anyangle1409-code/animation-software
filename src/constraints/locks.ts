import { Quaternion, Vector3 } from 'three';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Pose, Vec3 } from '../rig/types';
import { vec3 } from '../rig/types';
import { clonePose } from '../rig/pose';
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
        if (lock.onBall) {
          const ball = evaluation.tail(IK_CHAINS[lock.chain].end, new Vector3());
          const at = anchor ?? vec3(ball.x, ball.y, ball.z);
          goal.target = { ...at };
          goal.ball = { anchor: { ...at }, ankle: lock.onBall.ankle, toeOut: lock.onBall.toeOut ?? 0 };
          break;
        }
        const current = evaluation.head(IK_CHAINS[lock.chain].end, new Vector3());
        goal.target = vec3(
          anchor?.x ?? current.x,
          anchor?.y ?? current.y,
          anchor?.z ?? current.z,
        );
        const direction = lock.holdOrientation ? anchors?.get(orientationKey(lock.id, 'direction')) : undefined;
        const forward = lock.holdOrientation ? anchors?.get(orientationKey(lock.id, 'forward')) : undefined;
        if (direction && forward) goal.endAim = { direction: { ...direction }, forward: { ...forward } };
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
    // A foot standing on its ball is anchored at the ball, not the ankle.
    if (lock.onBall) evaluation.tail(IK_CHAINS[lock.chain].end, position);
    else evaluation.head(IK_CHAINS[lock.chain].end, position);
    anchors.set(lock.id, vec3(position.x, position.y, position.z));
  }

  // The orientation to hold is the one the opening frame is *shown* with, which
  // is the pose after its locks are solved, not the pose as authored: the solve
  // turns the shin about the leg to meet its pole, and the foot turns with it —
  // measured, by 15° on a hinge's standing leg. Holding the authored orientation
  // instead would twist the foot against the shin at the very first frame.
  const held = locks.filter((lock) => lock.mode === 'floor' && lock.enabled && lock.holdOrientation);
  if (held.length > 0) {
    const solved = clonePose(pose);
    const floorLocks = locks
      .filter((lock) => lock.mode === 'floor')
      .map((lock) => ({ ...lock, holdOrientation: false }));
    solveGoals(evaluation.skeleton, evaluation, solved, resolveLocks(evaluation, solved, floorLocks, undefined, anchors));
    evaluation.apply(solved);
    for (const lock of held) {
      const turn = evaluation.quaternion(IK_CHAINS[lock.chain].end);
      const direction = scratchDirection.copy(Y_AXIS).applyQuaternion(turn);
      const forward = scratchForward.copy(Z_AXIS).applyQuaternion(turn);
      anchors.set(orientationKey(lock.id, 'direction'), vec3(direction.x, direction.y, direction.z));
      anchors.set(orientationKey(lock.id, 'forward'), vec3(forward.x, forward.y, forward.z));
    }
    evaluation.apply(pose);
  }
  return anchors;
}

/**
 * Where a lock that holds its orientation keeps it among the anchors: the end
 * bone's +Y and +Z in the opening pose, beside its position. Keyed apart from
 * the position so every existing reader of the map is unchanged.
 */
const orientationKey = (id: string, axis: 'direction' | 'forward') => `${id}#${axis}`;

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
