import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './editor/App';
import { createStudioAppShellDom } from './editor/appShellDom';
import { createStudioToolbarDom } from './editor/toolbarDom';
import { createStudioTimelineDom } from './editor/timelineDom';
import { createTechniquePanelDom } from './editor/panels/techniquePanelDom';
import { createTechniquePanelMount } from './editor/panels/techniquePanelMount';
import { createMusclePanelDom } from './editor/panels/musclePanelDom';
import { createMusclePanelMount } from './editor/panels/musclePanelMount';
import { studioLayoutStore } from './editor/layoutState';
import './editor/styles.css';

const container = document.getElementById('root');
if (!container) throw new Error('Missing #root element');

const shell = createStudioAppShellDom();
const toolbar = createStudioToolbarDom();
shell.slots.toolbar.append(toolbar.element);
const timeline = createStudioTimelineDom();
shell.slots.timeline.append(timeline.element);

const techniquePanelMount = createTechniquePanelMount(
  shell.slots.rightPanel,
  () => createTechniquePanelDom(),
  studioLayoutStore,
);
const musclePanelMount = createMusclePanelMount(
  shell.slots.rightPanel,
  () => createMusclePanelDom(),
  studioLayoutStore,
);

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
    musclePanelMount.dispose();
    techniquePanelMount.dispose();
    timeline.dispose();
    toolbar.dispose();
    shell.dispose();
    shell.element.remove();
    reactBridge.remove();
  });
}
