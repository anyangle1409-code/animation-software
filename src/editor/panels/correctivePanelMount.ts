import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface CorrectivePanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface CorrectivePanelMount {
  dispose(): void;
}

/** Mount the first-party Corrective editor only while Corrective owns the right-side slot. */
export function createCorrectivePanelMount(
  slot: HTMLElement,
  factory: () => CorrectivePanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): CorrectivePanelMount {
  let panel: CorrectivePanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().rightTab === 'correctives') {
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
