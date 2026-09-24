import { supineFamily } from '../families/supine';

/**
 * Flat dumbbell fly.
 *
 * The supine family's second motion: the same bench and stance as the bench
 * press, the arms opened wide on a soft, fixed elbow, palms facing, and swept
 * back together over the chest by the shoulder alone.
 */
export const dumbbellFly = supineFamily({
  id: 'dumbbell_fly',
  name: 'Dumbbell Fly',
  clipName: 'dumbbell_fly',
  motion: 'fly',
  description:
    'Lying on a flat bench with the feet flat on the floor. The arms open wide ' +
    'on a soft, fixed elbow until the upper arms are level with the chest, ' +
    'then sweep back together over the chest.',
});
