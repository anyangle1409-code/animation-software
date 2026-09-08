import type { ExerciseDefinition } from './types';
import { bicepCurl } from './definitions/bicepCurl';
import { pushUp } from './definitions/pushUp';
import { airSquat } from './definitions/airSquat';

/**
 * Every exercise the studio knows about. The engine is deliberately proven on a
 * small set first — one arm exercise, one whole-body pressing movement, one
 * lower-body movement — rather than filled with variations of the same thing.
 */
export const EXERCISES: ExerciseDefinition[] = [bicepCurl, pushUp, airSquat];

export const EXERCISE_BY_ID = new Map(EXERCISES.map((exercise) => [exercise.id, exercise]));

export function getExercise(id: string): ExerciseDefinition {
  const exercise = EXERCISE_BY_ID.get(id);
  if (!exercise) throw new Error(`Unknown exercise "${id}"`);
  return exercise;
}
