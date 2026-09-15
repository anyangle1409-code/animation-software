import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './editor/App';
import { registerBundledCharacters } from './character/bundled';
import { useCharacter } from './editor/characterStore';
import './editor/styles.css';

const container = document.getElementById('root');
if (!container) throw new Error('Missing #root element');

// The bundled characters are registered before the studio renders. Registering
// them is not quite enough on its own: the character store captures the default
// source id when its module is first evaluated, which has already happened by
// the time an asset probe can finish, so the choice is made explicitly here.
// A missing asset resolves to an empty list and the built-in character stays.
void registerBundledCharacters()
  .then((registered) => {
    const preferred = registered.includes('baseline-dressed') ? 'baseline-dressed' : registered[0];
    if (preferred) useCharacter.getState().setSource(preferred);
  })
  .finally(() => {
    createRoot(container).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
  });
