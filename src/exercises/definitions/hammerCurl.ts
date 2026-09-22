import { curlFamily } from '../families/curl';

/**
 * Standing two-arm hammer curl.
 *
 * The first variant built on a family rather than copied from a sibling, and the
 * point of the exercise: what is written here is only what makes a hammer curl
 * different from a dumbbell curl. Everything else — the elbow-led timing, the
 * quiet shoulder, the planted feet, the torso rules, the wrist rules — is
 * inherited and cannot drift away from the curl it shares them with.
 *
 * The difference is the grip, and the grip is motion: `neutral` sets the
 * forearm's axial rotation to the rig's neutral instead of 72° of supination,
 * turns the dumbbell with it because the implement is rigid in the hand, and
 * sets the band the technique rule holds it inside. One word changes all three.
 *
 * `forearm_flexors` is promoted to a prime mover, which is as close as the
 * vocabulary gets. A hammer curl's real headline is the brachioradialis, and
 * `MUSCLE_GROUP_IDS` has no entry for it — it exists in the repo only as
 * écorché-only sculpt data, never as a group with an activation row. Naming the
 * flexor compartment is honest rather than exact, and the gap is worth closing
 * when the muscle model next moves.
 */
export const hammerCurl = curlFamily({
  id: 'dumbbell_hammer_curl',
  name: 'Dumbbell Hammer Curl',
  clipName: 'hammer_curl',
  description:
    'Standing two-arm dumbbell curl with a neutral grip — palms facing each ' +
    'other throughout. The neutral forearm shifts the work from the biceps ' +
    'towards the brachioradialis and the forearm flexors.',
  grip: 'neutral',
  mass: 12,
  // A hammer curl needs the arms wider, and the reason is geometry rather than
  // taste. A dumbbell held neutral turns its plates to face the leg, presenting
  // their full 48 mm radius, where a supinated one presents a 17.5 mm edge. At
  // the family's 3 deg the plate drives 16.92 mm into the thigh through the
  // bottom of the rep, 82 vertices inside, measured on the production character.
  //
  // 12 deg is determined rather than chosen: 11 deg leaves only 2.26 mm, and
  // 13 deg clears 22.98 mm but pushes the hands past the 0.56 m the
  // `hands_shoulder_width` rule allows. 12 deg clears 11.41 mm with nothing
  // inside, which is more room than the reference curl's own 9.75 mm.
  //
  // Worth stating plainly: every one of those variants passed technique, IK,
  // loop closure and contact validation, including the one 16.92 mm inside the
  // leg. Nothing in the suite measures body-versus-equipment penetration yet -
  // that is Phase 5 - so this number comes from a harness, not a gate.
  abduction: { start: 12, peak: 13 },
  muscles: {
    primary: ['biceps', 'forearm_flexors'],
    secondary: ['deltoid_anterior'],
  },
  commonErrors: [
    {
      id: 'rolling_to_supination',
      label: 'Rolling the palms up',
      description:
        'The forearms turn towards a normal curl as the weight rises, which hands the work back to the biceps.',
      ruleId: 'grip_held_l',
      correction: 'Keep the thumbs up and the knuckles outward for the whole repetition.',
    },
  ],
});
