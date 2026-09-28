import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { MUSCLES, createMuscleTransform, resolveMuscle } from '../muscles/model';
import { restPose } from '../rig/pose';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { captureMuscleFrame } from './muscleFrameSnapshot';

describe('muscle frame snapshot', () => {
  it('captures every overlay muscle as finite copied numeric data', () => {
    const evaluation = new PoseEvaluation(canonicalSkeleton).apply(restPose());
    const snapshot = captureMuscleFrame(evaluation);
    expect(snapshot.size).toBe(MUSCLES.length);

    for (const value of snapshot.values()) {
      expect([...value.position, ...value.quaternion, ...value.scale, value.stretch].every(Number.isFinite)).toBe(true);
      expect(value.scale.every((axis) => axis > 0)).toBe(true);
      const q = value.quaternion;
      expect(Math.hypot(q[0], q[1], q[2], q[3])).toBeCloseTo(1, 8);
    }
  });

  it('matches the existing muscle resolver for a real muscle', () => {
    const evaluation = new PoseEvaluation(canonicalSkeleton).apply(restPose());
    const muscle = MUSCLES.find((entry) => entry.id === 'biceps_l')!;
    const direct = resolveMuscle(evaluation, muscle, createMuscleTransform());
    const copied = captureMuscleFrame(evaluation, [muscle]).get(muscle.id)!;

    expect(copied.position).toEqual([direct.position.x, direct.position.y, direct.position.z]);
    expect(copied.quaternion).toEqual([
      direct.quaternion.x,
      direct.quaternion.y,
      direct.quaternion.z,
      direct.quaternion.w,
    ]);
    expect(copied.scale).toEqual([direct.scale.x, direct.scale.y, direct.scale.z]);
    expect(copied.stretch).toBe(direct.stretch);
  });

  it('keeps an earlier snapshot independent when the evaluation advances to another real curl frame', () => {
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    resolveFrame(canonicalSkeleton, evaluation, clip, 0);
    const first = captureMuscleFrame(evaluation);
    const before = first.get('biceps_l')!;

    resolveFrame(canonicalSkeleton, evaluation, clip, clip.duration / 2);
    const second = captureMuscleFrame(evaluation);

    expect(first.get('biceps_l')).toEqual(before);
    expect(second.get('biceps_l')).not.toBe(first.get('biceps_l'));
  });
});
