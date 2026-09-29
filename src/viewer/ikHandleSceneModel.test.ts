import { describe, expect, it } from 'vitest';
import { IK_CHAIN_IDS } from '../ik/chains';
import {
  buildHgIKHandleSceneModel,
  HG_IK_HANDLE_COLOURS,
  hgIKHandleKey,
  resolveHgIKHandleAppearance,
} from './ikHandleSceneModel';

describe('first-party IK handle scene model', () => {
  it('owns target/pole primitive geometry and base material state', () => {
    const model = buildHgIKHandleSceneModel();
    expect(model).toHaveLength(IK_CHAIN_IDS.length * 2);

    const target = model.find((entry) => entry.key === 'arm_l:target')!;
    expect(target.geometry).toEqual({ kind: 'box', size: [0.045, 0.045, 0.045] });
    expect(target.material).toEqual({
      colour: HG_IK_HANDLE_COLOURS.target,
      transparent: true,
      opacity: 0.9,
      depthTest: false,
    });

    const pole = model.find((entry) => entry.key === 'arm_l:pole')!;
    expect(pole.geometry).toEqual({ kind: 'octahedron', radius: 0.032 });
    expect(hgIKHandleKey('leg_r', 'pole')).toBe('leg_r:pole');
  });

  it('owns selected/unselected colour and emissive rules', () => {
    expect(resolveHgIKHandleAppearance('arm_r', 'target', null)).toEqual({
      colour: HG_IK_HANDLE_COLOURS.target,
      emissive: HG_IK_HANDLE_COLOURS.emissiveOff,
      emissiveIntensity: 0,
    });
    expect(resolveHgIKHandleAppearance(
      'arm_r',
      'target',
      { chain: 'arm_r', kind: 'target' },
    )).toEqual({
      colour: HG_IK_HANDLE_COLOURS.selected,
      emissive: HG_IK_HANDLE_COLOURS.selected,
      emissiveIntensity: 0.5,
    });
  });
});
