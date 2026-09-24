import { pressFamily } from '../families/press';

/**
 * Seated dumbbell shoulder press.
 *
 * The standing press, sat down: the same grip, range, tempo and rules, with the
 * body supported on the end of a flat bench and the feet flat in front. It is
 * the press family's proof that support is a variant field like any other —
 * and the first exercise that rests the body on a piece of equipment.
 */
export const seatedShoulderPress = pressFamily({
  id: 'seated_dumbbell_shoulder_press',
  name: 'Seated Dumbbell Shoulder Press',
  clipName: 'seated_dumbbell_shoulder_press',
  grip: 'pronated',
  support: 'seated',
  description:
    'Overhead press sitting on the end of a flat bench, feet flat on the floor. ' +
    'Dumbbells press from beside the head to straight over the shoulders, with ' +
    'the torso tall and still.',
});
