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
import { createComparisonPanelDom } from './editor/panels/comparisonPanelDom';
import { createComparisonPanelMount } from './editor/panels/comparisonPanelMount';
import { createContactPanelDom } from './editor/panels/contactPanelDom';
import { createContactPanelMount } from './editor/panels/contactPanelMount';
import { createExercisePanelDom } from './editor/panels/exercisePanelDom';
import { createExercisePanelMount } from './editor/panels/exercisePanelMount';
import { createIKPanelDom } from './editor/panels/ikPanelDom';
import { createIKPanelMount } from './editor/panels/ikPanelMount';
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
const comparisonPanelMount = createComparisonPanelMount(
  shell.slots.rightPanel,
  () => createComparisonPanelDom(),
  studioLayoutStore,
);
const contactPanelMount = createContactPanelMount(
  shell.slots.leftPanel,
  () => createContactPanelDom(),
  studioLayoutStore,
);
const exercisePanelMount = createExercisePanelMount(
  shell.slots.rightPanel,
  () => createExercisePanelDom(),
  studioLayoutStore,
);
const ikPanelMount = createIKPanelMount(
  shell.slots.leftPanel,
  () => createIKPanelDom(),
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
    ikPanelMount.dispose();
    exercisePanelMount.dispose();
    contactPanelMount.dispose();
    comparisonPanelMount.dispose();
    musclePanelMount.dispose();
    techniquePanelMount.dispose();
    timeline.dispose();
    toolbar.dispose();
    shell.dispose();
    shell.element.remove();
    reactBridge.remove();
  });
}
