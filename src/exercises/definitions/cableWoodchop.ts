import { rotationFamily } from '../families/rotation';

/**
 * Cable woodchop, high to low.
 *
 * The rotation family's standing variant: side-on to a high cable, the handle
 * in both hands, chopped down across the body to beside the far hip on long
 * arms as the hips and trunk turn, and returned under control.
 */
export const cableWoodchop = rotationFamily({
  id: 'cable_woodchop',
  name: 'Cable Woodchop',
  clipName: 'cable_woodchop',
  setup: 'cable',
  description:
    'Standing side-on to a high cable, the handle held in both hands. The ' +
    'handle is pulled diagonally down across the body to outside the far knee, ' +
    'the hips and trunk turning with it, then returned under control.',
});
