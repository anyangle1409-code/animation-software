import { lungeFamily } from '../families/lunge';

/**
 * Bodyweight split squat.
 *
 * The lunge family's reference variant: the lunge with the step taken away.
 * The left foot is forward and flat, the right behind on the ball of the foot,
 * and the body sinks straight down between them until the back knee is just
 * above the floor.
 */
export const splitSquat = lungeFamily({
  id: 'split_squat',
  name: 'Bodyweight Split Squat',
  clipName: 'split_squat',
  description:
    'Static lunge with the left foot forward. The body lowers straight down ' +
    'until the back knee is just above the floor, with the torso tall and the ' +
    'front knee tracking over the front foot, then drives back up.',
});
