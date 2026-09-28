import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface ExercisePanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface ExercisePanelMount {
  dispose(): void;
}

/** Mount the Exercise editor only while Exercise owns the right-side panel slot. */
export function createExercisePanelMount(
  slot: HTMLElement,
  factory: () => ExercisePanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): ExercisePanelMount {
  let panel: ExercisePanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().rightTab === 'exercise') {
      if (!panel) {
        panel = factory();
        slot.append(panel.element);
      }
    } else {
      unmount();
    }
  };

  const unsubscribe = layoutStore.subscribe(sync);
  sync();

  return {
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribe();
      unmount();
    },
  };
}
