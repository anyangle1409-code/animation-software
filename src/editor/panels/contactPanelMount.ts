import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface ContactPanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface ContactPanelMount {
  dispose(): void;
}

/** Mount Contact diagnostics only while Contacts owns the left-side panel slot. */
export function createContactPanelMount(
  slot: HTMLElement,
  factory: () => ContactPanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): ContactPanelMount {
  let panel: ContactPanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().leftTab === 'contacts') {
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
