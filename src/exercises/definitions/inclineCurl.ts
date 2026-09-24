import { curlFamily } from '../families/curl';

/**
 * Incline dumbbell curl.
 *
 * The curl family's fourth variant, and the first that lies back on a bench: a
 * supinated curl with the back on an incline set to 45° and the arms hanging
 * straight down behind the body, so every repetition starts with the biceps on
 * full stretch.
 */
export const inclineCurl = curlFamily({
  id: 'incline_dumbbell_curl',
  name: 'Incline Dumbbell Curl',
  clipName: 'incline_dumbbell_curl',
  grip: 'supinated',
  support: 'incline',
  mass: 8,
  description:
    'Supinated curl lying back on a 45° incline bench. The arms hang straight ' +
    'down behind the body and stay there while the elbows curl, so each ' +
    'repetition starts from a full biceps stretch.',
});
