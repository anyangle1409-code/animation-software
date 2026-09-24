import type { ExerciseDefinition } from './types';
import { bicepCurl } from './definitions/bicepCurl';
import { hammerCurl } from './definitions/hammerCurl';
import { reverseCurl } from './definitions/reverseCurl';
import { pushUp } from './definitions/pushUp';
import { airSquat } from './definitions/airSquat';
import { shoulderPress } from './definitions/shoulderPress';
import { pullUp } from './definitions/pullUp';
import { romanianDeadlift } from './definitions/romanianDeadlift';
import { bentOverRow } from './definitions/bentOverRow';
import { seatedShoulderPress } from './definitions/seatedShoulderPress';
import { inclineCurl } from './definitions/inclineCurl';
import { overheadExtension } from './definitions/overheadExtension';
import { splitSquat } from './definitions/splitSquat';
import { cablePushdown } from './definitions/cablePushdown';
import { lateralRaise } from './definitions/lateralRaise';
import { frontRaise } from './definitions/frontRaise';
import { calfRaise } from './definitions/calfRaise';
import { dumbbellCalfRaise } from './definitions/dumbbellCalfRaise';
import { pallofPress } from './definitions/pallofPress';
import { dumbbellBenchPress } from './definitions/dumbbellBenchPress';
import { dumbbellFly } from './definitions/dumbbellFly';
import { russianTwist } from './definitions/russianTwist';
import { cableWoodchop } from './definitions/cableWoodchop';

/**
 * Every exercise the studio knows about. The engine is deliberately proven on a
 * small set first — one arm exercise, one whole-body pressing movement, one
 * lower-body movement — rather than filled with variations of the same thing.
 *
 * The hammer curl is the exception, and it is here to prove something rather
 * than to pad the list: it is the first exercise built from a movement family
 * instead of copied from a sibling, so it is the measure of whether a variant
 * really is a short override.
 */
export const EXERCISES: ExerciseDefinition[] = [
  bicepCurl,
  hammerCurl,
  reverseCurl,
  pushUp,
  airSquat,
  shoulderPress,
  pullUp,
  romanianDeadlift,
  bentOverRow,
  seatedShoulderPress,
  inclineCurl,
  overheadExtension,
  splitSquat,
  cablePushdown,
  lateralRaise,
  frontRaise,
  calfRaise,
  dumbbellCalfRaise,
  pallofPress,
  dumbbellBenchPress,
  dumbbellFly,
  russianTwist,
  cableWoodchop,
];

export const EXERCISE_BY_ID = new Map(EXERCISES.map((exercise) => [exercise.id, exercise]));

export function getExercise(id: string): ExerciseDefinition {
  const exercise = EXERCISE_BY_ID.get(id);
  if (!exercise) throw new Error(`Unknown exercise "${id}"`);
  return exercise;
}
