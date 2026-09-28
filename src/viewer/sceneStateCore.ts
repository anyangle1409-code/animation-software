import type { ResolvedFrame } from '../animation/pipeline';
import { skeleton } from '../editor/store';
import { PoseEvaluation } from '../rig/skeleton';

/**
 * Renderer/framework-neutral mutable scene state.
 *
 * The resolved pose changes every animation frame, so this is deliberately a
 * plain mutable object rather than UI state. React/R3F currently expose it
 * through sceneState.ts; the first-party scene host can own this object
 * directly after parity gates pass.
 */
export interface SceneState {
  evaluation: PoseEvaluation;
  frame: ResolvedFrame | null;
}

export const createSceneState = (): SceneState => ({
  evaluation: new PoseEvaluation(skeleton),
  frame: null,
});
