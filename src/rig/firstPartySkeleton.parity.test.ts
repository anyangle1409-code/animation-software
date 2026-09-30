import { describe, expect, it } from 'vitest';
import { EXERCISES } from '../exercises/library';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { HgVec3 } from '../core/linearMath';
import { HUMANOID_BONES } from './humanoid';
import { HgPoseEvaluation, HgSkeleton } from './firstPartySkeleton';
import { PoseEvaluation, canonicalSkeleton } from './skeleton';

const EPS = 2e-11;
const hgCanonicalSkeleton = new HgSkeleton(HUMANOID_BONES);

const quaternionNorm = (q: { x: number; y: number; z: number; w: number }) =>
  Math.hypot(q.x, q.y, q.z, q.w);

const quaternionAgreement = (
  a: { x: number; y: number; z: number; w: number },
  b: { x: number; y: number; z: number; w: number },
) => Math.abs(
  a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w,
);

describe('first-party skeleton production invariants', () => {
  it('derives the canonical rest skeleton exactly from authored humanoid geometry', () => {
    const authoredNames = HUMANOID_BONES.map((bone) => bone.name);
    expect(canonicalSkeleton.names).toEqual(authoredNames);
    expect(hgCanonicalSkeleton.names).toEqual(authoredNames);

    for (const definition of HUMANOID_BONES) {
      const current = canonicalSkeleton.bone(definition.name);
      const hg = hgCanonicalSkeleton.bone(definition.name);
      const authoredHead = new HgVec3(
        definition.head.x,
        definition.head.y,
        definition.head.z,
      );
      const authoredTail = new HgVec3(
        definition.tail.x,
        definition.tail.y,
        definition.tail.z,
      );
      const authoredLength = authoredHead.distanceTo(authoredTail);

      for (const candidate of [current, hg]) {
        expect(candidate.parent, definition.name).toBe(definition.parent);
        expect(Math.abs(candidate.length - authoredLength), definition.name)
          .toBeLessThan(EPS);
        expect(candidate.restHead.distanceTo(authoredHead), `${definition.name}/head`)
          .toBeLessThan(EPS);
        expect(candidate.restTail.distanceTo(authoredTail), `${definition.name}/tail`)
          .toBeLessThan(EPS);
        expect(Math.abs(quaternionNorm(candidate.restWorldQuaternion) - 1), `${definition.name}/world-q`)
          .toBeLessThan(EPS);
        expect(Math.abs(quaternionNorm(candidate.restLocalQuaternion) - 1), `${definition.name}/local-q`)
          .toBeLessThan(EPS);

        if (candidate.parent === null) {
          expect(candidate.offset.distanceTo(authoredHead), `${definition.name}/root-offset`)
            .toBeLessThan(EPS);
          expect(candidate.depth).toBe(0);
        } else {
          const parent = hgCanonicalSkeleton.bone(candidate.parent);
          const rebuiltHead = candidate.offset.clone()
            .applyQuaternion(parent.restWorldQuaternion)
            .add(parent.restHead);
          expect(rebuiltHead.distanceTo(authoredHead), `${definition.name}/offset`)
            .toBeLessThan(EPS);
          expect(candidate.depth).toBe(parent.depth + 1);

          const rebuiltWorld = parent.restWorldQuaternion.clone()
            .multiply(candidate.restLocalQuaternion);
          expect(
            Math.abs(1 - quaternionAgreement(rebuiltWorld, candidate.restWorldQuaternion)),
            `${definition.name}/rest-orientation`,
          ).toBeLessThan(EPS);
        }
      }
    }
  });

  it('keeps compatibility and first-party hierarchy queries identical', () => {
    for (const name of canonicalSkeleton.names) {
      expect(canonicalSkeleton.chainToRoot(name).map((bone) => bone.name))
        .toEqual(hgCanonicalSkeleton.chainToRoot(name).map((bone) => bone.name));
      expect(canonicalSkeleton.descendants(name).map((bone) => bone.name))
        .toEqual(hgCanonicalSkeleton.descendants(name).map((bone) => bone.name));
      expect(canonicalSkeleton.jointParent(name)).toBe(hgCanonicalSkeleton.jointParent(name));

      for (const other of canonicalSkeleton.names) {
        expect(canonicalSkeleton.isAncestorOf(name, other))
          .toBe(hgCanonicalSkeleton.isAncestorOf(name, other));
      }
    }
  });

  it('keeps the compatibility evaluator identical across the whole exercise library', () => {
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
          const currentMatrix = current.matrix(bone.name).elements;
          const hgMatrix = hg.matrix(bone.name).elements;
          for (let index = 0; index < 16; index += 1) {
            const delta = Math.abs(currentMatrix[index] - hgMatrix[index]);
            if (delta > worst) {
              worst = delta;
              label = `${exercise.id}/${fraction}/${bone.name}/m${index}`;
            }
          }

          expect(current.head(bone.name).distanceTo(hg.head(bone.name)), `${bone.name}/head`)
            .toBeLessThan(EPS);
          expect(current.tail(bone.name).distanceTo(hg.tail(bone.name)), `${bone.name}/tail`)
            .toBeLessThan(EPS);

          const currentQ = current.quaternion(bone.name);
          const hgQ = hg.quaternion(bone.name);
          expect(
            Math.abs(1 - quaternionAgreement(currentQ, hgQ)),
            `${bone.name}/quaternion`,
          ).toBeLessThan(EPS);
        }
      }
    }

    expect(worst, label).toBeLessThan(EPS);
  }, 60_000);
});
