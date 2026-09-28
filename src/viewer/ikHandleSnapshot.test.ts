import { describe, expect, it } from 'vitest';
import type { IKChainId, IKGoal } from '../ik/types';
import { resolveIKHandleStates } from './ikHandleSnapshot';

const goal = (
  chain: IKChainId,
  enabled: boolean,
  target = { x: 1, y: 2, z: 3 },
  pole = { x: 4, y: 5, z: 6 },
): IKGoal => ({
  chain,
  enabled,
  target,
  pole,
});

const effector = (chain: IKChainId) => ({
  x: chain === 'arm_l' || chain === 'leg_l' ? -0.25 : 0.25,
  y: chain.startsWith('arm') ? 1.2 : 0.15,
  z: 0.1,
});

describe('IK handle snapshot', () => {
  it('uses enabled target and pole positions', () => {
    const result = resolveIKHandleStates({ arm_l: goal('arm_l', true) }, effector);
    expect(result.get('arm_l')).toEqual({
      target: { visible: true, position: { x: 1, y: 2, z: 3 } },
      pole: { visible: true, position: { x: 4, y: 5, z: 6 } },
    });
  });

  it('parks a disabled target on the current effector while keeping the hidden pole position', () => {
    const result = resolveIKHandleStates({ arm_r: goal('arm_r', false) }, effector);
    expect(result.get('arm_r')).toEqual({
      target: { visible: false, position: effector('arm_r') },
      pole: { visible: false, position: { x: 4, y: 5, z: 6 } },
    });
  });

  it('emits all four chains and parks absent goals at their effectors', () => {
    const result = resolveIKHandleStates({}, effector);
    expect([...result.keys()]).toEqual(['arm_l', 'arm_r', 'leg_l', 'leg_r']);
    for (const chain of result.keys()) {
      expect(result.get(chain)?.target).toEqual({ visible: false, position: effector(chain) });
      expect(result.get(chain)?.pole.visible).toBe(false);
    }
  });

  it('copies goal positions so later source mutation cannot change the snapshot', () => {
    const source = goal('leg_l', true, { x: -1, y: 0.5, z: 0.2 }, { x: -2, y: 0.7, z: 0.4 });
    const result = resolveIKHandleStates({ leg_l: source }, effector);
    source.target.x = 99;
    source.pole.y = 99;
    expect(result.get('leg_l')?.target.position.x).toBe(-1);
    expect(result.get('leg_l')?.pole.position.y).toBe(0.7);
  });
});
