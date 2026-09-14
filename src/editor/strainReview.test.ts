import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { builtinCharacter } from '../character/builtin';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { scanMeshStrainWorstCases } from './strainReview';

const skeleton = canonicalSkeleton;

describe('whole-rep deformation review', () => {
  it('finds finite worst strain frames and restores a bounded diagnostic scan', async () => {
    const character = await builtinCharacter.build(skeleton);
    try {
      const clip = generateClip(skeleton, bicepCurl);
      clip.fps = 4; // Keep the regression cheap; production uses the authored clip FPS.
      const result = scanMeshStrainWorstCases(character, skeleton, clip, true, 1.25, 80);
      expect(result.length).toBeGreaterThan(0);
      for (const item of result) {
        expect(item.sampledEdges).toBeGreaterThan(0);
        for (const metric of [item.p95, item.p99, item.max]) {
          expect(Number.isFinite(metric.value)).toBe(true);
          expect(metric.value).toBeGreaterThanOrEqual(0);
          expect(metric.time).toBeGreaterThanOrEqual(0);
          expect(metric.time).toBeLessThanOrEqual(clip.duration);
        }
      }
    } finally {
      character.dispose();
    }
  });
});
