import { describe, expect, it } from 'vitest';
import { EXERCISES } from '../exercises/library';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { HgPoseEvaluation, hgCanonicalSkeleton } from '../rig/firstPartySkeleton';
import { HgVec3 } from '../core/linearMath';
import {
  hingeRotationForDirection,
  restWorldQuaternion,
  swingFor,
} from './orient';
import {
  hgHingeRotationForDirection,
  hgRestWorldQuaternion,
  hgSwingFor,
} from './firstPartyOrient';

const EPS = 2e-11;

function expectRotation(
  actual: { x: number; y: number; z: number },
  expected: { x: number; y: number; z: number },
  label: string,
) {
  expect(Math.abs(actual.x - expected.x), `${label}.x`).toBeLessThan(EPS);
  expect(Math.abs(actual.y - expected.y), `${label}.y`).toBeLessThan(EPS);
  expect(Math.abs(actual.z - expected.z), `${label}.z`).toBeLessThan(EPS);
}

describe('first-party IK orientation parity', () => {
  it('exposes the live first-party FK orientation after each pose update', () => {
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const clip = generateClip(canonicalSkeleton, EXERCISES[0]);
    for (const fraction of [0.12, 0.76, 0.34]) {
      const pose = sampleClip(clip, clip.duration * fraction).pose;
      evaluation.apply(pose);
      expect(evaluation.firstPartyEvaluation).toBeInstanceOf(HgPoseEvaluation);
      for (const name of ['upperarm_l', 'forearm_l', 'thigh_r', 'shin_r'] as const) {
        const expected = restWorldQuaternion(canonicalSkeleton, evaluation, name);
        const actual = hgRestWorldQuaternion(
          canonicalSkeleton.firstParty,
          evaluation.firstPartyEvaluation,
          name,
        );
        expectRotation(actual, expected, `${fraction}/${name}`);
        expect(Math.abs(actual.w - expected.w)).toBeLessThan(EPS);
      }
    }
  });

  it('matches rest-world quaternions through representative exercise poses', () => {
    for (const exercise of EXERCISES.slice(0, 8)) {
      const clip = generateClip(canonicalSkeleton, exercise);
      for (const fraction of [0, 0.31, 0.67, 1]) {
        const pose = sampleClip(clip, clip.duration * fraction).pose;
        const current = new PoseEvaluation(canonicalSkeleton).apply(pose);
        const hg = new HgPoseEvaluation(hgCanonicalSkeleton).apply(pose);

        for (const bone of canonicalSkeleton.bones) {
          const a = restWorldQuaternion(canonicalSkeleton, current, bone.name);
          const b = hgRestWorldQuaternion(hgCanonicalSkeleton, hg, bone.name);
          const dot = Math.abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w);
          expect(Math.abs(1-dot), `${exercise.id}/${bone.name}`).toBeLessThan(EPS);
        }
      }
    }
  });

  it('matches analytic swing solving', () => {
    const directions = [
      [0.25, 0.9, 0.15],
      [-0.4, 0.7, 0.35],
      [0.1, -0.8, 0.5],
    ] as const;
    const bones = ['upperarm_l', 'upperarm_r', 'thigh_l', 'thigh_r'] as const;

    const clip = generateClip(canonicalSkeleton, EXERCISES[0]);
    const pose = sampleClip(clip, clip.duration * 0.43).pose;
    const current = new PoseEvaluation(canonicalSkeleton).apply(pose);
    const hg = new HgPoseEvaluation(hgCanonicalSkeleton).apply(pose);

    for (const bone of bones) {
      for (const [x, y, z] of directions) {
        const a = swingFor(
          canonicalSkeleton,
          current,
          bone,
          new HgVec3(x, y, z),
          0.17,
        );
        const b = hgSwingFor(
          hgCanonicalSkeleton,
          hg,
          bone,
          new HgVec3(x, y, z),
          0.17,
        );
        expectRotation(b, a, `${bone}/swing`);
      }
    }
  });

  it('matches elbow and knee hinge solving', () => {
    const directions = [
      [0.15, -0.9, 0.2],
      [-0.2, -0.7, 0.5],
      [0.3, -0.85, -0.1],
    ] as const;
    const bones = ['forearm_l', 'forearm_r', 'shin_l', 'shin_r'] as const;

    const clip = generateClip(canonicalSkeleton, EXERCISES[0]);
    const pose = sampleClip(clip, clip.duration * 0.28).pose;
    const current = new PoseEvaluation(canonicalSkeleton).apply(pose);
    const hg = new HgPoseEvaluation(hgCanonicalSkeleton).apply(pose);

    for (const bone of bones) {
      for (const [x, y, z] of directions) {
        const a = hingeRotationForDirection(
          canonicalSkeleton,
          current,
          bone,
          new HgVec3(x, y, z),
        );
        const b = hgHingeRotationForDirection(
          hgCanonicalSkeleton,
          hg,
          bone,
          new HgVec3(x, y, z),
        );
        expectRotation(b, a, `${bone}/hinge`);
      }
    }
  });
});
