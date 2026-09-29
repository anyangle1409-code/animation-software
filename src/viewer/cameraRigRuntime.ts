import type { CameraRecommendation } from '../exercises/types';
import type { BoneName } from '../rig/boneNames';
import type { CameraPresetId } from './cameraTypes';
import {
  StudioCameraRigController,
  type CameraOrbitPort,
  type CameraPort,
} from './cameraRigController';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';

export interface CameraRigState {
  camera: CameraPresetId;
  document: { exercise: { camera: CameraRecommendation } };
  selection: { bone: BoneName | null };
}

export interface CameraRigStorePort {
  getState(): CameraRigState;
  subscribe(listener: () => void): () => void;
}

export interface CameraRigRuntimeOptions {
  sceneState: SceneState;
  camera: CameraPort;
  store: CameraRigStorePort;
  controls(): CameraOrbitPort | null;
}

export interface CameraRigRuntime {
  dispose(): void;
}

/** Framework-neutral camera preset/focus lifecycle. */
export function createCameraRigRuntime(
  options: CameraRigRuntimeOptions,
): CameraRigRuntime {
  const { sceneState, camera, store, controls } = options;
  const controller = new StudioCameraRigController();

  let configuredPreset: CameraPresetId | null = null;
  let configuredRecommendation: CameraRecommendation | null = null;

  const configure = () => {
    const state = store.getState();
    if (
      state.camera === configuredPreset &&
      state.document.exercise.camera === configuredRecommendation
    ) {
      return;
    }
    configuredPreset = state.camera;
    configuredRecommendation = state.document.exercise.camera;
    controller.configure(configuredPreset, configuredRecommendation);
  };

  configure();
  const unsubscribeStore = store.subscribe(configure);

  const removeFrame = sceneState.consumers.add(({ delta }) => {
    const state = store.getState();
    controller.update({
      delta,
      preset: state.camera,
      selectedBone: state.selection.bone,
      evaluation: sceneState.evaluation,
      camera,
      controls: controls(),
    });
  }, SCENE_FRAME_PRIORITY.camera);

  let disposed = false;
  return {
    dispose() {
      if (disposed) return;
      disposed = true;
      removeFrame();
      unsubscribeStore();
    },
  };
}
