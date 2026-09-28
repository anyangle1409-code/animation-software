import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface MusclePanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface MusclePanelMount {
  dispose(): void;
}

/**
 * Mirrors the former React mount lifecycle: the Muscle diagnostics surface
 * exists only while the Muscles tab is active, so its local filters reset on
 * remount and no hidden diagnostics keep subscribing in the background.
 */
export function createMusclePanelMount(
  slot: HTMLElement,
  factory: () => MusclePanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): MusclePanelMount {
  let panel: MusclePanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    const active = layoutStore.getState().rightTab === 'muscles';
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
