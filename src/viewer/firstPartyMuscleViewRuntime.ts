import type { MuscleInvolvement } from '../exercises/types';
import type { HgObject3D } from '../core/sceneGraph';
import { captureMuscleFrame } from './muscleFrameSnapshot';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';
import {
  applyHgMuscleFrame,
  createHgMuscleScene,
  type HgMuscleSceneResources,
} from './firstPartyMuscleScene';

export interface FirstPartyMuscleViewState {
  document: { exercise: { muscles: MuscleInvolvement } };
}
export interface FirstPartyMuscleViewStorePort {
  getState(): FirstPartyMuscleViewState;
  subscribe(listener: () => void): () => void;
}
export interface FirstPartyMuscleViewRuntime {
  readonly resources: HgMuscleSceneResources;
  dispose(): void;
}

export function createFirstPartyMuscleViewRuntime(options: {
  sceneState: SceneState;
  root: Pick<HgObject3D, 'add' | 'remove'>;
  store: FirstPartyMuscleViewStorePort;
}): FirstPartyMuscleViewRuntime {
  const { sceneState, root, store } = options;
  let involvement = store.getState().document.exercise.muscles;
  let resources = createHgMuscleScene(involvement);
  root.add(resources.group);

  const rebuild = (next: MuscleInvolvement) => {
    root.remove(resources.group);
    resources.dispose();
    involvement = next;
    resources = createHgMuscleScene(involvement);
    root.add(resources.group);
  };
  const unsubscribeStore = store.subscribe(() => {
    const next = store.getState().document.exercise.muscles;
    if (next !== involvement) rebuild(next);
  });
  const removeFrame = sceneState.consumers.add(() => {
    applyHgMuscleFrame(resources, captureMuscleFrame(sceneState.evaluation));
  }, SCENE_FRAME_PRIORITY.muscle);

  let disposed = false;
  return {
    get resources() { return resources; },
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
