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

  it('retains the legacy Three adapter only as a compatibility/parity surface', () => {
    const source = readFileSync(new URL('./threeSceneBoundary.ts', import.meta.url), 'utf8');
    expect(source).not.toMatch(/from ['"]three(?:\/|['"])/);
    expect(source).toContain("from '../core/threeRuntimeBoundary'");
  });
});
