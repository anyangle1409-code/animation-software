import { Scene } from 'three';
import { describe, expect, it, vi } from 'vitest';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import type { EquipmentInstance } from '../equipment/types';
import { canonicalSkeleton } from '../rig/skeleton';
import { createSceneState } from './sceneStateCore';
import {
  createEquipmentViewRuntime,
  type EquipmentViewStudioState,
  type EquipmentViewStorePort,
} from './equipmentViewRuntime';

function createStore(initial: EquipmentViewStudioState): EquipmentViewStorePort & {
  setEquipment(equipment: EquipmentInstance[]): void;
} {
  let state = initial;
  const listeners = new Set<() => void>();
  return {
    getState: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    setEquipment(equipment) {
      state = {
        ...state,
        document: { clip: { equipment } },
      };
      for (const listener of [...listeners]) listener();
    },
  };
}

describe('framework-neutral equipment view runtime', () => {
  it('mounts, places, rebuilds, routes picks and disposes cleanly', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const selected: string[] = [];
    const store = createStore({
      document: { clip: { equipment: clip.equipment } },
      selectEquipment: (id) => {
        if (id) selected.push(id);
      },
    });
    const sceneState = createSceneState();
    sceneState.frame = resolveFrame(
      canonicalSkeleton,
      sceneState.evaluation,
      clip,
      0,
    );
    const root = new Scene();
    const handlers = new Map<object, { pointerdown?: (event: { stopPropagation(): void }) => void }>();
    const pointers = {
      register: vi.fn((object: object, handler: { pointerdown?: (event: { stopPropagation(): void }) => void }) => {
        handlers.set(object, handler);
        return () => handlers.delete(object);
      }),
    };

    const runtime = createEquipmentViewRuntime({
      sceneState,
      root,
      pointers,
      store,
      characterStore: { getState: () => ({ active: null }) },
    });

    expect(root.children).toContain(runtime.resources.group);
    expect(sceneState.consumers.subscriberCount).toBe(1);
    expect(runtime.resources.instances.size).toBeGreaterThan(0);

    sceneState.consumers.dispatch({ delta: 0.016, elapsed: 1, timestampMs: 1000 });
    const first = [...runtime.resources.instances.entries()][0];
    expect(first).toBeDefined();
    if (!first) throw new Error('Expected equipment fixture');
    const [id, group] = first;
    expect(group.visible).toBe(true);

    const handler = handlers.get(group);
    const stopPropagation = vi.fn();
    handler?.pointerdown?.({ stopPropagation });
    expect(stopPropagation).toHaveBeenCalledTimes(1);
    expect(selected).toEqual([id]);

    const previousGroup = runtime.resources.group;
    store.setEquipment([]);
    expect(root.children).not.toContain(previousGroup);
    expect(runtime.resources.instances.size).toBe(0);
    expect(root.children).toContain(runtime.resources.group);

    runtime.dispose();
    runtime.dispose();
    expect(root.children).not.toContain(runtime.resources.group);
    expect(sceneState.consumers.subscriberCount).toBe(0);
    expect(handlers.size).toBe(0);
  });
});
