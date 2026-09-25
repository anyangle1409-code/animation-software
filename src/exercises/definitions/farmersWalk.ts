import { carryFamily } from '../families/carry';

/**
 * Farmer's walk.
 *
 * The carry family's reference variant: a 24 kg dumbbell in each hand at the
 * sides, walking tall in short, even steps. The clip walks in place; its
 * travel speed says how fast to move it.
 */
export const farmersWalk = carryFamily({
  id: 'farmers_walk',
  name: "Farmer's Walk",
  clipName: 'farmers_walk',
  description:
    'Walking tall with a heavy dumbbell in each hand at the sides, shoulders ' +
    'down and trunk braced, in short, even steps.',
});
