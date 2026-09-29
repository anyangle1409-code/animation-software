import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('first-party imported deformation maths', () => {
  for (const file of ['./importedDeformation.ts', './muscleDeformation.ts']) {
    it(`keeps ${file} vector/matrix calculations on Home Gym PT algebra`, () => {
      const source = readFileSync(new URL(file, import.meta.url), 'utf8');
      expect(source).toContain("from '../core/linearMath'");
      expect(source).not.toContain('createCharacterVector3');
      expect(source).not.toContain('CharacterVector3');
      expect(source).not.toContain('.getWorldPosition(');
      expect(source).not.toContain('.worldToLocal(');
    });
  }
});
