import { createContext, useContext } from 'react';
import { createSceneState } from './sceneStateCore';
import type { SceneState } from './sceneStateCore';

export type { SceneState } from './sceneStateCore';
export { createSceneState } from './sceneStateCore';

/**
 * Temporary React access wrapper around the framework-neutral scene state.
 *
 * Per-frame data is not React state: the pose changes sixty times a second
 * during playback and the mutable object avoids re-rendering the editor on each
 * frame. Remove only this wrapper when the production host no longer needs
 * React/R3F.
 */
export const SceneStateContext = createContext<SceneState | null>(null);

export function useSceneState(): SceneState {
  const state = useContext(SceneStateContext);
  if (!state) throw new Error('useSceneState must be used inside the studio canvas');
  return state;
}
