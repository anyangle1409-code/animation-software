import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { shoulderPress } from '../exercises/definitions/shoulderPress';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { GRIP_CLOSURE_PRESETS, measureGripFit } from './gripDiagnostics';
import { FINGERS } from '../rig/boneNames';

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
        expect(Object.keys(fit.digitReachUse).sort()).toEqual([...FINGERS].sort());
        for (const finger of FINGERS) {
          expect(fit.digitReachUse[finger]).toBeGreaterThanOrEqual(0);
          expect(fit.digitReachUse[finger]).toBeLessThan(1);
        }
        expect(fit.reachUse).toBeCloseTo(Math.max(...Object.values(fit.digitReachUse)), 10);
      }
    }
  });

  it('identifies the digit carrying the largest reach value', () => {
    const exercise = structuredClone(bicepCurl);
    exercise.hands.digitClosure = { pinky: 0.35 };
    const clip = generateClip(skeleton, exercise);
    const evaluation = new PoseEvaluation(skeleton);
    const frame = resolveFrame(skeleton, evaluation, clip, 0);
    evaluation.apply(frame.pose);
    const equipment = frame.equipment.get('dumbbell_l');
    expect(equipment).toBeDefined();
    const fit = measureGripFit(evaluation, equipment!, 'l');
    const largest = FINGERS.reduce((best, finger) =>
      fit.digitReachUse[finger] > fit.digitReachUse[best] ? finger : best,
    );
    expect(fit.reachUse).toBeCloseTo(fit.digitReachUse[largest], 10);
    expect(fit.digitReachUse.pinky).not.toBeCloseTo(fit.digitReachUse.index, 6);
  });

});
