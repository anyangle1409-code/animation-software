import { describe, expect, it } from 'vitest';
import { Quaternion, Vector3 } from 'three';
import {
  CORRECTED_HAND_FRAME,
  handFrameTurn,
  inHandFrame,
} from '../character/retargetSource';

describe('grip metadata hand-frame compatibility', () => {
  const earlierFrame = {
    l: new Quaternion().setFromAxisAngle(new Vector3(0, 1, 0), 0.1),
    r: new Quaternion(),
  };

  it('turns earlier-frame grip offsets into the corrected hand frame when required', () => {
    const offsets = {
      l: { x: 0.015, y: 0.055, z: 0.012 },
      r: { x: -0.015, y: 0.055, z: 0.012 },
    };
    const turned = inHandFrame(offsets, handFrameTurn(undefined, earlierFrame))!;
    const expected = new Vector3(0.015, 0.055, 0.012).applyQuaternion(earlierFrame.l);
    expect(new Vector3(turned.l!.x, turned.l!.y, turned.l!.z).distanceTo(expected)).toBeLessThan(1e-15);
    expect(turned.r).toEqual(offsets.r);
    expect(inHandFrame(offsets, handFrameTurn(CORRECTED_HAND_FRAME, earlierFrame))).toEqual(offsets);
    expect(inHandFrame(undefined, earlierFrame)).toBeUndefined();
  });
});
