import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { getExercise } from '../exercises/library';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { MUSCLE_GROUP_IDS } from './groups';
import { diagnoseMuscles, muscleLengthState } from './diagnostics';

const skeleton = canonicalSkeleton;
const curl = getExercise('dumbbell_bicep_curl');
const clip = generateClip(skeleton, curl);

function at(time: number) {
  const evaluation = new PoseEvaluation(skeleton);
  const frame = resolveFrame(skeleton, evaluation, clip, time);
  evaluation.apply(frame.pose);
  return diagnoseMuscles(evaluation, curl.muscles);
}

describe('live muscle diagnostics', () => {
  it('reports every trainer-level group and keeps exercise activation separate from length', () => {
    const diagnostics = at(0);
    expect(diagnostics).toHaveLength(MUSCLE_GROUP_IDS.length);

    const biceps = diagnostics.find((entry) => entry.id === 'biceps')!;
    const forearms = diagnostics.find((entry) => entry.id === 'forearm_flexors')!;
    const triceps = diagnostics.find((entry) => entry.id === 'triceps')!;

    expect(biceps.activation).toBe('primary');
    expect(forearms.activation).toBe('secondary');
    expect(triceps.activation).toBe('inactive');
    expect(biceps.readings).toHaveLength(2);
  });

  it('shows the biceps shortening and triceps lengthening through the retained curl', () => {
    const bottom = at(0);
    const top = at(2.5);
    const reading = (entries: ReturnType<typeof at>, group: string) =>
      entries.find((entry) => entry.id === group)!.readings[0];

    expect(reading(top, 'biceps').stretch).toBeLessThan(reading(bottom, 'biceps').stretch);
    expect(reading(top, 'triceps').stretch).toBeGreaterThan(reading(bottom, 'triceps').stretch);
    expect(reading(top, 'biceps').state).toBe('shortened');
  });

  it('keeps left and right readings equal for the symmetrical curl', () => {
    for (const group of at(1.4)) {
      if (group.readings.length !== 2) continue;
      expect(group.readings[0].stretch, group.id).toBeCloseTo(group.readings[1].stretch, 8);
    }
  });

  it('uses a small neutral dead-band rather than labelling numerical noise as contraction', () => {
    expect(muscleLengthState(0.984)).toBe('shortened');
    expect(muscleLengthState(0.99)).toBe('neutral');
    expect(muscleLengthState(1.01)).toBe('neutral');
    expect(muscleLengthState(1.016)).toBe('lengthened');
  });
});
