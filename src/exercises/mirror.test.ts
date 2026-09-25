import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { restPose } from '../rig/pose';
import { resolvePoint } from '../constraints/points';
import { lockAnchors } from '../constraints/locks';
import type { TechniqueRule } from '../constraints/types';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { sampleClip } from '../animation/clip';
import { EXERCISES } from './library';
import {
  bilateralRule,
  mirrorBoneName,
  mirrorJointTarget,
  mirrorLock,
  mirrorRule,
} from './mirror';

/**
 * What is checked here, and what stopped being checkable.
 *
 * These primitives were written against 30 hand-authored mirror pairs and had
 * to reproduce every one of them exactly. That was a real test — the pairs were
 * written by someone reasoning about each exercise, not about a general rule —
 * and it earned its keep immediately, catching a `-0` that structural equality
 * treats as a difference and a dropped equipment `socket` that would have
 * pointed both hands at the same end of the pull-up bar.
 *
 * It cannot stay a test. Those right-hand halves are now derived, so asserting
 * that the derivation reproduces them only asserts that a function equals
 * itself. The ground truth was spent when it was used, which is the honest
 * shape of this kind of migration, and pretending otherwise would leave a
 * green test guarding nothing.
 *
 * What replaces it is stronger and does not decay: the *resolved motion* of
 * every exercise must be its own mirror. That runs through FK, the IK solver,
 * the contact locks and the equipment attachment, none of which the mirroring
 * code can see, so a sign error anywhere in it moves a limb and fails here. The
 * measured departure is 0.0000 mm for all five exercises, over every bone of
 * every frame.
 *
 * Alongside it: the convention is its own inverse, the bone-local reflection
 * claim is measured against the rest skeleton rather than asserted, and the two
 * authoring mistakes the helpers are meant to refuse are exercised.
 */
const skeleton = canonicalSkeleton;

/**
 * Mirror symmetry is exact, so this is a float-noise guard rather than a
 * tolerance. A micron is roughly a thousandth of the tightest real threshold in
 * the suite, the 5 mm contact drift limit.
 */
const EXACT = 1e-6;

/** Strip ids and labels: those are checked separately and would mask a body difference. */
const body = <T extends { id?: string; label?: string }>(value: T): Omit<T, 'id' | 'label'> => {
  const { id: _id, label: _label, ...rest } = value;
  return rest;
};

const pairsOf = <T extends { id: string }>(items: T[]): [T, T][] => {
  const byId = new Map(items.map((item) => [item.id, item]));
  const pairs: [T, T][] = [];
  for (const item of items) {
    if (!item.id.endsWith('_l')) continue;
    const twin = byId.get(`${item.id.slice(0, -2)}_r`);
    if (twin) pairs.push([item, twin]);
  }
  return pairs;
};

/**
 * Exercises whose two sides are meant to differ — a split stance puts one foot
 * forward and the other back; a Pallof press stacks one hand above the other on
 * a cable from one side; a Russian twist turns the trunk to one side and then
 * the other; a woodchop pulls from a pulley on one side down to the other; a
 * forward lunge steps with one foot; a walk has one foot ahead at every moment
 * — and so are not their own mirror. Listed rather than
 * detected, so an exercise cannot drop out of the symmetry check by accident;
 * the test below holds each to actually being asymmetric.
 */
const ASYMMETRIC = new Set(['split_squat', 'cable_pallof_press', 'russian_twist', 'cable_woodchop', 'forward_lunge', 'farmers_walk']);

