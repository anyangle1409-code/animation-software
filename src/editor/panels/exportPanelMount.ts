import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface ExportPanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface ExportPanelMount {
  dispose(): void;
}

/** Mount the first-party Export workspace only while Export owns the right-side slot. */
export function createExportPanelMount(
  slot: HTMLElement,
  factory: () => ExportPanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): ExportPanelMount {
  let panel: ExportPanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().rightTab === 'export') {
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
