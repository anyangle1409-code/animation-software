import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { getExercise } from '../exercises/library';
import { generateClip } from '../animation/generate';
import { reviewExercise } from './review';

const clone = <T>(value: T): T => structuredClone(value);

describe('exercise review gate', () => {
  it('clears the retained dumbbell curl through measurable automated gates', () => {
    const exercise = getExercise('dumbbell_bicep_curl');
    const clip = generateClip(canonicalSkeleton, exercise);
    const review = reviewExercise(canonicalSkeleton, exercise, clip, 4);
    expect(review.automatedPass).toBe(true);
    expect(review.gates.find((gate) => gate.id === 'grip')?.applicable).toBe(true);
    expect(review.gates.every((gate) => gate.passed)).toBe(true);
  });

  it('blocks approval when a locked arm target is physically impossible', () => {
    const exercise = clone(getExercise('dumbbell_bicep_curl'));
    exercise.locks = [
      ...exercise.locks,
      {
        id: 'impossible_review_target',
        chain: 'arm_l',
        mode: 'world',
        position: { x: -4, y: 4, z: 4 },
        enabled: true,
      },
    ];
    const clip = generateClip(canonicalSkeleton, exercise);
    const review = reviewExercise(canonicalSkeleton, exercise, clip, 3);
    expect(review.automatedPass).toBe(false);
    expect(review.gates.find((gate) => gate.id === 'contacts')?.passed).toBe(false);
    expect(review.gates.find((gate) => gate.id === 'ik')?.passed).toBe(false);
  });
});
