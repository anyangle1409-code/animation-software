import { BACKDROPS, type Backdrop } from '../editor/storeCore';
import { createStudioStage, type StudioStageResources } from './studioStage';

export interface StaticStageState {
  backdrop: Backdrop;
  showGrid: boolean;
}

export interface StaticStageStorePort {
  getState(): StaticStageState;
  subscribe(listener: () => void): () => void;
}

export interface StaticStageRuntime {
  readonly stage: StudioStageResources;
  dispose(): void;
}

export interface StaticStageRootPort {
  background: unknown;
  add(object: StudioStageResources['root']): unknown;
  remove(object: StudioStageResources['root']): unknown;
}

/**
 * Framework-neutral Studio stage controller.
 *
 * Owns background/light/floor/grid replacement from store state and restores
 * the host scene's prior background on disposal.
 */
export function createStaticStageRuntime(
  root: StaticStageRootPort,
  store: StaticStageStorePort,
): StaticStageRuntime {
  const previousBackground = root.background;
  let state = store.getState();
  let stage = createStudioStage(BACKDROPS[state.backdrop], state.showGrid);

  root.background = stage.background;
  root.add(stage.root);

  const rebuild = (next: StaticStageState) => {
    root.remove(stage.root);
    stage.dispose();
    state = next;
    stage = createStudioStage(BACKDROPS[state.backdrop], state.showGrid);
    root.background = stage.background;
    root.add(stage.root);
  };

  const unsubscribe = store.subscribe(() => {
    const next = store.getState();
    if (next.backdrop === state.backdrop && next.showGrid === state.showGrid) return;
    rebuild(next);
  });

  let disposed = false;
  return {
    get stage() {
      return stage;
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribe();
      root.remove(stage.root);
      if (root.background === stage.background) root.background = previousBackground;
      stage.dispose();
    },
  };
}
