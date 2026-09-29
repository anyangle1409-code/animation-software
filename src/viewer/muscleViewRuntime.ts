import { captureMuscleFrame } from './muscleFrameSnapshot';
import type { MuscleInvolvement } from '../exercises/types';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';
import { createMuscleScene, type MuscleSceneResources } from './muscleScene';

export interface MuscleViewState {
  document: { exercise: { muscles: MuscleInvolvement } };
}

export interface MuscleViewStorePort {
  getState(): MuscleViewState;
  subscribe(listener: () => void): () => void;
}

export interface MuscleViewRootPort {
  add(object: MuscleSceneResources['group']): unknown;
  remove(object: MuscleSceneResources['group']): unknown;
}

export interface MuscleViewRuntimeOptions {
  sceneState: SceneState;
  root: MuscleViewRootPort;
  store: MuscleViewStorePort;
}

export interface MuscleViewRuntime {
  readonly resources: MuscleSceneResources;
  dispose(): void;
}

/**
 * Framework-neutral live muscle-overlay controller.
 *
 * Owns resource rebuilds when the exercise changes, scene insertion, per-frame
 * anatomical transforms and deterministic disposal.
 */
export function createMuscleViewRuntime(
  options: MuscleViewRuntimeOptions,
): MuscleViewRuntime {
  const { sceneState, root, store } = options;

  let involvement = store.getState().document.exercise.muscles;
  let resources = createMuscleScene(involvement);
  root.add(resources.group);

  const rebuild = (next: MuscleInvolvement) => {
    root.remove(resources.group);
    resources.dispose();
    involvement = next;
    resources = createMuscleScene(involvement);
    root.add(resources.group);
  };

  const unsubscribeStore = store.subscribe(() => {
    const next = store.getState().document.exercise.muscles;
    if (next !== involvement) rebuild(next);
  });

  const removeFrame = sceneState.consumers.add(() => {
    const snapshot = captureMuscleFrame(sceneState.evaluation);
    for (const [id, transform] of snapshot) {
      const mesh = resources.meshes.get(id);
      if (!mesh) continue;
      mesh.position.set(...transform.position);
      mesh.quaternion.set(...transform.quaternion);
      mesh.scale.set(...transform.scale);
    }
  }, SCENE_FRAME_PRIORITY.muscle);

  let disposed = false;
  return {
    get resources() {
      return resources;
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      removeFrame();
      unsubscribeStore();
      root.remove(resources.group);
      resources.dispose();
    },
  };
}
