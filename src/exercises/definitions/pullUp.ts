import { verticalPullFamily } from '../families/verticalPull';

/**
 * Strict bodyweight pull-up from the crossbar of a rack.
 *
 * Tests the one thing nothing else in the library does: the body is supported
 * entirely by two grips on a piece of equipment that never moves, with no floor
 * contact at all. The measurements behind every value are in
 * `families/verticalPull.ts`.
 */
export const pullUp = verticalPullFamily({
  id: 'pull_up',
  name: 'Pull-Up',
  clipName: 'pull_up',
  description:
    'Strict pull-up from a dead hang with a pronated grip just wider than the ' +
    'shoulders. The hands stay fixed on the bar and the whole body travels.',
});
