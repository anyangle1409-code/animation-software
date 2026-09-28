import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface EquipmentPanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface EquipmentPanelMount {
  dispose(): void;
}

/** Mount the first-party Equipment editor only while Equipment owns the left-side slot. */
export function createEquipmentPanelMount(
  slot: HTMLElement,
  factory: () => EquipmentPanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): EquipmentPanelMount {
  let panel: EquipmentPanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().leftTab === 'equipment') {
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
