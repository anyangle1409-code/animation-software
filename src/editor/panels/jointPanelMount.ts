import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface JointPanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface JointPanelMount {
  dispose(): void;
}

/** Mount the first-party Joint editor only while Joint owns the left-side slot. */
export function createJointPanelMount(
  slot: HTMLElement,
  factory: () => JointPanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): JointPanelMount {
  let panel: JointPanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().leftTab === 'joint') {
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
