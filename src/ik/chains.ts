import type { IKChain, IKChainId } from './types';

export const IK_CHAINS: Record<IKChainId, IKChain> = {
  arm_l: {
    id: 'arm_l',
    label: 'Left arm',
    root: 'upperarm_l',
    mid: 'forearm_l',
    end: 'hand_l',
    poleLabel: 'Left elbow',
  },
  arm_r: {
    id: 'arm_r',
    label: 'Right arm',
    root: 'upperarm_r',
    mid: 'forearm_r',
    end: 'hand_r',
    poleLabel: 'Right elbow',
  },
  leg_l: {
    id: 'leg_l',
    label: 'Left leg',
    root: 'thigh_l',
    mid: 'shin_l',
    end: 'foot_l',
    poleLabel: 'Left knee',
  },
  leg_r: {
    id: 'leg_r',
    label: 'Right leg',
    root: 'thigh_r',
    mid: 'shin_r',
    end: 'foot_r',
    poleLabel: 'Right knee',
  },
};

export const IK_CHAIN_IDS = Object.keys(IK_CHAINS) as IKChainId[];

export const isArmChain = (id: IKChainId): boolean => id.startsWith('arm');
