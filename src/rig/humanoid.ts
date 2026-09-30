/**
 * Historical v3 compatibility exports.
 *
 * The live runtime uses hgpt_canonical_v4_original. These names remain for
 * regression tests and historical comparisons only. Operational generation
 * imports the frozen exercise-authoring reference directly so this module does
 * not need to be reachable from src/main.ts.
 */
export {
  EXERCISE_AUTHORING_REFERENCE_BONES as HUMANOID_BONES,
  EXERCISE_AUTHORING_REFERENCE_HEIGHT as RIG_HEIGHT,
  SHOULDER_WIDENING,
  SHOULDER_SETBACK,
  SIDE_LIST,
  FINGER_LIST,
} from './exerciseAuthoringReference';
