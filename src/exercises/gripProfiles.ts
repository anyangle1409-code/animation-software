import type { GripKind } from './types';

export interface GripProfile {
  id: GripKind;
  label: string;
  /** Flexion degrees for MCP / PIP / DIP of the four fingers at closure 1. */
  fingers: readonly [number, number, number];
  /** Thumb Z rotations for its three available segments at closure 1. */
  thumb: readonly [number, number, number];
  /** Thumb-base X rotation used as the rig's limited opposition proxy. */
  thumbOppositionX: number;
}

export const GRIP_PROFILES: Record<GripKind, GripProfile> = {
  none: {
    id: 'none',
    label: 'Open / relaxed',
    fingers: [0, 0, 0],
    thumb: [0, 0, 0],
    thumbOppositionX: 0,
  },
  // Compatibility baseline: these values are the original production curl hand.
  dumbbell: {
    id: 'dumbbell',
    label: 'Dumbbell wrap',
    fingers: [78, 95, 60],
    thumb: [-22, 60, 60],
    thumbOppositionX: -14,
  },
  bar: {
    id: 'bar',
    label: 'Bar / pull-up wrap',
    fingers: [76, 98, 66],
    thumb: [-24, 64, 64],
    thumbOppositionX: -14,
  },
  handle: {
    id: 'handle',
    label: 'Neutral handle',
    fingers: [82, 100, 68],
    thumb: [-26, 68, 65],
    thumbOppositionX: -14,
  },
  rope: {
    id: 'rope',
    label: 'Rope / thick handle',
    fingers: [88, 105, 72],
    thumb: [-28, 70, 68],
    thumbOppositionX: -14,
  },
  // A floor contact is a spread hand, not a cylindrical grip. Existing push-up
  // closure is only 0.05, so this keeps the fingers essentially straight.
  floor: {
    id: 'floor',
    label: 'Floor / open palm',
    fingers: [18, 12, 8],
    thumb: [6, 8, 6],
    thumbOppositionX: -4,
  },
};

export const GRIP_PROFILE_LIST = Object.values(GRIP_PROFILES);

export function gripProfile(grip: GripKind): GripProfile {
  return GRIP_PROFILES[grip];
}
