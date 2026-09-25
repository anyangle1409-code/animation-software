import { describe, expect, it } from 'vitest';
import { EXERCISE_BY_ID } from '../exercises/library';
import { GENERATOR_FAMILIES } from '../generation/families';
import { referenceForFamily } from './library';

describe('generator/reference coverage contract', () => {
  it('gives every certified generator family an independent local reference pack', () => {
    for (const family of GENERATOR_FAMILIES) {
      expect(family.library.length, family.id).toBeGreaterThan(0);
      const exercise = EXERCISE_BY_ID.get(family.library[0]);
      expect(exercise, `${family.id}: missing library reference ${family.library[0]}`).toBeDefined();

      const reference = referenceForFamily(family.id, exercise!);
      expect(reference.family, family.id).toBe(family.id);
      expect(reference.schemaVersion, family.id).toBe(1);
      expect(reference.referenceVersion, family.id).toBeGreaterThanOrEqual(1);
      expect(reference.provenance.length, family.id).toBeGreaterThan(20);
      expect(reference.checks.length, family.id).toBeGreaterThanOrEqual(5);
      expect(reference.reviewViews?.length ?? 0, family.id).toBeGreaterThanOrEqual(3);

      const ids = reference.checks.map((check) => check.id);
      expect(new Set(ids).size, `${family.id}: duplicate reference check ids`).toBe(ids.length);

      const views = (reference.reviewViews ?? []).map((view) => view.id);
      expect(new Set(views).size, `${family.id}: duplicate review view ids`).toBe(views.length);
    }
  });

  it('keeps generator proving-set ids real and unique within each family', () => {
    for (const family of GENERATOR_FAMILIES) {
      expect(new Set(family.library).size, family.id).toBe(family.library.length);
      for (const id of family.library) {
        expect(EXERCISE_BY_ID.has(id), `${family.id}: ${id}`).toBe(true);
      }
    }
  });

  it('does not accidentally certify a draft reference through generator registration', () => {
    for (const family of GENERATOR_FAMILIES) {
      const exercise = EXERCISE_BY_ID.get(family.library[0])!;
      // Certification is a separate reviewed act. Expanding prompt generation
      // must never silently flip the independent reference pack to certified.
      expect(referenceForFamily(family.id, exercise).status, family.id).toBe('draft');
    }
  });
});
