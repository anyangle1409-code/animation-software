import { createStore } from '../core/observableStore';
import { bindReactStore } from '../core/store';

export type LeftTab = 'joint' | 'grip' | 'ik' | 'contacts' | 'equipment' | 'character';
export type RightTab =
  | 'generate'
  | 'exercise'
  | 'muscles'
  | 'technique'
  | 'correctives'
  | 'compare'
  | 'review'
  | 'export';

export interface StudioLayoutState {
  leftTab: LeftTab;
  rightTab: RightTab;
  panelsOpen: boolean;
  setLeftTab(tab: LeftTab): void;
  setRightTab(tab: RightTab): void;
  setPanelsOpen(open: boolean): void;
  togglePanels(): void;
}

export const studioLayoutStore = createStore<StudioLayoutState>((set, get) => ({
  leftTab: 'joint',
  rightTab: 'exercise',
  panelsOpen: true,
  setLeftTab: (leftTab) => set({ leftTab }),
  setRightTab: (rightTab) => set({ rightTab }),
  setPanelsOpen: (panelsOpen) => set({ panelsOpen }),
  togglePanels: () => set({ panelsOpen: !get().panelsOpen }),
}));

/** Temporary React adapter while the editor chrome still renders through React. */
export const useStudioLayout = bindReactStore(studioLayoutStore);
