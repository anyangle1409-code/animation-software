import type { ObservableStore } from '../core/observableStore';
import {
  studioLayoutStore,
  type LeftTab,
  type RightTab,
  type StudioLayoutState,
} from './layoutState';

type LayoutStorePort = Pick<ObservableStore<StudioLayoutState>, 'getState' | 'subscribe'>;

export const LEFT_SHELL_TABS: ReadonlyArray<{ id: LeftTab; label: string }> = [
  { id: 'joint', label: 'Joint' },
  { id: 'grip', label: 'Grip' },
  { id: 'ik', label: 'IK & locks' },
  { id: 'contacts', label: 'Contacts' },
  { id: 'equipment', label: 'Equipment' },
  { id: 'character', label: 'Character' },
];

export const RIGHT_SHELL_TABS: ReadonlyArray<{ id: RightTab; label: string }> = [
  { id: 'generate', label: 'Generate' },
  { id: 'exercise', label: 'Exercise' },
  { id: 'muscles', label: 'Muscles' },
  { id: 'technique', label: 'Technique' },
  { id: 'correctives', label: 'Correctives' },
  { id: 'compare', label: 'Compare' },
  { id: 'review', label: 'Review' },
  { id: 'export', label: 'Export' },
];

export interface StudioAppShellSlots {
  toolbar: HTMLDivElement;
  leftPanel: HTMLDivElement;
  viewport: HTMLElement;
  rightPanel: HTMLDivElement;
  timeline: HTMLDivElement;
}

export interface StudioAppShellControls {
  leftTabs: Record<LeftTab, HTMLButtonElement>;
  rightTabs: Record<RightTab, HTMLButtonElement>;
  panelToggle: HTMLButtonElement;
}

export interface StudioAppShellDom {
  element: HTMLDivElement;
  slots: StudioAppShellSlots;
  controls: StudioAppShellControls;
  dispose(): void;
}

const setSlot = (element: HTMLElement, slot: string): void => {
  element.dataset.hgptEditorSlot = slot;
};

const createTabButton = (
  documentRef: Pick<Document, 'createElement'>,
  label: string,
  onClick: () => void,
  cleanups: Array<() => void>,
): HTMLButtonElement => {
  const button = documentRef.createElement('button');
  button.type = 'button';
  button.textContent = label;
  button.addEventListener('click', onClick);
  cleanups.push(() => button.removeEventListener('click', onClick));
  return button;
};

/**
 * Project-owned DOM structure and layout-state binding for the Studio shell.
 *
 * This owns the live outer editor structure. During React migration, the
 * existing child surfaces mount into these slots without changing their
 * behavior or state ownership.
 */
export function createStudioAppShellDom(
  documentRef: Pick<Document, 'createElement'> = document,
  layoutStore: LayoutStorePort = studioLayoutStore,
): StudioAppShellDom {
  const cleanups: Array<() => void> = [];

  const root = documentRef.createElement('div');
  root.className = 'studio';
  root.dataset.hgptEditorShell = 'first-party';

  const toolbar = documentRef.createElement('div');
  setSlot(toolbar, 'toolbar');

  const body = documentRef.createElement('div');
  body.className = 'studio__body';

  const leftSide = documentRef.createElement('aside');
  leftSide.className = 'studio__side studio__side--left';
  const leftNav = documentRef.createElement('nav');
  leftNav.className = 'tabs';
  const leftPanel = documentRef.createElement('div');
  leftPanel.className = 'studio__side-body';
  setSlot(leftPanel, 'left-panel');

  const leftTabs = {} as Record<LeftTab, HTMLButtonElement>;
  for (const tab of LEFT_SHELL_TABS) {
    const button = createTabButton(
      documentRef,
      tab.label,
      () => layoutStore.getState().setLeftTab(tab.id),
      cleanups,
    );
    leftTabs[tab.id] = button;
    leftNav.append(button);
  }
  leftSide.append(leftNav, leftPanel);

  const viewport = documentRef.createElement('main');
  viewport.className = 'studio__viewport';

  const viewportSlot = documentRef.createElement('div');
  viewportSlot.className = 'studio__viewport-slot';
  setSlot(viewportSlot, 'viewport');

  const panelToggle = documentRef.createElement('button');
  panelToggle.type = 'button';
  panelToggle.className = 'studio__panel-toggle';
  const togglePanels = () => layoutStore.getState().togglePanels();
  panelToggle.addEventListener('click', togglePanels);
  cleanups.push(() => panelToggle.removeEventListener('click', togglePanels));
  viewport.append(viewportSlot, panelToggle);

  const rightSide = documentRef.createElement('aside');
  rightSide.className = 'studio__side studio__side--right';
  const rightNav = documentRef.createElement('nav');
  rightNav.className = 'tabs';
  const rightPanel = documentRef.createElement('div');
  rightPanel.className = 'studio__side-body';
  setSlot(rightPanel, 'right-panel');

  const rightTabs = {} as Record<RightTab, HTMLButtonElement>;
  for (const tab of RIGHT_SHELL_TABS) {
    const button = createTabButton(
      documentRef,
      tab.label,
      () => layoutStore.getState().setRightTab(tab.id),
      cleanups,
    );
    rightTabs[tab.id] = button;
    rightNav.append(button);
  }
  rightSide.append(rightNav, rightPanel);

  body.append(leftSide, viewport, rightSide);

  const timeline = documentRef.createElement('div');
  setSlot(timeline, 'timeline');

  root.append(toolbar, body, timeline);

  const sync = () => {
    const state = layoutStore.getState();
    root.classList.toggle('studio--focus', !state.panelsOpen);
    for (const tab of LEFT_SHELL_TABS) {
      leftTabs[tab.id].classList.toggle('is-active', state.leftTab === tab.id);
    }
    for (const tab of RIGHT_SHELL_TABS) {
      rightTabs[tab.id].classList.toggle('is-active', state.rightTab === tab.id);
    }
    panelToggle.textContent = state.panelsOpen ? 'Hide panels' : 'Show panels';
  };

  const unsubscribe = layoutStore.subscribe(sync);
  sync();

  let disposed = false;
  return {
    element: root,
    slots: { toolbar, leftPanel, viewport: viewportSlot, rightPanel, timeline },
    controls: { leftTabs, rightTabs, panelToggle },
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribe();
      for (const cleanup of cleanups.splice(0)) cleanup();
    },
  };
}
