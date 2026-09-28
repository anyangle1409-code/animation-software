import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface GripPanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface GripPanelMount {
  dispose(): void;
}

/** Mount the first-party Grip editor only while Grip owns the left-side slot. */
export function createGripPanelMount(
  slot: HTMLElement,
  factory: () => GripPanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): GripPanelMount {
  let panel: GripPanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().leftTab === 'grip') {
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
