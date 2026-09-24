import { rowFamily } from '../families/row';

/**
 * Dumbbell bent-over row.
 *
 * The horizontal-pull family's reference variant. The body holds a hinge — the
 * trunk about 50° forward over soft knees and flat feet — and the arms row a
 * dumbbell each from a long hang up past the ribs, palms facing in.
 */
export const bentOverRow = rowFamily({
  id: 'dumbbell_bent_over_row',
  name: 'Dumbbell Bent-Over Row',
  clipName: 'dumbbell_bent_over_row',
  description:
    'Bent-over row with a dumbbell in each hand, palms facing in. The back stays ' +
    'flat and still at about 50° from vertical while the elbows drive back past ' +
    'the ribs, then lower under control to a full stretch.',
});
