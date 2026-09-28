import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Viewport } from '../viewer/Viewport';
import type { StudioAppShellDom } from './appShellDom';
import { bindStudioKeyboard } from './keyboardController';

export interface AppProps {
  shell: StudioAppShellDom;
}

/**
 * Temporary React child-surface bridge.
 *
 * The outer editor DOM is project-owned by appShellDom. React remains only
 * for active panels and the viewport adapter while those surfaces are
 * migrated independently.
 */
export function App({ shell }: AppProps) {
  useEffect(() => bindStudioKeyboard(window), []);

  return createPortal(<Viewport />, shell.slots.viewport);
}
