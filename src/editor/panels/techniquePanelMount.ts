import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface TechniquePanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface TechniquePanelMount {
  dispose(): void;
}

/**
 * Mirrors the React panel mount lifecycle: the Technique surface exists only
 * while the Technique tab is active. This prevents detached/background
 * validation work when another panel owns the right-side slot.
 */
export function createTechniquePanelMount(
  slot: HTMLElement,
  factory: () => TechniquePanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): TechniquePanelMount {
  let panel: TechniquePanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    const active = layoutStore.getState().rightTab === 'technique';
    if (active) {
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
