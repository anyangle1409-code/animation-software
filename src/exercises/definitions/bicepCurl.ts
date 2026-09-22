import { curlFamily } from '../families/curl';

/**
 * Standing two-arm dumbbell curl.
 *
 * The curl family's reference variant, and the exercise the studio opens on.
 * Everything that makes it a curl lives in `families/curl.ts`; what is left here
 * is what makes it *this* curl.
 */
export const bicepCurl = curlFamily({
  id: 'dumbbell_bicep_curl',
  name: 'Dumbbell Bicep Curl',
  clipName: 'bicep_curl',
  description:
    'Standing two-arm dumbbell curl with a supinated grip. The upper arms stay ' +
    'still beside the torso and the forearms do the work.',
  grip: 'supinated',
  mass: 10,
});
