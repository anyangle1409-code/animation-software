import { describe, expect, it } from 'vitest';
import {
  analyseSilhouetteRgba,
  compareSilhouetteMetrics,
  silhouetteSanity,
} from './silhouette';

function image(width: number, height: number, white: [number, number][]) {
  const rgba = new Uint8Array(width * height * 4);
  for (let index = 0; index < width * height; index += 1) rgba[index * 4 + 3] = 255;
  for (const [x, yTop] of white) {
    const yBottom = height - 1 - yTop;
    const index = (yBottom * width + x) * 4;
    rgba[index] = 255;
    rgba[index + 1] = 255;
    rgba[index + 2] = 255;
    rgba[index + 3] = 255;
  }
  return rgba;
}

describe('deterministic silhouette analysis', () => {
  it('measures top-left image bounds and centroid from bottom-up WebGL pixels', () => {
    const metrics = analyseSilhouetteRgba(
      image(4, 4, [
        [1, 1],
        [2, 1],
        [1, 2],
        [2, 2],
      ]),
      4,
      4,
    );

    expect(metrics.foregroundPixels).toBe(4);
    expect(metrics.areaRatio).toBeCloseTo(0.25, 8);
    expect(metrics.bounds).toEqual({
      minX: 0.25,
      minY: 0.25,
      maxX: 0.75,
      maxY: 0.75,
      width: 0.5,
      height: 0.5,
    });
    expect(metrics.centroid).toEqual({ x: 0.5, y: 0.5 });
    expect(metrics.touches).toEqual({ left: false, right: false, top: false, bottom: false });
  });

  it('flags empty and frame-clipped silhouettes without making a biomechanics claim', () => {
    const empty = analyseSilhouetteRgba(image(4, 4, []), 4, 4);
    expect(silhouetteSanity(empty).passed).toBe(false);
    expect(silhouetteSanity(empty).issues).toContain('silhouette is empty');

    const clipped = analyseSilhouetteRgba(
      image(4, 4, [
        [0, 1],
        [0, 2],
        [1, 1],
        [1, 2],
      ]),
      4,
      4,
    );
    const sanity = silhouetteSanity(clipped, { minAreaRatio: 0 });
    expect(sanity.passed).toBe(false);
    expect(sanity.issues.join(' ')).toMatch(/left/);
  });

  it('returns resolution-independent comparison measurements', () => {
    const reference = analyseSilhouetteRgba(
      image(10, 10, [
        [4, 4],
        [5, 4],
        [4, 5],
        [5, 5],
      ]),
      10,
      10,
    );
    const candidate = analyseSilhouetteRgba(
      image(10, 10, [
        [5, 4],
        [6, 4],
        [5, 5],
        [6, 5],
      ]),
      10,
      10,
    );
    const comparison = compareSilhouetteMetrics(candidate, reference);

    expect(comparison.areaRatioDelta).toBeCloseTo(0, 8);
    expect(comparison.centroidDistance).toBeCloseTo(0.1, 8);
    expect(comparison.boundsEdgeMaxDelta).toBeCloseTo(0.1, 8);
  });

  it('rejects malformed RGBA buffers', () => {
    expect(() => analyseSilhouetteRgba(new Uint8Array(3), 2, 2)).toThrow(/does not match/);
  });
});
