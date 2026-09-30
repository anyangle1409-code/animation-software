import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { airSquat } from '../exercises/definitions/airSquat';
import { EXERCISES } from '../exercises/library';
import { HGPT_CANONICAL_V4_ORIGINAL_BONES } from './canonicalV4Original';
import { HUMANOID_BONES } from './humanoid';
import { Skeleton } from './skeleton';

const v3 = new Skeleton(HUMANOID_BONES);
const v4 = new Skeleton(HGPT_CANONICAL_V4_ORIGINAL_BONES);

const finitePose = (pose: ReturnType<typeof generateClip>['keyframes'][number]['pose']): boolean => {
  for (const rotation of Object.values(pose.rotations)) {
    if (!rotation) continue;
    if (![rotation.x, rotation.y, rotation.z].every(Number.isFinite)) return false;
  }
  if (![pose.rootPosition.x, pose.rootPosition.y, pose.rootPosition.z].every(Number.isFinite)) {
    return false;
  }
  if (![pose.rootRotation.x, pose.rootRotation.y, pose.rootRotation.z].every(Number.isFinite)) {
    return false;
  }
  return true;
};

describe('canonical v4 ORIGINAL shadow runtime compatibility', () => {
  it('keeps the complete v3 bone-name and parent architecture', () => {
    expect(v4.names).toEqual(v3.names);
    for (const name of v3.names) {
      expect(v4.bone(name).parent, name).toBe(v3.bone(name).parent);
    }
  });

  it('generates every exercise with unchanged clip structure and finite poses', () => {
    for (const exercise of EXERCISES) {
      const current = generateClip(v3, exercise);
      const shadow = generateClip(v4, exercise);

      expect(shadow.duration, exercise.id).toBe(current.duration);
      expect(shadow.fps, exercise.id).toBe(current.fps);
      expect(shadow.loop, exercise.id).toBe(current.loop);
      expect(shadow.keyframes.length, exercise.id).toBe(current.keyframes.length);
      expect(shadow.keyframes.map(frame => frame.marker), exercise.id)
        .toEqual(current.keyframes.map(frame => frame.marker));
      expect(shadow.keyframes.map(frame => frame.phaseId), exercise.id)
        .toEqual(current.keyframes.map(frame => frame.phaseId));
      expect(shadow.equipment, exercise.id).toEqual(current.equipment);
      expect(shadow.hands, exercise.id).toEqual(current.hands);
      expect(shadow.locks, exercise.id).toEqual(current.locks);

      for (const frame of shadow.keyframes) {
        expect(finitePose(frame.pose), `${exercise.id} @ ${frame.time}s`).toBe(true);
        for (const name of Object.keys(frame.pose.rotations)) {
          expect(v4.has(name), `${exercise.id}: unknown v4 pose bone ${name}`).toBe(true);
        }
      }
    }
  }, 60_000);

  it('uses each skeleton own hip width and leg span for generated stance', () => {
    const current = generateClip(v3, airSquat);
    const shadow = generateClip(v4, airSquat);

    const v3HalfHip = Math.abs(v3.bone('thigh_l').restHead.x);
    const v3LegSpan = Math.abs(
      v3.bone('thigh_l').restHead.y - v3.bone('shin_l').restTail.y,
    );
    const v4HalfHip = Math.abs(v4.bone('thigh_l').restHead.x);
    const v4LegSpan = Math.abs(
      v4.bone('thigh_l').restHead.y - v4.bone('shin_l').restTail.y,
    );
    const halfStance = airSquat.feet.width / 2;

    const expectedV3 = -Math.atan2(halfStance - v3HalfHip, v3LegSpan);
    const expectedV4 = -Math.atan2(halfStance - v4HalfHip, v4LegSpan);

    expect(v3HalfHip).toBeCloseTo(0.09, 12);
    expect(v3LegSpan).toBeCloseTo(0.84, 12);
    expect(v4HalfHip).toBeCloseTo(0.092, 12);
    expect(v4LegSpan).toBeCloseTo(0.875, 12);

    expect(current.keyframes[0].pose.rotations.thigh_l?.z).toBeCloseTo(expectedV3, 12);
    expect(shadow.keyframes[0].pose.rotations.thigh_l?.z).toBeCloseTo(expectedV4, 12);
    expect(expectedV4).not.toBeCloseTo(expectedV3, 6);
  });
});
