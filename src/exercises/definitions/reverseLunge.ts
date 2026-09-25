import { lungeFamily } from '../families/lunge';

/**
 * Reverse lunge.
 *
 * The lunge family's backward-stepping variant: the front foot stays where it
 * stands, and the right foot steps back onto its ball into the split squat's
 * bottom position.
 */
export const reverseLunge = lungeFamily({
  id: 'reverse_lunge',
  name: 'Reverse Lunge',
  clipName: 'reverse_lunge',
  step: 'back',
  description:
    'From standing, one long step back with the right foot onto its ball, ' +
    'lowering until the back knee is just above the floor, then a drive through ' +
    'the front heel back to standing.',
});
