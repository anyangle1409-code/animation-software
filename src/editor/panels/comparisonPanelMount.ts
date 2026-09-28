import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface ComparisonPanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface ComparisonPanelMount {
  dispose(): void;
}

/** Mount the first-party Pose A/B surface only while Compare owns the right slot. */
export function createComparisonPanelMount(
  slot: HTMLElement,
  factory: () => ComparisonPanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): ComparisonPanelMount {
  let panel: ComparisonPanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().rightTab === 'compare') {
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
