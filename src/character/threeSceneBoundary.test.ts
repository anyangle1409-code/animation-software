import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('character production scene boundary', () => {
  it('keeps canonical character construction on first-party scene/skin classes', () => {
    const source = readFileSync(new URL('./bones.ts', import.meta.url), 'utf8');
    expect(source).not.toContain("from './threeSceneBoundary'");
    expect(source).toContain("from '../core/sceneGraph'");
    expect(source).toContain("from '../core/sceneSkin'");
  });

  it('keeps production GLB character loaders on the first-party materialiser', () => {
    for (const file of ['./glbSource.ts', './retargetSource.ts']) {
      const source = readFileSync(new URL(file, import.meta.url), 'utf8');
      expect(source).toContain("from './gltfFirstPartyScene'");
      expect(source).not.toContain("from './gltfThreeScene'");
    }
  });

  it('removes the legacy character Three scene adapters from production source', () => {
    for (const file of ['./threeSceneBoundary.ts', './gltfThreeScene.ts']) {
      expect(() => readFileSync(new URL(file, import.meta.url), 'utf8')).toThrow();
    }
  });
});
