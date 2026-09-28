import { IK_CHAIN_IDS } from '../ik/chains';
import type { IKChainId, IKGoal } from '../ik/types';
import type { Vec3 } from '../rig/types';

export interface IKHandleState {
  readonly visible: boolean;
  readonly position: Vec3;
}

export interface IKChainHandleState {
  readonly target: IKHandleState;
  readonly pole: IKHandleState;
}

export type IKGoalMap = Partial<Record<IKChainId, IKGoal | undefined>>;

const copy = (value: Vec3): Vec3 => ({ x: value.x, y: value.y, z: value.z });

/**
 * Renderer-neutral handle state matching the current IKHandles useFrame policy.
 *
 * Enabled goals draw target and pole at their authored positions. A disabled or
 * absent target is parked on the current effector so enabling IK does not make
 * the handle jump from an unrelated stale location. A disabled goal's pole is
 * retained but hidden, matching the current viewer semantics.
 */
export function resolveIKHandleStates(
  goals: IKGoalMap,
  effectorHead: (chain: IKChainId) => Vec3,
): Map<IKChainId, IKChainHandleState> {
  const out = new Map<IKChainId, IKChainHandleState>();

  for (const chain of IK_CHAIN_IDS) {
    const goal = goals[chain];
    const active = Boolean(goal?.enabled);
    out.set(chain, {
      target: {
        visible: active,
        position: active && goal ? copy(goal.target) : copy(effectorHead(chain)),
      },
      pole: {
        visible: active,
        position: goal ? copy(goal.pole) : { x: 0, y: 0, z: 0 },
      },
    });
  }

  return out;
}
