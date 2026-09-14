import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { canonicalSkeleton } from '../rig/skeleton';
import { getExercise } from './library';
import type { GripKind } from './types';

const deg = (radians: number | undefined) => ((radians ?? 0) * 180) / Math.PI;

function poseFor(preset: GripKind) {
  const source = getExercise('dumbbell_bicep_curl');
  const exercise = structuredClone(source);
  exercise.hands.gripPreset = preset;
  return generateClip(canonicalSkeleton, exercise).keyframes[0].pose;
}

describe('equipment-aware grip profiles', () => {
  it('keeps the authored dumbbell curl hand exactly compatible with the original profile', () => {
    const exercise = getExercise('dumbbell_bicep_curl');
    const pose = generateClip(canonicalSkeleton, exercise).keyframes[0].pose;
    expect(deg(pose.rotations.index_01_l?.z)).toBeCloseTo(78 * 0.85, 8);
    expect(deg(pose.rotations.index_02_l?.z)).toBeCloseTo(95 * 0.85, 8);
    expect(deg(pose.rotations.thumb_01_l?.z)).toBeCloseTo(-22 * 0.85, 8);
    expect(deg(pose.rotations.thumb_01_l?.x)).toBeCloseTo(-14 * 0.85, 8);
  });

  it('produces distinct bar, handle and rope hand shapes deterministically', () => {
    const bar = poseFor('bar');
    const handle = poseFor('handle');
    const rope = poseFor('rope');
    expect(deg(bar.rotations.index_01_l?.z)).toBeCloseTo(76 * 0.85, 8);
    expect(deg(handle.rotations.index_01_l?.z)).toBeCloseTo(82 * 0.85, 8);
    expect(deg(rope.rotations.index_01_l?.z)).toBeCloseTo(88 * 0.85, 8);
    expect(deg(rope.rotations.thumb_01_l?.x)).toBeCloseTo(-14 * 0.85, 8);
    expect(deg(rope.rotations.thumb_02_l?.z)).toBeCloseTo(70 * 0.85, 8);
  });

  it('keeps a floor-contact profile almost open at push-up closure', () => {
    const exercise = getExercise('push_up');
    const pose = generateClip(canonicalSkeleton, exercise).keyframes[0].pose;
    expect(Math.abs(deg(pose.rotations.index_01_l?.z))).toBeLessThan(1);
    expect(Math.abs(deg(pose.rotations.index_02_l?.z))).toBeLessThan(1);
  });
});
