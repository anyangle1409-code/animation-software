import { describe, expect, it } from 'vitest';
import { HgQuat, HgVec3 } from '../core/linearMath';
import {
  CORRECTED_HAND_FRAME,
  handFrameTurn,
  inHandFrame,
} from '../character/retargetSource';

describe('grip metadata hand-frame compatibility', () => {
  const earlierFrame = {
    l: new HgQuat().setFromAxisAngle(new HgVec3(0, 1, 0), 0.1),
    r: new HgQuat(),
  };

  it('turns earlier-frame grip offsets into the corrected hand frame when required', () => {
    const offsets = {
      l: { x: 0.015, y: 0.055, z: 0.012 },
      r: { x: -0.015, y: 0.055, z: 0.012 },
    };
    const turned = inHandFrame(offsets, handFrameTurn(undefined, earlierFrame))!;
    const expected = new HgVec3(0.015, 0.055, 0.012).applyHgQuat(earlierFrame.l);
    expect(new HgVec3(turned.l!.x, turned.l!.y, turned.l!.z).distanceTo(expected)).toBeLessThan(1e-15);
    expect(turned.r).toEqual(offsets.r);
    expect(inHandFrame(offsets, handFrameTurn(CORRECTED_HAND_FRAME, earlierFrame))).toEqual(offsets);
    expect(inHandFrame(undefined, earlierFrame)).toBeUndefined();
  });
});
