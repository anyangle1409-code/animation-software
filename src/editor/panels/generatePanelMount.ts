import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface GeneratePanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface GeneratePanelMount {
  dispose(): void;
}

/** Mount Generate only while the right-side Generate tab owns the panel slot. */
export function createGeneratePanelMount(
  slot: HTMLElement,
  factory: () => GeneratePanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): GeneratePanelMount {
  let panel: GeneratePanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().rightTab === 'generate') {
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
