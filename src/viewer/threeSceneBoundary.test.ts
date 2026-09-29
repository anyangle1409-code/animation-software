import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const VIEWER_FILES = [
  'scenePointerRouter.ts',
  'ikHandleScene.ts',
  'skeletonScene.ts',
  'studioStage.ts',
  'transformGizmoRuntime.ts',
  'transformGizmoScene.ts',
  'firstPartyViewportRuntime.ts',
  'threeSceneHost.ts',
  'studioEditRuntimes.ts',
  'muscleScene.ts',
] as const;

describe('viewer Three compatibility boundary', () => {
  it('keeps live viewer modules behind one Three gateway', () => {
    for (const file of VIEWER_FILES) {
      const source = readFileSync(new URL('./' + file, import.meta.url), 'utf8');
      expect(source, file).not.toMatch(/from ['"]three(?:\/|['"])/);
    }
  });
});
