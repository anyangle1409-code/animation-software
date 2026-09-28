import fs from 'node:fs';
import { describe, expect, it } from 'vitest';
import { HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS } from '../rig/originalDimensions';
import {
  EQUIPMENT_LIBRARY,
  PULLUP_GRIP_HALF_WIDTH,
  PULLUP_GRIP_TO_V4_SHOULDER_RATIO,
} from './library';

describe('first-party equipment body-relative dimensions', () => {
  it('expresses pull-up grip width only against the independent v4 shoulder target', () => {
    const rack = EQUIPMENT_LIBRARY.squat_rack;
    const left = rack.sockets.find((socket) => socket.id === 'pullup_l')!;
    const right = rack.sockets.find((socket) => socket.id === 'pullup_r')!;

    expect(left.position.x).toBe(-PULLUP_GRIP_HALF_WIDTH);
    expect(right.position.x).toBe(PULLUP_GRIP_HALF_WIDTH);
    expect(right.position.x - left.position.x).toBeCloseTo(0.54734, 12);
    expect(
      (right.position.x - left.position.x) /
        HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS.shoulderBreadth,
    ).toBeCloseTo(PULLUP_GRIP_TO_V4_SHOULDER_RATIO, 15);
  });

  it('does not import the active humanoid rig or its fit constants', () => {
    const source = fs.readFileSync(new URL('./library.ts', import.meta.url), 'utf8');
    expect(source).not.toContain("../rig/humanoid");
    expect(source).not.toContain('SHOULDER_' + 'WIDENING');
  });
});
