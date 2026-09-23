import { pressFamily } from '../families/press';

/**
 * Standing two-arm dumbbell overhead press.
 *
 * The press family's reference variant. It exercises the shoulder itself rather
 * than the arm below it: the humerus travels from 72° of abduction to nearly
 * overhead, at the end of its range where the joint limits are tightest.
 */
export const shoulderPress = pressFamily({
  id: 'dumbbell_shoulder_press',
  name: 'Dumbbell Shoulder Press',
  clipName: 'shoulder_press',
  description:
    'Standing dumbbell overhead press. The dumbbells start beside the head ' +
    'with the elbows under the wrists and finish stacked over the shoulders.',
  grip: 'pronated',
  mass: 12,
});
