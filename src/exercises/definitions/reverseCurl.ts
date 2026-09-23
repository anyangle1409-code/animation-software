import { curlFamily } from '../families/curl';

/**
 * Standing two-arm reverse curl.
 *
 * The curl family's third variant, and the cheapest evidence yet that the family
 * is doing its job: the `pronated` grip row already existed and was already
 * covered by `families/curl.test.ts`, so this exercise is a description and a
 * grip name. No new code, no new rules, no new tuning.
 *
 * A reverse curl turns the palms down, which takes the biceps out of its best
 * leverage and hands the work to the forearm extensors and the brachioradialis.
 * The load drops accordingly — a lifter curls meaningfully less weight this way,
 * and 7 kg against the dumbbell curl's 10 kg is that difference.
 */
export const reverseCurl = curlFamily({
  id: 'dumbbell_reverse_curl',
  name: 'Dumbbell Reverse Curl',
  clipName: 'reverse_curl',
  description:
    'Standing two-arm dumbbell curl with a pronated grip — palms facing down ' +
    'throughout. Shifts the work from the biceps to the forearm extensors.',
  grip: 'pronated',
  mass: 7,
  // The family's 16 deg at the bottom is not enough here. A pronated grip turns
  // the dumbbell so it hangs differently against the thigh, and at 16 deg the
  // plate drove 5.50 mm in with 8 vertices inside - caught by the clearance
  // gate on the exercise's first run, before it was ever looked at.
  //
  // The elbow is the right lever and the family already says why: bending it is
  // where a hanging dumbbell's thigh clearance is bought, rather than tilting
  // the humerus forward. Abduction was tried first and rejected on measurement -
  // its landscape here is a ridge, not a slope, running 0.79, 2.39, 4.21, 5.70,
  // 0.47 and -4.76 mm across 4 to 6.5 deg, so any value that passed would sit
  // one degree from one that does not. Elbow angle is monotonic over the same
  // range - 20 deg gives 2.96 mm, 22 gives 6.77, 23 gives 11.49, 24 gives 16.69 -
  // so 23 is chosen for clearing comfortably from the flat part of a slope
  // rather than from the top of a spike. Measured 11.49 mm, against the
  // dumbbell curl's 11.46 mm and the hammer curl's 11.68 mm.
  elbow: { start: 23, peak: 126 },
  muscles: {
    primary: ['biceps', 'forearm_extensors'],
    secondary: ['forearm_flexors', 'deltoid_anterior'],
  },
  commonErrors: [
    {
      id: 'rolling_to_supination',
      label: 'Letting the palms turn up',
      description:
        'The forearms rotate back towards a normal curl as the weight rises, handing the work back to the biceps.',
      ruleId: 'grip_held_l',
      correction: 'Keep the knuckles up and the palms facing the floor for the whole repetition.',
    },
  ],
});
