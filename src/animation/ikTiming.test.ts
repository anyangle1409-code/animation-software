import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { generateClip } from './generate';
import { sampleClip } from './clip';
import { forwardLunge } from '../exercises/definitions/forwardLunge';
import { EXERCISES } from '../exercises/library';

/**
 * Per-chain timing for pose-level IK targets (`MovementPhase.ikTiming`): the
 * target waits until `delay`, arrives by `finish`, and with `lift` rises off
 * the straight line by a half sine on the way.
 */
describe('IK target timing', () => {
  const clip = generateClip(canonicalSkeleton, forwardLunge);
  const [start, bottom, drive, end] = clip.keyframes;
  const step = bottom.time - start.time;
  const target = (time: number) => sampleClip(clip, time).ik.leg_l!.target;

  it('is carried from the phase onto its keyframe, and only where a phase sets it', () => {
    expect(start.ikTiming?.leg_l).toEqual({ finish: 0.65, lift: 0.07, easing: 'easeInOut' });
    expect(drive.ikTiming?.leg_l).toEqual({ delay: 0.35, lift: 0.07, easing: 'easeInOut' });
    expect(bottom.ikTiming).toBeUndefined();
    for (const exercise of EXERCISES.filter((entry) => entry.id !== forwardLunge.id)) {
      for (const keyframe of generateClip(canonicalSkeleton, exercise).keyframes) {
        expect('ikTiming' in keyframe, exercise.id).toBe(false);
      }
    }
  });

  it('arrives by finish and holds there', () => {
    const landed = bottom.ik.leg_l!.target;
    for (const fraction of [0.65, 0.8, 0.99]) {
      const at = target(start.time + step * fraction);
      for (const axis of ['x', 'y', 'z'] as const) expect(at[axis]).toBeCloseTo(landed[axis], 12);
    }
  });

  it('lifts by exactly `lift` half way through its own travel, and not at the ends', () => {
    // easeInOut is symmetric, so half way through the travel is half way along it.
    const middle = target(start.time + step * 0.325);
    expect(middle.y).toBeCloseTo(0.08 + 0.07, 12);
    expect(middle.z).toBeCloseTo((start.ik.leg_l!.target.z + bottom.ik.leg_l!.target.z) / 2, 12);
    expect(target(start.time).y).toBeCloseTo(0.08, 12);
  });

  it('waits until delay', () => {
    const planted = bottom.ik.leg_l!.target;
    const span = end.time - drive.time;
    for (const fraction of [0, 0.2, 0.35]) {
      const at = target(drive.time + span * fraction);
      for (const axis of ['x', 'y', 'z'] as const) expect(at[axis]).toBeCloseTo(planted[axis], 12);
    }
    expect(target(drive.time + span * 0.5).z).toBeLessThan(planted.z);
  });

  it('carries the aim’s forward through the blend, so the foot cannot roll', () => {
    const aim = sampleClip(clip, start.time + step * 0.3).ik.leg_l!.aim!;
    expect(aim.forward).toBeDefined();
  });
});
