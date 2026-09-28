import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface ReviewPanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface ReviewPanelMount {
  dispose(): void;
}

/** Mount Review only while the right-side Review tab owns the panel slot. */
export function createReviewPanelMount(
  slot: HTMLElement,
  factory: () => ReviewPanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): ReviewPanelMount {
  let panel: ReviewPanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().rightTab === 'review') {
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
