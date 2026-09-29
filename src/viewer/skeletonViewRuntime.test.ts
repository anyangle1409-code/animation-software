import { Scene } from 'three';
import { describe, expect, it, vi } from 'vitest';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton } from '../rig/skeleton';
import { createSceneState } from './sceneStateCore';
import {
  createSkeletonViewRuntime,
  type SkeletonViewState,
  type SkeletonViewStorePort,
} from './skeletonViewRuntime';

function createStore(initial: SkeletonViewState): SkeletonViewStorePort & {
  set(next: Partial<SkeletonViewState>): void;
} {
  let state = initial;
  const listeners = new Set<() => void>();
  return {
    getState: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    set(next) {
      state = { ...state, ...next };
      for (const listener of [...listeners]) listener();
    },
  };
}

describe('framework-neutral skeleton view runtime', () => {
  it('mounts, follows frame/store state, routes picks and disposes cleanly', () => {
    const sceneState = createSceneState();
    const root = new Scene();
    const selected: Array<BoneName | null> = [];
    const handlers = new Map<object, { pointerdown?: (event: { stopPropagation(): void }) => void }>();
    const pointers = {
      register: vi.fn((object: object, handler: { pointerdown?: (event: { stopPropagation(): void }) => void }) => {
        handlers.set(object, handler);
        return () => handlers.delete(object);
      }),
    };
    const store = createStore({
      selection: { bone: null },
      showJoints: true,
      selectBone: (bone) => selected.push(bone),
    });

    const runtime = createSkeletonViewRuntime({
      sceneState,
      root,
      pointers,
      store,
      skeleton: canonicalSkeleton,
    });

    expect(root.children).toContain(runtime.resources.group);
    expect(sceneState.consumers.subscriberCount).toBe(1);

    const upperarm = runtime.resources.bones.get('upperarm_l')!;
    expect(upperarm.joint.visible).toBe(true);

    store.set({ selection: { bone: 'upperarm_l' }, showJoints: false });
    expect(upperarm.joint.visible).toBe(false);
    expect(upperarm.joint.material.emissiveIntensity).toBeGreaterThan(0);

    sceneState.evaluation.apply({
      rotations: { upperarm_l: { x: 0.2, y: 0, z: 0 } },
      rootPosition: { x: 0, y: 0, z: 0 },
      rootRotation: { x: 0, y: 0, z: 0 },
    });
    sceneState.consumers.dispatch({ delta: 0.016, elapsed: 1, timestampMs: 1000 });
    expect(Array.from(upperarm.group.matrix.elements)).toEqual(
      Array.from(sceneState.evaluation.matrix('upperarm_l').elements),
    );

    const handler = handlers.get(upperarm.joint);
    const stopPropagation = vi.fn();
    handler?.pointerdown?.({ stopPropagation });
    expect(stopPropagation).toHaveBeenCalledTimes(1);
    expect(selected).toEqual(['upperarm_l']);

    runtime.dispose();
    runtime.dispose();

    expect(root.children).not.toContain(runtime.resources.group);
    expect(sceneState.consumers.subscriberCount).toBe(0);
    expect(handlers.size).toBe(0);
  });
});
