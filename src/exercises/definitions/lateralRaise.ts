import { raiseFamily } from '../families/raise';

/**
 * Standing dumbbell lateral raise.
 *
 * The shoulder-raise family's reference variant: a dumbbell in each hand, arms
 * swung out to the sides to shoulder height on a soft, fixed elbow, a little
 * forward of the body in the line of the shoulder blades.
 */
export const lateralRaise = raiseFamily({
  id: 'dumbbell_lateral_raise',
  name: 'Dumbbell Lateral Raise',
  clipName: 'dumbbell_lateral_raise',
  direction: 'lateral',
  description:
    'Standing with a dumbbell in each hand at the sides. The arms rise out to ' +
    'the sides on a slight elbow bend until they are level with the shoulders, ' +
    'palms turning to face the floor, then lower under control.',
});
