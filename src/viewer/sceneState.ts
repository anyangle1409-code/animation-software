import { createContext, useContext, useEffect, useRef } from 'react';
import type { HgFrameCallback } from '../core/frameLoop';
import type { SceneState } from './sceneStateCore';

export type { SceneState } from './sceneStateCore';
export { createSceneState, SCENE_FRAME_PRIORITY } from './sceneStateCore';

export const SceneStateContext = createContext<SceneState | null>(null);

export function useSceneState(): SceneState {
  const state = useContext(SceneStateContext);
  if (!state) throw new Error('useSceneState must be used inside the studio canvas');
  return state;
}

/**
 * Register a visual consumer with the project-owned frame dispatcher.
 *
 * The callback ref changes without re-registering, so React updates can change
 * inputs without changing deterministic frame ordering.
 */
export function useSceneFrame(callback: HgFrameCallback, priority = 0): void {
  const scene = useSceneState();
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(
    () => scene.consumers.add((frame) => callbackRef.current(frame), priority),
    [scene, priority],
  );
}
