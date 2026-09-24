import { rotationFamily } from '../families/rotation';

/**
 * Russian twist.
 *
 * The rotation family's reference variant: bodyweight, seated on the floor,
 * leaning back with the heels down and the hands clasped, the shoulders turned
 * from one side to the other over still hips.
 */
export const russianTwist = rotationFamily({
  id: 'russian_twist',
  name: 'Russian Twist',
  clipName: 'russian_twist',
  description:
    'Seated on the floor, leaning back with the knees bent and the heels down, ' +
    'hands clasped in front of the chest. The shoulders turn from side to side ' +
    'while the hips stay still.',
});
