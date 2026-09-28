import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface IKPanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface IKPanelMount {
  dispose(): void;
}

/** Mount the first-party IK editor only while IK & locks owns the left-side slot. */
export function createIKPanelMount(
  slot: HTMLElement,
  factory: () => IKPanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): IKPanelMount {
  let panel: IKPanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().leftTab === 'ik') {
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
