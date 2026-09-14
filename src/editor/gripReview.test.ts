import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { FINGERS } from '../rig/boneNames';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { measureGripFit } from '../equipment/gripDiagnostics';
import { scanGripWorstCases } from './gripReview';

const skeleton = canonicalSkeleton;

describe('whole-rep grip review', () => {
  it('records each digit worst point at an authored animation frame', () => {
    const clip = generateClip(skeleton, bicepCurl);
    const sweeps = scanGripWorstCases(skeleton, clip);

    expect(sweeps).toHaveLength(2);
    for (const sweep of sweeps) {
      expect(sweep.overall.time).toBeGreaterThanOrEqual(0);
      expect(sweep.overall.time).toBeLessThanOrEqual(clip.duration);
      expect(Math.abs(sweep.overall.time * clip.fps - Math.round(sweep.overall.time * clip.fps))).toBeLessThan(1e-8);

      const evaluation = new PoseEvaluation(skeleton);
      for (const finger of FINGERS) {
        const worst = sweep.digits[finger];
        expect(worst.reachUse).toBeGreaterThan(0);
        expect(worst.time).toBeGreaterThanOrEqual(0);
        expect(worst.time).toBeLessThanOrEqual(clip.duration);

        const frame = resolveFrame(skeleton, evaluation, clip, worst.time);
        evaluation.apply(frame.pose);
        const transform = frame.equipment.get(sweep.instanceId);
        expect(transform).toBeDefined();
        const fit = measureGripFit(evaluation, transform!, sweep.side);
        expect(fit.digitReachUse[finger]).toBeCloseTo(worst.reachUse, 10);
      }

      expect(sweep.overall.reachUse).toBeCloseTo(
        Math.max(...FINGERS.map((finger) => sweep.digits[finger].reachUse)),
        10,
      );
    }
  });
});
