import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('single Three runtime gateway', () => {
  it('removes the character compatibility boundary and contains the viewer boundary', () => {
    expect(() =>
      readFileSync(new URL('../character/threeSceneBoundary.ts', import.meta.url), 'utf8'),
    ).toThrow();

    const viewer = readFileSync(
      new URL('../viewer/threeSceneBoundary.ts', import.meta.url),
      'utf8',
    );
    expect(viewer).not.toMatch(/from ['"]three(?:\/|['"])/);
    expect(viewer).toContain("threeRuntimeBoundary");
  });

  it('contains the remaining direct runtime import in one explicit file', () => {
    const source = readFileSync(new URL('./threeRuntimeBoundary.ts', import.meta.url), 'utf8');
    expect(source).toContain("from 'three'");
  });
});
