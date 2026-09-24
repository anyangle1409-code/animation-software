import { horizontalPressFamily } from '../families/horizontalPress';

/**
 * Standard push-up.
 *
 * Tests the hardest part of the engine: the body is supported on four contacts
 * at once, so the root moves and the limbs are solved backwards from hands and
 * feet that must not move at all. The root placement is computed so the toes
 * stay pinned while the body pivots on them, and world locks hold the hands.
 * The measurements behind every value are in `families/horizontalPress.ts`.
 */
export const pushUp = horizontalPressFamily({
  id: 'push_up',
  name: 'Push-Up',
  clipName: 'push_up',
  description:
    'Bodyweight push-up with the hands slightly wider than the shoulders. The ' +
    'body travels as one rigid unit between four fixed contacts.',
});
