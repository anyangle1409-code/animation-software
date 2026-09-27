import { describe, expect, it } from 'vitest';
import { EXERCISES } from '../exercises/library';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { canonicalSkeleton, PoseEvaluation } from './skeleton';
import { HgPoseEvaluation, hgCanonicalSkeleton } from './firstPartySkeleton';
import { HgVec3 } from '../core/linearMath';

const EPS = 2e-11;

describe('first-party skeleton parity', () => {
  it('reproduces the current canonical rest skeleton', () => {
    expect(hgCanonicalSkeleton.names).toEqual(canonicalSkeleton.names);
    expect(hgCanonicalSkeleton.bones).toHaveLength(canonicalSkeleton.bones.length);

    for (const current of canonicalSkeleton.bones) {
      const hg = hgCanonicalSkeleton.bone(current.name);
      expect(hg.parent).toBe(current.parent);
      expect(Math.abs(hg.length - current.length), current.name).toBeLessThan(EPS);
      expect(
        hg.restHead.distanceTo(new HgVec3(current.restHead.x, current.restHead.y, current.restHead.z)),
        current.name,
      ).toBeLessThan(EPS);
      expect(
        hg.restTail.distanceTo(new HgVec3(current.restTail.x, current.restTail.y, current.restTail.z)),
        current.name,
      ).toBeLessThan(EPS);

      const restDot = Math.abs(
        hg.restWorldQuaternion.x * current.restWorldQuaternion.x +
        hg.restWorldQuaternion.y * current.restWorldQuaternion.y +
        hg.restWorldQuaternion.z * current.restWorldQuaternion.z +
        hg.restWorldQuaternion.w * current.restWorldQuaternion.w
      );
      expect(Math.abs(1 - restDot), current.name).toBeLessThan(EPS);
    }
  });

  it('reproduces sampled exercise pose matrices across the whole library', () => {
    const current = new PoseEvaluation(canonicalSkeleton);
    const hg = new HgPoseEvaluation(hgCanonicalSkeleton);
    let worst = 0;
    let label = '';

    for (const exercise of EXERCISES) {
      const clip = generateClip(canonicalSkeleton, exercise);
      for (const fraction of [0, 0.17, 0.33, 0.5, 0.71, 1]) {
        const pose = sampleClip(clip, clip.duration * fraction).pose;
        current.apply(pose);
        hg.apply(pose);

        for (const bone of canonicalSkeleton.bones) {
          const a = current.matrix(bone.name).elements;
          const b = hg.matrix(bone.name).elements;
          for (let index = 0; index < 16; index += 1) {
            const delta = Math.abs(a[index] - b[index]);
            if (delta > worst) {
              worst = delta;
              label = `${exercise.id}/${fraction}/${bone.name}/m${index}`;
            }
          }
        }
      }
    }

    expect(worst, label).toBeLessThan(EPS);
  }, 60_000);

  it('reproduces head, tail and quaternion queries', () => {
    const exercise = EXERCISES[0];
    const clip = generateClip(canonicalSkeleton, exercise);
    const pose = sampleClip(clip, clip.duration * 0.43).pose;
    const current = new PoseEvaluation(canonicalSkeleton).apply(pose);
    const hg = new HgPoseEvaluation(hgCanonicalSkeleton).apply(pose);

    for (const bone of canonicalSkeleton.bones) {
      const currentHead = current.head(bone.name);
      const currentTail = current.tail(bone.name);
      const hgHead = hg.head(bone.name);
      const hgTail = hg.tail(bone.name);
      expect(Math.hypot(
        hgHead.x-currentHead.x,
        hgHead.y-currentHead.y,
        hgHead.z-currentHead.z,
      ), `${bone.name} head`).toBeLessThan(EPS);
      expect(Math.hypot(
        hgTail.x-currentTail.x,
        hgTail.y-currentTail.y,
        hgTail.z-currentTail.z,
      ), `${bone.name} tail`).toBeLessThan(EPS);

      const a = current.quaternion(bone.name);
      const b = hg.quaternion(bone.name);
      const dot = Math.abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w);
      expect(Math.abs(1-dot), `${bone.name} quaternion`).toBeLessThan(EPS);
    }
  });
});
