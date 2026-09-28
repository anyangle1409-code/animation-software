import { useEffect } from 'react';
import { bindStudioKeyboard } from './keyboardController';

/**
 * Temporary React keyboard-lifetime bridge.
 *
 * All visible editor and viewport surfaces are now project-owned DOM/lifecycle
 * code. This component remains only until the React root is removed.
 */
export function App() {
  useEffect(() => bindStudioKeyboard(window), []);
  return null;
}
