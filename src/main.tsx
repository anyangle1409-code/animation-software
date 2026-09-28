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
import { createEquipmentPanelDom } from './editor/panels/equipmentPanelDom';
import { createEquipmentPanelMount } from './editor/panels/equipmentPanelMount';
import { createCharacterPanelDom } from './editor/panels/characterPanelDom';
import { createCharacterPanelMount } from './editor/panels/characterPanelMount';
import { createJointPanelDom } from './editor/panels/jointPanelDom';
import { createJointPanelMount } from './editor/panels/jointPanelMount';
import { createGripPanelDom } from './editor/panels/gripPanelDom';
import { createGripPanelMount } from './editor/panels/gripPanelMount';
import { createCorrectivePanelDom } from './editor/panels/correctivePanelDom';
import { createCorrectivePanelMount } from './editor/panels/correctivePanelMount';
import { createGeneratePanelDom } from './editor/panels/generatePanelDom';
import { createGeneratePanelMount } from './editor/panels/generatePanelMount';
import { createReviewPanelDom } from './editor/panels/reviewPanelDom';
import { createReviewPanelMount } from './editor/panels/reviewPanelMount';
import { createExportPanelDom } from './editor/panels/exportPanelDom';
import { createExportPanelMount } from './editor/panels/exportPanelMount';
import { studioLayoutStore } from './editor/layoutState';
import { bindStudioKeyboard } from './editor/keyboardController';
import { createFirstPartyViewportDom } from './viewer/firstPartyViewportDom';
import './editor/styles.css';

const container = document.getElementById('root');
if (!container) throw new Error('Missing #root element');

const shell = createStudioAppShellDom();
const toolbar = createStudioToolbarDom();
shell.slots.toolbar.append(toolbar.element);
const timeline = createStudioTimelineDom();
shell.slots.timeline.append(timeline.element);

const viewport = createFirstPartyViewportDom();
shell.slots.viewport.append(viewport.element);

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
const equipmentPanelMount = createEquipmentPanelMount(
  shell.slots.leftPanel,
  () => createEquipmentPanelDom(),
  studioLayoutStore,
);

const characterPanelMount = createCharacterPanelMount(
  shell.slots.leftPanel,
  () => createCharacterPanelDom(),
  studioLayoutStore,
);

const jointPanelMount = createJointPanelMount(
  shell.slots.leftPanel,
  () => createJointPanelDom(),
  studioLayoutStore,
);

const gripPanelMount = createGripPanelMount(
  shell.slots.leftPanel,
  () => createGripPanelDom(),
  studioLayoutStore,
);

const correctivePanelMount = createCorrectivePanelMount(
  shell.slots.rightPanel,
  () => createCorrectivePanelDom(),
  studioLayoutStore,
);
const generatePanelMount = createGeneratePanelMount(
  shell.slots.rightPanel,
  () => createGeneratePanelDom(),
  studioLayoutStore,
);
const reviewPanelMount = createReviewPanelMount(
  shell.slots.rightPanel,
  () => createReviewPanelDom(),
  studioLayoutStore,
);

const exportPanelMount = createExportPanelMount(
  shell.slots.rightPanel,
  () => createExportPanelDom(),
  studioLayoutStore,
);

const unbindKeyboard = bindStudioKeyboard(window);
container.replaceChildren(shell.element);

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    unbindKeyboard();
    viewport.dispose();
    exportPanelMount.dispose();
    reviewPanelMount.dispose();
    generatePanelMount.dispose();
    correctivePanelMount.dispose();
    gripPanelMount.dispose();
    jointPanelMount.dispose();
    characterPanelMount.dispose();
    equipmentPanelMount.dispose();
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
  });
}
