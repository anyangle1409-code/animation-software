import { hingeFamily } from '../families/hinge';

/**
 * Dumbbell Romanian deadlift.
 *
 * The hinge family's reference variant. Everything the squat does with the
 * knees it does with the hips instead: the whole body pitches forward from
 * planted feet, the hips travel back, the spine keeps its standing shape, and
 * the dumbbells hang from straight arms and travel down the front of the legs.
 */
export const romanianDeadlift = hingeFamily({
  id: 'dumbbell_romanian_deadlift',
  name: 'Dumbbell Romanian Deadlift',
  clipName: 'dumbbell_romanian_deadlift',
  description:
    'Hip hinge with a dumbbell in each hand. The knees stay soft, the back stays ' +
    'flat, and the hips travel back until the hamstrings are stretched, with the ' +
    'dumbbells kept close to the legs all the way down and up.',
});
