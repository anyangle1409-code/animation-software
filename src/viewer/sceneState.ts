import { createContext, useContext } from 'react';
import { PoseEvaluation } from '../rig/skeleton';
import type { ResolvedFrame } from '../animation/pipeline';
import { skeleton } from '../editor/store';

/**
 * Per-frame state shared by everything in the canvas.
 *
 * It is a mutable object rather than React state on purpose: the pose changes
 * sixty times a second during playback, and pushing that through React would
 * re-render the whole editor for every frame of animation.
 */
export interface SceneState {
  evaluation: PoseEvaluation;
  frame: ResolvedFrame | null;
}

export const createSceneState = (): SceneState => ({
  evaluation: new PoseEvaluation(skeleton),
  frame: null,
});

export const SceneStateContext = createContext<SceneState | null>(null);

export function useSceneState(): SceneState {
  const state = useContext(SceneStateContext);
  if (!state) throw new Error('useSceneState must be used inside the studio canvas');
  return state;
}
