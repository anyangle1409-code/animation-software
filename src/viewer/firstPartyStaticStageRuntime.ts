import { BACKDROPS, type Backdrop } from '../editor/storeCore';
import type { HgScene } from '../core/sceneGraph';
import {
  createHgStudioStage,
  type HgStudioStageResources,
} from './firstPartyStudioStage';

export interface FirstPartyStaticStageState {
  backdrop: Backdrop;
  showGrid: boolean;
}
export interface FirstPartyStaticStageStorePort {
  getState(): FirstPartyStaticStageState;
  subscribe(listener: () => void): () => void;
}
export interface FirstPartyStaticStageRuntime {
  readonly stage: HgStudioStageResources;
  dispose(): void;
}

export function createFirstPartyStaticStageRuntime(
  root: Pick<HgScene, 'background' | 'add' | 'remove'>,
  store: FirstPartyStaticStageStorePort,
): FirstPartyStaticStageRuntime {
  const previousBackground = root.background;
  let state = store.getState();
  let stage = createHgStudioStage(BACKDROPS[state.backdrop], state.showGrid);
  root.background = stage.background;
  root.add(stage.root);

  const rebuild = (next: FirstPartyStaticStageState) => {
    root.remove(stage.root);
    stage.dispose();
    state = next;
    stage = createHgStudioStage(BACKDROPS[state.backdrop], state.showGrid);
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
    get stage() { return stage; },
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
