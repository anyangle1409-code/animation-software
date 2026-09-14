import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { shoulderPress } from '../exercises/definitions/shoulderPress';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { GRIP_CLOSURE_PRESETS, measureGripFit } from './gripDiagnostics';

const skeleton = canonicalSkeleton;

describe('grip authoring diagnostics', () => {
  it('provides ordered closure presets with the authored curl default represented', () => {
    expect(GRIP_CLOSURE_PRESETS.map((preset) => preset.closure)).toEqual([0.7, 0.85, 1]);
    expect(GRIP_CLOSURE_PRESETS.some((preset) => preset.closure === bicepCurl.hands.closure)).toBe(true);
  });

  it.each([
    ['curl', bicepCurl],
    ['shoulder press', shoulderPress],
  ])('keeps %s inside the measurable grip envelope through the full rep', (_label, exercise) => {
    const clip = generateClip(skeleton, exercise);
    const evaluation = new PoseEvaluation(skeleton);
    for (let index = 0; index <= 12; index += 1) {
      const time = (index / 12) * clip.duration;
      const frame = resolveFrame(skeleton, evaluation, clip, time);
      evaluation.apply(frame.pose);
      for (const side of ['l', 'r'] as const) {
        const equipment = frame.equipment.get(`dumbbell_${side}`);
        expect(equipment).toBeDefined();
        const fit = measureGripFit(evaluation, equipment!, side);
        expect(fit.withinEnvelope, `${side} at ${time.toFixed(2)}s`).toBe(true);
        expect(fit.reachUse).toBeLessThan(1);
        expect(fit.wrapCoverageDeg).toBeGreaterThan(190);
      }
    }
  });
});
