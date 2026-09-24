import { extensionFamily } from '../families/extension';

/**
 * Standing overhead dumbbell triceps extension.
 *
 * The elbow-extension family's reference variant: a dumbbell in each hand, the
 * upper arms pointing at the ceiling, and the forearms folding down behind the
 * head and straightening again.
 */
export const overheadExtension = extensionFamily({
  id: 'dumbbell_overhead_triceps_extension',
  name: 'Dumbbell Overhead Triceps Extension',
  clipName: 'dumbbell_overhead_triceps_extension',
  description:
    'Standing triceps extension with a dumbbell in each hand, palms facing in. ' +
    'The upper arms stay pointing at the ceiling while the forearms lower ' +
    'behind the head to a full stretch and straighten to lockout.',
});
