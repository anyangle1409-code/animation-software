import { supineFamily } from '../families/supine';

/**
 * Flat dumbbell bench press.
 *
 * The supine family's reference variant: lying on a flat bench, feet flat on
 * the floor, a dumbbell in each hand pressed from beside the chest to arm's
 * length above the shoulders.
 */
export const dumbbellBenchPress = supineFamily({
  id: 'dumbbell_bench_press',
  name: 'Dumbbell Bench Press',
  clipName: 'dumbbell_bench_press',
  motion: 'press',
  description:
    'Lying on a flat bench with the feet flat on the floor. The dumbbells lower ' +
    'under control to the sides of the chest, elbows angled out below the ' +
    'shoulders, then press back up over the shoulders.',
});
