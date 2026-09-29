import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('character Three boundary consolidation', () => {
  it('keeps direct Three imports out of character construction and GLB materialization', () => {
    for (const file of ['./bones.ts', './gltfThreeScene.ts']) {
      const source = readFileSync(new URL(file, import.meta.url), 'utf8');
      expect(source).not.toMatch(/from ['"]three(?:\/|['"])/);
      expect(source).toContain("from './threeSceneBoundary'");
    }
  });

  it('routes the character adapter through the single project-wide vendor gateway', () => {
    const source = readFileSync(new URL('./threeSceneBoundary.ts', import.meta.url), 'utf8');
    expect(source).not.toMatch(/from ['"]three(?:\/|['"])/);
    expect(source).toContain("from '../core/threeRuntimeBoundary'");
  });
});
