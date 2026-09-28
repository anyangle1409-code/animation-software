import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './editor/App';
import { createStudioAppShellDom } from './editor/appShellDom';
import { createStudioToolbarDom } from './editor/toolbarDom';
import { createStudioTimelineDom } from './editor/timelineDom';
import { createTechniquePanelDom } from './editor/panels/techniquePanelDom';
import { studioLayoutStore } from './editor/layoutState';
import './editor/styles.css';

const container = document.getElementById('root');
if (!container) throw new Error('Missing #root element');

const shell = createStudioAppShellDom();
const toolbar = createStudioToolbarDom();
shell.slots.toolbar.append(toolbar.element);
const timeline = createStudioTimelineDom();
shell.slots.timeline.append(timeline.element);

const techniquePanel = createTechniquePanelDom();
const syncTechniquePanel = () => {
  const active = studioLayoutStore.getState().rightTab === 'technique';
  if (active) {
    if (techniquePanel.element.parentElement !== shell.slots.rightPanel) {
      shell.slots.rightPanel.append(techniquePanel.element);
    }
  } else if (techniquePanel.element.parentElement === shell.slots.rightPanel) {
    techniquePanel.element.remove();
  }
};
const unsubscribeTechniquePanel = studioLayoutStore.subscribe(syncTechniquePanel);
syncTechniquePanel();

const reactBridge = document.createElement('div');
reactBridge.dataset.hgptReactBridge = 'editor-children';
reactBridge.style.display = 'contents';

container.replaceChildren(shell.element, reactBridge);

const root = createRoot(reactBridge);
root.render(
  <StrictMode>
    <App shell={shell} />
  </StrictMode>,
);

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    root.unmount();
    unsubscribeTechniquePanel();
    techniquePanel.dispose();
    techniquePanel.element.remove();
    timeline.dispose();
    toolbar.dispose();
    shell.dispose();
    shell.element.remove();
    reactBridge.remove();
  });
}
