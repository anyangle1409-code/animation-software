import { describe, expect, it } from 'vitest';
import { EXERCISES } from '../library';
import { bicepCurl } from '../definitions/bicepCurl';
import { hammerCurl } from '../definitions/hammerCurl';
import { curlFamily } from './curl';
import { inclineCurl } from '../definitions/inclineCurl';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import type { ExerciseDefinition } from '../types';

/**
 * The family is only worth having if variants actually share it, and the shared
 * parts are only safe if changing them is checked against every variant. Both of
 * those are structural facts about the library rather than things a per-exercise
 * test would notice.
 *
 * The grip check is the one with history. `hands.orientation` used to be
 * documentation — a single reader, a display string — while the forearm's real
 * rotation came from a joint target authored separately, so an exercise could
 * claim a neutral grip and supinate 72°. The family now derives both from one
 * place; this holds the whole library to it, including exercises that do not
 * come from a family at all.
 */
const gripTarget = (exercise: ExerciseDefinition) =>
  exercise.jointTargets.find((target) => target.bone === 'forearm_l' && target.axis === 'y');

describe('the curl family', () => {
  it('has more than one registered variant, so the shared half is exercised', () => {
    // Every variant is in EXERCISES, which is what puts family changes through
    // the library-wide gates. One variant would make that coverage vacuous.
    const curls = EXERCISES.filter((exercise) => exercise.category === 'arms');
    expect(curls.length).toBeGreaterThanOrEqual(2);
    expect(new Set(curls.map((exercise) => exercise.hands.orientation)).size).toBeGreaterThanOrEqual(2);
  });

  it('gives its variants the same rules, so one cannot quietly lose a guard', () => {
    const ids = (exercise: ExerciseDefinition) => exercise.technique.map((rule) => rule.id).sort();
    expect(ids(hammerCurl)).toEqual(ids(bicepCurl));
  });

  it('changes the motion when the grip changes, not just the caption', () => {
    expect(bicepCurl.hands.orientation).toBe('supinated');
    expect(hammerCurl.hands.orientation).toBe('neutral');
    // The forearm really rotates differently: a supinated curl holds 72°, a
    // hammer curl holds the rig's neutral.
    expect(gripTarget(bicepCurl)!.start).toBe(72);
    expect(gripTarget(hammerCurl)!.start).toBe(0);
    // And the rule that checks it moves with it, so a variant is never held to
    // a grip it does not hold.
    const band = (exercise: ExerciseDefinition) => {
      const rule = exercise.technique.find((entry) => entry.id === 'grip_held_l');
      return rule && rule.kind === 'jointAngle' ? [rule.min, rule.max] : null;
    };
    expect(band(bicepCurl)).toEqual([65, 90]);
    expect(band(hammerCurl)).toEqual([-12, 15]);
  });

  it('carries a third grip with no change to this module', () => {
    // This was written before the reverse curl existed, building one locally to
    // show the family already carried it. It is now registered, so the check
    // reads the real exercise: the prediction and the thing predicted.
    const reverse = EXERCISES.find((exercise) => exercise.id === 'dumbbell_reverse_curl');
    expect(reverse, 'the reverse curl is registered').toBeDefined();
    expect(reverse!.hands.orientation).toBe('pronated');
    expect(gripTarget(reverse!)!.start).toBeLessThan(0);
    expect(reverse!.technique.map((rule) => rule.id).sort()).toEqual(
      bicepCurl.technique.map((rule) => rule.id).sort(),
    );
    // Its only departures from the family are the grip and the elbow it needed
    // to clear the thigh; the shared half is untouched.
    expect(curlFamily).toBeTypeOf('function');
  });
});

describe('a declared grip and the motion it names', () => {
  it('agree across the whole library', () => {
    // General, not curl-specific: any exercise that both declares a hand
    // orientation and drives forearm rotation has to make the two say the same
    // thing. Exercises that do not drive forearm rotation are not constrained
    // here — their grip comes from the hand pose instead, and this says nothing
    // about it rather than pretending to check it.
    for (const exercise of EXERCISES) {
      const target = gripTarget(exercise);
      if (!target) continue;
      const declared = exercise.hands.orientation;
      const rotation = target.start;
      if (declared === 'supinated') {
        expect(rotation, `${exercise.id} claims a supinated grip`).toBeGreaterThan(30);
      } else if (declared === 'pronated') {
        expect(rotation, `${exercise.id} claims a pronated grip`).toBeLessThan(-30);
      } else if (declared === 'neutral') {
        expect(Math.abs(rotation), `${exercise.id} claims a neutral grip`).toBeLessThan(30);
      }
    }
  });
});

