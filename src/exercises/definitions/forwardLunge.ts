import { lungeFamily } from '../families/lunge';

/**
 * Forward lunge.
 *
 * The lunge family's stepping variant: a long step forward with the left foot
 * from standing, down to the back knee just above the floor, and a push off
 * the front foot back to standing.
 */
export const forwardLunge = lungeFamily({
  id: 'forward_lunge',
  name: 'Forward Lunge',
  clipName: 'forward_lunge',
  step: 'forward',
  description:
    'From standing, one long step forward, lowering until the back knee is just ' +
    'above the floor, then a push off the front foot back to standing.',
});
