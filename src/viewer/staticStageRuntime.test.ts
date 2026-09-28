import { Color, Scene } from 'three';
import { describe, expect, it } from 'vitest';
import type { Backdrop } from '../editor/storeCore';
import {
  createStaticStageRuntime,
  type StaticStageState,
  type StaticStageStorePort,
} from './staticStageRuntime';

function createStore(initial: StaticStageState): StaticStageStorePort & {
  set(next: Partial<StaticStageState>): void;
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

describe('framework-neutral static Studio stage runtime', () => {
  it('mounts, rebuilds from store state and restores the prior background', () => {
    const root = new Scene();
    const before = new Color('#123456');
    root.background = before;
    const store = createStore({ backdrop: 'studio' as Backdrop, showGrid: true });

    const runtime = createStaticStageRuntime(root, store);
    expect(root.children).toContain(runtime.stage.root);
    expect((root.background as Color).getHexString()).toBe('12151a');
    expect(runtime.stage.grid).not.toBeNull();

    const firstRoot = runtime.stage.root;
    store.set({ backdrop: 'void' as Backdrop });
    expect(root.children).not.toContain(firstRoot);
    expect(root.children).toContain(runtime.stage.root);
    expect((root.background as Color).getHexString()).toBe('000000');
    expect(runtime.stage.grid).toBeNull();
    expect(runtime.stage.floor).toBeNull();

    store.set({ backdrop: 'light' as Backdrop, showGrid: false });
    expect((root.background as Color).getHexString()).toBe('eef1f5');
    expect(runtime.stage.floor).not.toBeNull();
    expect(runtime.stage.grid).toBeNull();

    runtime.dispose();
    runtime.dispose();
    expect(root.children).not.toContain(runtime.stage.root);
    expect(root.background).toBe(before);
  });
});
