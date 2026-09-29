import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('single Three runtime gateway', () => {
  it('keeps character and viewer boundaries off direct Three imports', () => {
    for (const file of [
      '../character/threeSceneBoundary.ts',
      '../viewer/threeSceneBoundary.ts',
    ]) {
      const source = readFileSync(new URL(file, import.meta.url), 'utf8');
      expect(source).not.toMatch(/from ['"]three(?:\/|['"])/);
      expect(source).toContain("threeRuntimeBoundary");
    }
  });

  it('contains the remaining direct runtime import in one explicit file', () => {
    const source = readFileSync(new URL('./threeRuntimeBoundary.ts', import.meta.url), 'utf8');
    expect(source).toContain("from 'three'");
  });
});
