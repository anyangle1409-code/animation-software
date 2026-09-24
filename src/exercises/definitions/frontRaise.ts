import { raiseFamily } from '../families/raise';

/**
 * Standing dumbbell front raise.
 *
 * The shoulder-raise family's second direction: the same soft-elbowed lever
 * raised straight ahead to shoulder height, palms down.
 */
export const frontRaise = raiseFamily({
  id: 'dumbbell_front_raise',
  name: 'Dumbbell Front Raise',
  clipName: 'dumbbell_front_raise',
  direction: 'front',
  description:
    'Standing with a dumbbell in each hand in front of the thighs, palms down. ' +
    'The arms rise straight ahead on a slight elbow bend to shoulder height, then ' +
    'lower under control.',
});
