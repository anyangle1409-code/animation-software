import type { ResolvedFrame } from '../animation/pipeline';
import { HgFrameDispatcher } from '../core/frameLoop';
import { skeleton } from '../editor/store';
import { PoseEvaluation } from '../rig/skeleton';

export const SCENE_FRAME_PRIORITY = {
  bone: 10,
  character: 10,
  muscle: 10,
  equipment: 20,
  ik: 20,
  proxy: 30,
  orbit: 40,
  camera: 50,
  gizmo: 60,
} as const;

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
  consumers: HgFrameDispatcher;
}

export const createSceneState = (): SceneState => ({
  evaluation: new PoseEvaluation(skeleton),
  frame: null,
  consumers: new HgFrameDispatcher(),
});
