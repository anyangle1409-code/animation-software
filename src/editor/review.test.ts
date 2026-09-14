import { describe, expect, it } from 'vitest';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { getExercise } from '../exercises/library';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { measureTwoHandFit } from '../equipment/gripDiagnostics';
import { withTwoHandGripWidth } from '../equipment/library';
import type { EquipmentInstance } from '../equipment/types';
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

  it('blocks rigid two-hand equipment until its grip sockets match the authored hands', () => {
    const exercise = clone(getExercise('push_up'));
    const bar: EquipmentInstance = {
      id: 'review_barbell',
      kind: 'barbell',
      position: { x: 0, y: 0, z: 0 },
      rotation: { x: 0, y: 0, z: 0 },
      attachment: {
        mode: 'hands',
        leftSocket: 'grip_l',
        rightSocket: 'grip_r',
        gripOffset: { x: 0, y: 0, z: 0 },
      },
      visible: true,
    };
    exercise.equipment.instances = [...exercise.equipment.instances, bar];

    const rawClip = generateClip(canonicalSkeleton, exercise);
    const rawReview = reviewExercise(canonicalSkeleton, exercise, rawClip, 3);
    const rawGate = rawReview.gates.find((gate) => gate.id === 'twoHandGrip');
    expect(rawGate?.applicable).toBe(true);
    expect(rawGate?.passed).toBe(false);
    expect(rawReview.automatedPass).toBe(false);

    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const frame = resolveFrame(canonicalSkeleton, evaluation, rawClip, 0);
    evaluation.apply(frame.pose);
    const transform = frame.equipment.get(bar.id)!;
    const targetWidth = measureTwoHandFit(evaluation, bar, transform)!.targetSeparation;
    const calibrated = withTwoHandGripWidth(bar, targetWidth);
    exercise.equipment.instances = exercise.equipment.instances.map((instance) =>
      instance.id === bar.id ? calibrated : instance,
    );

    const calibratedClip = generateClip(canonicalSkeleton, exercise);
    const calibratedReview = reviewExercise(canonicalSkeleton, exercise, calibratedClip, 3);
    const calibratedGate = calibratedReview.gates.find((gate) => gate.id === 'twoHandGrip');
    expect(calibratedGate?.passed).toBe(true);
    expect(calibratedReview.automatedPass).toBe(true);
  });

});
