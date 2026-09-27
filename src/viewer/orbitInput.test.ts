import { describe, expect, it } from 'vitest';
import { HgOrbitPointerTracker, wheelZoomFactor } from './orbitInput';

describe('first-party orbit input', () => {
  it('turns a desktop primary-pointer drag into rotation pixels', () => {
    const input = new HgOrbitPointerTracker();
    input.pointerDown(1, 100, 120);
    expect(input.pointerMove(1, 116, 91)).toEqual({
      rotateX: 16,
      rotateY: -29,
    });
  });

  it('uses one iPhone touch for rotation', () => {
    const input = new HgOrbitPointerTracker();
    input.pointerDown(7, 20, 30);
    expect(input.pointerMove(7, 26, 39)).toEqual({
      rotateX: 6,
      rotateY: 9,
    });
  });

  it('uses a two-finger iPhone pinch for proportional zoom', () => {
    const input = new HgOrbitPointerTracker();
    input.pointerDown(3, 0, 0);
    input.pointerDown(4, 100, 0);
    expect(input.pointerMove(4, 125, 0)).toEqual({ zoomFactor: 0.8 });
    expect(input.pointerMove(4, 75, 0)).toEqual({ zoomFactor: 5 / 3 });
  });

  it('rebases the remaining finger when a pinch ends', () => {
    const input = new HgOrbitPointerTracker();
    input.pointerDown(3, 10, 10);
    input.pointerDown(4, 30, 10);
    input.pointerUp(4);
    expect(input.pointerMove(3, 12, 13)).toEqual({ rotateX: 2, rotateY: 3 });
  });

  it('maps wheel motion to finite multiplicative zoom', () => {
    expect(wheelZoomFactor(-120)).toBeGreaterThan(0);
    expect(wheelZoomFactor(-120)).toBeLessThan(1);
    expect(wheelZoomFactor(120)).toBeGreaterThan(1);
    expect(wheelZoomFactor(Number.NaN)).toBe(1);
  });
});
