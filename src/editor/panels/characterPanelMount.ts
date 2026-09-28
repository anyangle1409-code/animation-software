import type { ObservableStore } from '../../core/observableStore';
import {
  studioLayoutStore,
  type StudioLayoutState,
} from '../layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export interface CharacterPanelSurface {
  element: HTMLElement;
  dispose(): void;
}

export interface CharacterPanelMount {
  dispose(): void;
}

/** Mount the first-party Character editor only while Character owns the left-side slot. */
export function createCharacterPanelMount(
  slot: HTMLElement,
  factory: () => CharacterPanelSurface,
  layoutStore: LayoutStorePort = studioLayoutStore,
): CharacterPanelMount {
  let panel: CharacterPanelSurface | null = null;
  let disposed = false;

  const unmount = () => {
    if (!panel) return;
    panel.dispose();
    panel.element.remove();
    panel = null;
  };

  const sync = () => {
    if (disposed) return;
    if (layoutStore.getState().leftTab === 'character') {
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
