import { describe, expect, it } from 'vitest';
import { EXERCISES } from '../exercises/library';
import { GENERATOR_FAMILIES, generatorFamily } from './families';
import { parsePrompt } from './parse';

/**
 * Prompt generation is the intended entry point for the whole first-party
 * exercise library. Keep that true as the library grows: every registered
 * exercise must belong to one and only one certified generator family, and its
 * own product-facing name must route deterministically back to that reference.
 */
describe('prompt-generation library coverage', () => {
  it('assigns every registered exercise to exactly one generator family', () => {
    const libraryIds = EXERCISES.map((exercise) => exercise.id).sort();
    const generatorIds = GENERATOR_FAMILIES.flatMap((family) => family.library);

    expect(new Set(generatorIds).size).toBe(generatorIds.length);
    expect([...generatorIds].sort()).toEqual(libraryIds);
  });

  it('routes every registered exercise name back to its exact library reference', () => {
    for (const exercise of EXERCISES) {
      const parsed = parsePrompt(`exercise: ${exercise.name}`);
      const blocking = parsed.issues.filter((issue) => issue.blocking);

      expect(blocking, exercise.id).toEqual([]);
      expect(parsed.intent, exercise.id).not.toBeNull();

      const family = generatorFamily(parsed.intent!.family);
      expect(family.library, exercise.id).toContain(exercise.id);
      expect(family.reference(parsed.intent!), exercise.id).toBe(exercise.id);
    }
  });
});
