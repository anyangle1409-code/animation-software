import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { bodyNormalization, normalizeDelta, normalizePoint } from './normalize';

describe('reference body normalization', () => {
  it('derives stable canonical body scales from the frozen rig geometry', () => {
    const scale = bodyNormalization(canonicalSkeleton);
    expect(scale.standingHeight).toBeCloseTo(1.75, 6);
    expect(scale.shoulderWidth).toBeCloseTo(0.40734, 6);
    expect(scale.armLength).toBeCloseTo(0.65, 6);
    expect(scale.torsoLength).toBeGreaterThan(0.4);
    expect(scale.torsoLength).toBeLessThan(0.6);
  });

  it('normalizes distances and points without pixels', () => {
    expect(normalizeDelta(0.17, 0.34)).toBeCloseTo(0.5, 8);
    expect(normalizePoint({ x: 0.17, y: 1, z: -0.1 }, { x: 0, y: 0.9, z: 0 }, 0.34)).toEqual({
      x: 0.5,
      y: expect.closeTo(0.294117647, 8),
      z: expect.closeTo(-0.294117647, 8),
    });
  });

  it('refuses a zero normalization scale', () => {
    expect(() => normalizeDelta(1, 0)).toThrow(/zero scale/);
  });
});
