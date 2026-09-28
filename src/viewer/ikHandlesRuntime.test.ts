import { Scene } from 'three';
import { describe, expect, it, vi } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { IK_CHAIN_IDS } from '../ik/chains';
import type { IKChainId } from '../ik/types';
import { canonicalSkeleton } from '../rig/skeleton';
import { createSceneState } from './sceneStateCore';
import type { IKHandleKind } from './ikHandleScene';
import {
  createIKHandlesRuntime,
  type IKHandlesState,
  type IKHandlesStorePort,
} from './ikHandlesRuntime';

function createStore(initial: IKHandlesState): IKHandlesStorePort & {
  setSelection(handle: { chain: IKChainId; kind: IKHandleKind } | null): void;
} {
  let state = initial;
  const listeners = new Set<() => void>();
  return {
    getState: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    setSelection(handle) {
      state = { ...state, selection: { handle } };
      for (const listener of [...listeners]) listener();
    },
  };
}

describe('framework-neutral IK handle runtime', () => {
  it('mounts, follows selection/frame state, routes picks and disposes', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const chosen: Array<{ chain: IKChainId; kind: IKHandleKind } | null> = [];
    const store = createStore({
      time: 0,
      document: { clip },
      selection: { handle: null },
      selectHandle: (handle) => chosen.push(handle),
    });
    const sceneState = createSceneState();
    const root = new Scene();
    const handlers = new Map<object, { pointerdown?: (event: { stopPropagation(): void }) => void }>();
    const pointers = {
      register: vi.fn((object: object, handler: { pointerdown?: (event: { stopPropagation(): void }) => void }) => {
        handlers.set(object, handler);
        return () => handlers.delete(object);
      }),
    };

    const runtime = createIKHandlesRuntime({
      sceneState,
      root,
      pointers,
      store,
    });

    expect(root.children).toContain(runtime.resources.group);
    expect(sceneState.consumers.subscriberCount).toBe(1);

    const chain = IK_CHAIN_IDS[0];
    const target = runtime.resources.handles.get(`${chain}:target`)!;

    store.setSelection({ chain, kind: 'target' });
    expect((target.material as import('three').MeshStandardMaterial).emissiveIntensity)
      .toBeGreaterThan(0);

    sceneState.consumers.dispatch({ delta: 0.016, elapsed: 1, timestampMs: 1000 });
    expect(Number.isFinite(target.position.x)).toBe(true);

    const stopPropagation = vi.fn();
    handlers.get(target)?.pointerdown?.({ stopPropagation });
    expect(stopPropagation).toHaveBeenCalledTimes(1);
    expect(chosen).toEqual([{ chain, kind: 'target' }]);

    runtime.dispose();
    runtime.dispose();

    expect(root.children).not.toContain(runtime.resources.group);
    expect(sceneState.consumers.subscriberCount).toBe(0);
    expect(handlers.size).toBe(0);
  });
});
