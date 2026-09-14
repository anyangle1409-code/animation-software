import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { builtinCharacter } from '../character/builtin';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { scanDeformationControlSweep, scanMeshStrainWorstCases } from './strainReview';
import type { DeformationControl } from '../character';

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

  it('sweeps explicit corrective values and restores the original source value', async () => {
    const character = await builtinCharacter.build(skeleton);
    try {
      const clip = generateClip(skeleton, bicepCurl);
      clip.fps = 2;
      let value = 0.37;
      const visited: number[] = [];
      const control: DeformationControl = {
        id: 'testCorrective',
        label: 'Test corrective',
        min: 0,
        max: 1,
        step: 0.25,
        defaultValue: 0,
        get value() {
          return value;
        },
        set(next) {
          value = Math.min(1, Math.max(0, next));
          visited.push(value);
        },
      };

      const result = scanDeformationControlSweep(
        character,
        control,
        skeleton,
        clip,
        true,
        1.25,
        [0, 0.5, 1],
        40,
      );
      expect(result.map((point) => point.value)).toEqual([0, 0.5, 1]);
      expect(visited).toEqual(expect.arrayContaining([0, 0.5, 1, 0.37]));
      expect(control.value).toBeCloseTo(0.37, 8);
      for (const point of result) {
        expect(point.p99).not.toBeNull();
        expect(point.max).not.toBeNull();
        expect(point.p99!.time).toBeGreaterThanOrEqual(0);
        expect(point.p99!.time).toBeLessThanOrEqual(clip.duration);
      }
    } finally {
      character.dispose();
    }
  });

});
