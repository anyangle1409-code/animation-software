import { describe, expect, it } from 'vitest';
import { EXERCISES } from '../library';
import { shoulderPress } from '../definitions/shoulderPress';
import { bicepCurl } from '../definitions/bicepCurl';
import { pressFamily } from './press';

/**
 * The press family exists to answer one question: was the pattern in
 * `families/curl.ts` a pattern, or a curl-shaped coincidence?
 *
 * What it had to absorb that a curl never needed is rules scoped to phases. A
 * press checks the same joint against opposite bounds at different moments — the
 * elbow must bend past 85° at the rack and lock out overhead — and a builder
 * that could not express that would have been a curl builder wearing a general
 * name.
 *
 * **It has one registered variant, and that is a real limitation, not an
 * oversight.** With one caller, a change to the shared half is checked against
 * the exercise it was made for and nothing else — the same vacuum the curl
 * family's variant-count test exists to prevent. A neutral-grip press was built
 * as the second and withdrawn: measured against the curls, whose grips are
 * known, reaching a true palms-facing position needed roughly 80–85° of forearm
 * supination, which is the joint's own limit, and shoulder rotation barely moved
 * it. That is a modelling gap rather than a tuning problem, and shipping an
 * exercise built on a guess would have been worse than shipping one variant.
 */
describe('the press family', () => {
  it('scopes rules to phases, which is what a curl never needed', () => {
    const phased = shoulderPress.technique.filter((rule) => rule.phases?.length);
    expect(phased.length, 'phase-scoped rules').toBeGreaterThan(0);
    // The same joint, opposite bounds, different moments.
    const bottom = phased.find((rule) => rule.id === 'bottom_depth');
    const lockout = phased.find((rule) => rule.id === 'lockout_l');
    expect(bottom && bottom.kind === 'jointAngle' ? bottom.min : null).toBe(85);
    expect(lockout && lockout.kind === 'jointAngle' ? lockout.max : null).toBe(15);
    expect(bottom?.phases).toEqual(['racked']);
    expect(lockout?.phases).toEqual(['lockout']);
    // Every phase a rule names has to exist, or the rule silently never runs.
    const ids = new Set(shoulderPress.phases.map((phase) => phase.id));
    for (const rule of phased) {
      for (const phase of rule.phases ?? []) {
        expect(ids, `${rule.id} names phase "${phase}"`).toContain(phase);
      }
    }
  });

  it('shares its stance with the curl family rather than restating it', () => {
    const foot = (exercise: typeof shoulderPress) =>
      exercise.technique.find((rule) => rule.id === 'foot_planted_l');
    expect(foot(shoulderPress)).toEqual(foot(bicepCurl));
    expect(shoulderPress.feet).toEqual(bicepCurl.feet);
    expect(shoulderPress.locks).toEqual(bicepCurl.locks);
  });

  it('keeps the torso rule that the stance deliberately does not share', () => {
    // 8° for the press against the curl's 10°: leaning back turns a press into
    // an incline press, where a curl's allowance is about not swinging. Same
    // shape, different reason, so `stance.ts` leaves them apart.
    const angle = (exercise: typeof shoulderPress) => {
      const rule = exercise.technique.find((entry) => entry.id === 'torso_upright');
      return rule && rule.kind === 'segmentAngle' ? rule.max : null;
    };
    expect(angle(shoulderPress)).toBe(8);
    expect(angle(bicepCurl)).toBe(10);
  });

  it('backs its declared grip with a rule, which it did not before', () => {
    // `orientation: 'pronated'` used to be an unchecked caption. It now carries
    // a band the forearm is held inside, from the same row that sets the motion.
    const rule = shoulderPress.technique.find((entry) => entry.id === 'grip_held_l');
    expect(rule, 'the press declares a grip and is checked against it').toBeDefined();
    expect(shoulderPress.hands.orientation).toBe('pronated');
  });

  it('has exactly one registered variant, which the header explains', () => {
    // Asserted so that adding a second is a deliberate act that updates this
    // test and the header with it, rather than quietly changing what the
    // family's coverage means.
    const presses = EXERCISES.filter((exercise) => exercise.clipName.includes('press'));
    expect(presses.map((exercise) => exercise.id)).toEqual(['dumbbell_shoulder_press']);
    expect(pressFamily).toBeTypeOf('function');
  });
});
