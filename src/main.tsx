import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './editor/App';
import { createStudioAppShellDom } from './editor/appShellDom';
import './editor/styles.css';

const container = document.getElementById('root');
if (!container) throw new Error('Missing #root element');

const shell = createStudioAppShellDom();
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
    shell.dispose();
    shell.element.remove();
    reactBridge.remove();
  });
}
