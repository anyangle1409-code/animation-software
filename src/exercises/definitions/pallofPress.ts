import { antiRotationFamily } from '../families/antiRotation';

/**
 * Standing cable Pallof press.
 *
 * The anti-rotation family's reference variant: side-on to a chest-height
 * cable, the handle pressed straight out from the sternum and held while the
 * trunk refuses to turn towards the stack.
 */
export const pallofPress = antiRotationFamily({
  id: 'cable_pallof_press',
  name: 'Cable Pallof Press',
  clipName: 'cable_pallof_press',
  side: 'left',
  description:
    'Standing side-on to a chest-height cable with the handle clasped at the ' +
    'sternum. The arms press the handle straight out, hold it there while the ' +
    'hips and shoulders stay square against the pull, and bring it back.',
});