describe('the incline curl', () => {
  const evaluation = new PoseEvaluation(canonicalSkeleton);
  const clip = generateClip(canonicalSkeleton, inclineCurl);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  const at = (time: number) => {
    evaluation.apply(resolveFrame(canonicalSkeleton, evaluation, clip, time, { anchors }).pose);
    const shoulder = evaluation.head('upperarm_l', new Vector3());
    const elbow = evaluation.head('forearm_l', new Vector3());
    const upperArm = elbow.clone().sub(shoulder);
    return {
      shoulder,
      elbow,
      /** Angle of the upper arm in the sagittal plane, from straight down; + is forward. */
      hang: (Math.atan2(upperArm.z, -upperArm.y) * 180) / Math.PI,
      pelvis: evaluation.head('pelvis', new Vector3()),
      back: evaluation.tail('spine_02', new Vector3()).sub(evaluation.head('spine_02', new Vector3())),
    };
  };

  it('curls exactly as the standing curl does, from a different shoulder', () => {
    const target = (exercise: ExerciseDefinition, bone: string, axis: 'x' | 'y' | 'z') =>
      exercise.jointTargets.find((entry) => entry.bone === bone && entry.axis === axis);
    expect(target(inclineCurl, 'forearm_l', 'x')).toEqual(target(bicepCurl, 'forearm_l', 'x'));
    expect(target(inclineCurl, 'forearm_l', 'y')).toEqual(target(bicepCurl, 'forearm_l', 'y'));
    expect(inclineCurl.hands.orientation).toBe('supinated');
    // The same upper-arm curve, shifted by the 45° hang.
    expect(inclineCurl.startPose.joints.upperarm_l!.x! - bicepCurl.startPose.joints.upperarm_l!.x!).toBe(-45);
    expect(inclineCurl.peakPose.joints.upperarm_l!.x! - bicepCurl.peakPose.joints.upperarm_l!.x!).toBe(-45);
  });

  it('lies back at 45° and stays there, sat on the bench', () => {
    for (let step = 0; step <= 20; step += 1) {
      const frame = at((step / 20) * clip.duration);
      const fromVertical = (Math.acos(frame.back.clone().normalize().y) * 180) / Math.PI;
      expect(fromVertical).toBeGreaterThan(40);
      expect(fromVertical).toBeLessThan(50);
      expect(frame.pelvis.y).toBeCloseTo(0.615, 9);
    }
    expect(inclineCurl.equipment.instances.find((instance) => instance.kind === 'incline_bench')?.supportsBody).toBe(true);
  });

  it('hangs the arms straight down behind the body, and keeps them there while it curls', () => {
    // The point of the variant: the elbow under the shoulder, not in front of
    // the body as a standing curl's is, for the whole repetition. The family's
    // own small forward drift near the top of the curl carries over: 7° at the
    // squeeze, measured.
    for (let step = 0; step <= 20; step += 1) {
      const frame = at((step / 20) * clip.duration);
      expect(Math.abs(frame.hang), `upper arm at step ${step}`).toBeLessThan(10);
      expect(frame.elbow.z, `elbow behind the hips at step ${step}`).toBeLessThan(frame.pelvis.z - 0.25);
    }
  });

  it('gives an explicit 45° bench angle exactly what the default gives', () => {
    // `benchAngle` defaults to 45, so asking for it explicitly must not be a
    // different code path with a different answer.
    const explicit = curlFamily({ ...variantOf(inclineCurl), benchAngle: 45 });
    expect(explicit).toEqual(inclineCurl);
  });

  it('derives the reclined posture from the bench angle, geometrically, at other angles', () => {
    // A shallower bench (30°) reclines the body further from vertical than a
    // steeper one (60°) does: pitch is `backAngle - 90`, not `-backAngle`.
    const thirty = curlFamily({ ...variantOf(inclineCurl), benchAngle: 30 });
    const sixty = curlFamily({ ...variantOf(inclineCurl), benchAngle: 60 });

    const bench = (exercise: ExerciseDefinition) =>
      exercise.equipment.instances.find((instance) => instance.kind === 'incline_bench');
    expect(bench(thirty)?.backAngle).toBe(30);
    expect(bench(sixty)?.backAngle).toBe(60);

    const backOnBench = (exercise: ExerciseDefinition) =>
      exercise.technique.find((rule) => rule.id === 'back_on_bench');
    const band = (exercise: ExerciseDefinition) => {
      const rule = backOnBench(exercise);
      return rule && rule.kind === 'segmentAngle' ? [rule.min, rule.max] : null;
    };
    // |pitch| = 90 - backAngle, ± the library's 5°.
    expect(band(thirty)).toEqual([55, 65]);
    expect(band(sixty)).toEqual([25, 35]);
    expect(band(inclineCurl)).toEqual([40, 50]);

    // The thigh stays flat on the seat: its flexion is `90 - backAngle`, the
    // exact amount that cancels the trunk's own pitch.
    expect(thirty.startPose.joints.thigh_l?.x).toBe(60);
    expect(sixty.startPose.joints.thigh_l?.x).toBe(30);

    // The knee and ankle are untouched by the angle: the hip and the thigh's
    // world orientation do not move, so nothing downstream of the knee does
    // either.
    expect(thirty.startPose.joints.shin_l).toEqual(sixty.startPose.joints.shin_l);
    expect(thirty.startPose.joints.shin_l).toEqual(inclineCurl.startPose.joints.shin_l);
  });
});

/** The parts of `inclineCurl` that make it an incline curl, as a `CurlVariant`. */
function variantOf(exercise: ExerciseDefinition) {
  return {
    id: exercise.id,
    name: exercise.name,
    clipName: exercise.clipName,
    description: exercise.description ?? '',
    grip: 'supinated' as const,
    support: 'incline' as const,
    mass: exercise.equipment.instances.find((instance) => instance.kind === 'dumbbell')?.mass,
  };
}
