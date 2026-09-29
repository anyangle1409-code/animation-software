import { describe, expect, it, vi } from 'vitest';
import { HgScene } from '../core/sceneGraph';
import { canonicalSkeleton } from '../rig/skeleton';
import { createSceneState } from './sceneStateCore';
import { createFirstPartyStaticStageRuntime } from './firstPartyStaticStageRuntime';
import { createFirstPartySkeletonViewRuntime } from './firstPartySkeletonViewRuntime';

describe('first-party scene lifecycle wrappers', () => {
  it('mounts/rebuilds the project-owned stage and skeleton without vendor scene nodes', () => {
    const scene = new HgScene();
    let stageState = { backdrop: 'studio' as const, showGrid: true };
    const stageListeners = new Set<() => void>();
    const stage = createFirstPartyStaticStageRuntime(scene, {
      getState: () => stageState,
      subscribe(listener) {
        stageListeners.add(listener);
        return () => stageListeners.delete(listener);
      },
    });
    expect(scene.children).toContain(stage.stage.root);
    expect(scene.background).toBe('#12151a');

    const sceneState = createSceneState();
    const handlers = new Map<object, unknown>();
    const skeleton = createFirstPartySkeletonViewRuntime({
      sceneState,
      root: scene,
      pointers: {
        register: vi.fn((object: object, handler: unknown) => {
          handlers.set(object, handler);
          return () => handlers.delete(object);
        }),
      },
      store: {
        getState: () => ({
          selection: { bone: null },
          showJoints: true,
          selectBone: vi.fn(),
        }),
        subscribe: () => () => {},
      },
      skeleton: canonicalSkeleton,
    });
    expect(scene.children).toContain(skeleton.resources.group);
    expect(skeleton.resources.bones.size).toBeGreaterThan(0);

    stageState = { backdrop: 'void', showGrid: true };
    for (const listener of stageListeners) listener();
    expect(scene.background).toBe('#000000');
    expect(stage.stage.floor).toBeNull();

    skeleton.dispose();
    stage.dispose();
    expect(scene.children).toHaveLength(0);
  });
});