describe('mirroring', () => {
  it('lists as asymmetric only exercises whose sides really differ', () => {
    for (const id of ASYMMETRIC) {
      const exercise = EXERCISES.find((entry) => entry.id === id)!;
      const left = exercise.locks.find((lock) => lock.id === 'foot_l');
      const right = exercise.locks.find((lock) => lock.id === 'foot_r');
      // One foot locked and the other not — a foot that steps — differs too.
      const legsDiffer =
        (left === undefined) !== (right === undefined) ||
        (left !== undefined && JSON.stringify(mirrorLock(left)) !== JSON.stringify(right));
      // Or the hands: an arm target that is not the other's mirror image.
      const handsDiffer = [exercise.startPose, exercise.peakPose].some((pose) => {
        const upper = pose.ik?.arm_l?.target;
        const lower = pose.ik?.arm_r?.target;
        return Boolean(upper && lower) && (Math.abs(upper!.x + lower!.x) > 1e-6 || upper!.y !== lower!.y || upper!.z !== lower!.z);
      });
      // Or the trunk: a keyframe turned to one side.
      const trunkTurns = [exercise.startPose, exercise.peakPose].some((pose) =>
        (['pelvis', 'spine_01', 'spine_02', 'spine_03'] as const).some((bone) => (pose.joints[bone]?.y ?? 0) !== 0),
      );
      expect(legsDiffer || handsDiffer || trunkTurns, id).toBe(true);
    }
  });

  describe('the derived half agrees with the body it drives', () => {
    for (const exercise of EXERCISES.filter((entry) => !ASYMMETRIC.has(entry.id))) {
      it(`${exercise.name} resolves to its own mirror`, () => {
        const evaluation = new PoseEvaluation(skeleton);
        const clip = generateClip(skeleton, exercise);
        const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
        const left = new Vector3();
        const right = new Vector3();
        let worst = 0;
        let where = '';
        for (let step = 0; step <= 40; step += 1) {
          const time = (step / 40) * clip.duration;
          evaluation.apply(resolveFrame(skeleton, evaluation, clip, time, { anchors }).pose);
          for (const bone of skeleton.bones) {
            if (!bone.name.endsWith('_l')) continue;
            evaluation.head(bone.name, left);
            evaluation.head(mirrorBoneName(bone.name), right);
            // Reflect the right-hand bone and it should land on the left one.
            right.x = -right.x;
            const apart = left.distanceTo(right);
            if (apart > worst) {
              worst = apart;
              where = `${bone.name} at ${time.toFixed(2)}s, ${(apart * 1000).toFixed(4)} mm apart`;
            }
          }
        }
        expect(worst, where).toBeLessThan(EXACT);
      });
    }

    it('still has pairs to derive, so the checks above mean something', () => {
      // If an exercise were un-migrated back to hand-written twins the symmetry
      // test would keep passing while testing nothing about this module. This
      // is what notices.
      let derived = 0;
      for (const exercise of EXERCISES) derived += pairsOf(exercise.technique).length;
      expect(derived, 'mirrored technique-rule pairs across the library').toBeGreaterThanOrEqual(27);
    });

    it('gives every sided rule a twin', () => {
      // A rule that names one side and not the other is almost always a
      // half-finished edit rather than a deliberate asymmetry.
      for (const exercise of EXERCISES) {
        const ids = new Set(exercise.technique.map((rule) => rule.id));
        for (const rule of exercise.technique) {
          if (!/_[lr]$/.test(rule.id)) continue;
          expect(ids, `${exercise.id}: ${rule.id} has no twin`).toContain(mirrorRule(rule).id);
        }
      }
    });
  });

  describe('the convention itself', () => {
    it('is its own inverse', () => {
      for (const exercise of EXERCISES) {
        for (const rule of exercise.technique) {
          expect(mirrorRule(mirrorRule(rule)), rule.id).toEqual(rule);
        }
        for (const target of exercise.jointTargets) {
          expect(mirrorJointTarget(mirrorJointTarget(target)), target.bone).toEqual(target);
        }
        for (const lock of exercise.locks) {
          expect(mirrorLock(mirrorLock(lock)), lock.id).toEqual(lock);
        }
      }
    });

    it('leaves centre-line bones on the centre line', () => {
      for (const bone of ['root', 'pelvis', 'spine_01', 'spine_03', 'neck', 'head'] as const) {
        expect(mirrorBoneName(bone)).toBe(bone);
      }
    });

    it('puts a mirrored point where the reflection of the original is', () => {
      // The claim underneath `mirrorPoint`: a bone-local offset reflects in x
      // alone. Checked against the rest skeleton rather than asserted, for every
      // sided point any rule in the library actually names.
      const evaluation = new PoseEvaluation(skeleton).apply(restPose());
      const here = new Vector3();
      const there = new Vector3();
      let checked = 0;
      for (const exercise of EXERCISES) {
        for (const rule of exercise.technique) {
          for (const point of pointsOf(rule)) {
            if (!point.bone.endsWith('_l')) continue;
            resolvePoint(evaluation, point, here);
            resolvePoint(evaluation, { ...point, bone: mirrorBoneName(point.bone) }, there);
            expect(there.x, `${rule.id} ${point.bone}`).toBeCloseTo(-here.x, 6);
            expect(there.y, `${rule.id} ${point.bone}`).toBeCloseTo(here.y, 6);
            expect(there.z, `${rule.id} ${point.bone}`).toBeCloseTo(here.z, 6);
            checked += 1;
          }
        }
      }
      expect(checked, 'sided points checked').toBeGreaterThan(10);
    });

    it('refuses a rule that names no sided bone', () => {
      expect(() =>
        bilateralRule({
          kind: 'jointAngle',
          id: 'torso_upright_l',
          label: 'Torso stays upright',
          bone: 'spine_02',
          axis: 'x',
          max: 10,
        }),
      ).toThrow(/names no sided bone/);
    });

    it('refuses to pair a symmetry rule, which already spans both sides', () => {
      expect(() =>
        bilateralRule({
          kind: 'symmetry',
          id: 'even_press_l',
          label: 'Both sides press evenly',
          left: { bone: 'forearm_l' },
          right: { bone: 'forearm_r' },
          tolerance: 0.02,
        }),
      ).toThrow(/already spans both sides/);
    });

    it('keeps a one-sided range one-sided, on the other side', () => {
      const rule: TechniqueRule = {
        kind: 'relativePosition',
        id: 'elbow_l',
        label: 'Left elbow',
        point: { bone: 'forearm_l' },
        relativeTo: { bone: 'spine_03' },
        axis: 'x',
        max: -0.13,
      };
      const mirrored = mirrorRule(rule);
      expect(body(mirrored)).toEqual({
        kind: 'relativePosition',
        point: { bone: 'forearm_r' },
        relativeTo: { bone: 'spine_03' },
        axis: 'x',
        min: 0.13,
      });
      expect('max' in mirrored, 'the open side stays open').toBe(false);
    });
  });
});

function pointsOf(rule: TechniqueRule) {
  switch (rule.kind) {
    case 'stationary':
      return [rule.point];
    case 'distance':
      return [rule.from, rule.to];
    case 'relativePosition':
      return [rule.point, rule.relativeTo];
    case 'symmetry':
      return [rule.left, rule.right];
    case 'alignment':
      return rule.points;
    default:
      return [];
  }
}
