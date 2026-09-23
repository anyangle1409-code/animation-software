import { squatFamily } from '../families/squat';

/**
 * Bodyweight squat.
 *
 * The squat family's reference variant, and the library's only lower-body
 * exercise. It tests the hardest thing the engine does below the waist: the
 * descent is authored as root motion — the body sinks half a metre — and the
 * legs are solved backwards from feet that must not move at all.
 */
export const airSquat = squatFamily({
  id: 'air_squat',
  name: 'Bodyweight Squat',
  clipName: 'air_squat',
  description:
    'Bodyweight squat to depth with a shoulder-width stance. The feet stay ' +
    'planted, the heels stay down, and the hips and knees bend together.',
});
