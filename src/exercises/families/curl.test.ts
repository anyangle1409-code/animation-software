import { describe, expect, it } from 'vitest';
import { EXERCISES } from '../library';
import { bicepCurl } from '../definitions/bicepCurl';
import { hammerCurl } from '../definitions/hammerCurl';
import { curlFamily } from './curl';
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
