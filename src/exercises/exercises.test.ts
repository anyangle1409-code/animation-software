import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { BoneName } from '../rig/boneNames';
import { generateClip } from '../animation/generate';
import { validateClip } from '../animation/validate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { toDeg } from '../core/math';
import { EXERCISES, getExercise } from './library';
import { repetitionDuration } from './types';

const skeleton = canonicalSkeleton;
const evaluation = new PoseEvaluation(skeleton);

describe.each(EXERCISES.map((exercise) => [exercise.name, exercise.id] as const))(
  '%s',
  (_name, id) => {
    const exercise = getExercise(id);
    const clip = generateClip(skeleton, exercise);
    const validation = validateClip(skeleton, evaluation, exercise, clip, 20);

    it('satisfies every technique rule it defines', () => {
      expect(
        validation.violations.map((violation) => `${violation.ruleId}: ${violation.message}`),
      ).toEqual([]);
    });

    it('reaches every IK target and lock', () => {
      expect(validation.unreachable).toEqual([]);
    });

    it('returns exactly to its opening pose', () => {
      expect(validation.loopClosed).toBe(true);
    });

    it('runs for the duration its tempo describes', () => {
      expect(clip.duration).toBeCloseTo(repetitionDuration(exercise), 6);
    });

    it('keeps every locked contact still for the whole repetition', () => {
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const start = new Map<string, Vector3>();

      for (let index = 0; index <= 40; index += 1) {
        const time = (index / 40) * clip.duration;
        const frame = resolveFrame(skeleton, evaluation, clip, time, { anchors });
        evaluation.apply(frame.pose);

        for (const lock of clip.locks) {
          const side = lock.chain.endsWith('_l') ? 'l' : 'r';
          const bone: BoneName = lock.chain.startsWith('arm')
            ? side === 'l'
              ? 'hand_l'
              : 'hand_r'
            : side === 'l'
              ? 'foot_l'
              : 'foot_r';
          // A foot standing on its ball is held at the ball; its ankle rises.
          const position = lock.onBall ? evaluation.tail(bone, new Vector3()) : evaluation.head(bone, new Vector3());
          const first = start.get(lock.id);
          if (!first) start.set(lock.id, position.clone());
          else expect(position.distanceTo(first), `${lock.id} at ${time.toFixed(2)}s`).toBeLessThan(0.005);
        }
      }
    });

    it('stays inside every joint limit', () => {
      for (let index = 0; index <= 20; index += 1) {
        const time = (index / 20) * clip.duration;
        const frame = resolveFrame(skeleton, evaluation, clip, time);
        for (const [name, rotation] of Object.entries(frame.pose.rotations)) {
          if (!rotation) continue;
          const bone = skeleton.bone(name as never);
          for (const axis of ['x', 'y', 'z'] as const) {
            const limit = bone.definition.limits[axis];
            const degrees = toDeg(rotation[axis]);
            if (!limit) {
              expect(Math.abs(degrees), `${name}.${axis} is a locked axis`).toBeLessThan(1e-6);
            } else {
              expect(degrees, `${name}.${axis} at ${time.toFixed(2)}s`).toBeGreaterThanOrEqual(
                limit.min - 1e-6,
              );
              expect(degrees, `${name}.${axis} at ${time.toFixed(2)}s`).toBeLessThanOrEqual(
                limit.max + 1e-6,
              );
            }
          }
        }
      }
    });

    it('names every muscle and rule it references', () => {
      const ruleIds = new Set(exercise.technique.map((rule) => rule.id));
      for (const error of exercise.commonErrors) {
        if (error.ruleId) expect(ruleIds, error.id).toContain(error.ruleId);
      }
      expect(new Set(exercise.technique.map((rule) => rule.id)).size).toBe(
        exercise.technique.length,
      );
      expect(exercise.muscles.primary.length).toBeGreaterThan(0);
    });
  },
);

describe('exercise library', () => {
  it('gives every exercise a unique id and clip name', () => {
    expect(new Set(EXERCISES.map((exercise) => exercise.id)).size).toBe(EXERCISES.length);
    expect(new Set(EXERCISES.map((exercise) => exercise.clipName)).size).toBe(EXERCISES.length);
    for (const exercise of EXERCISES) {
      expect(exercise.clipName).toMatch(/^[a-z][a-z0-9_]*$/);
    }
  });

  it('covers the three areas the first milestone is meant to prove', () => {
    const ids = EXERCISES.map((exercise) => exercise.id);
    expect(ids).toContain('dumbbell_bicep_curl'); // equipment held in the hands
    expect(ids).toContain('push_up'); // four floor contacts, whole-body constraint
    expect(ids).toContain('air_squat'); // hips, knees, ankles with foot locking
  });
});
