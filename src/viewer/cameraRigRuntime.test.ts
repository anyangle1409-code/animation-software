import { PerspectiveCamera, Vector3 } from 'three';
import { describe, expect, it, vi } from 'vitest';
import type { CameraRecommendation } from '../exercises/types';
import type { CameraPresetId } from './cameraTypes';
import { createSceneState } from './sceneStateCore';
import {
  createCameraRigRuntime,
  type CameraRigState,
  type CameraRigStorePort,
} from './cameraRigRuntime';

function createStore(initial: CameraRigState): CameraRigStorePort & {
  setCamera(camera: CameraPresetId, recommendation?: CameraRecommendation): void;
} {
  let state = initial;
  const listeners = new Set<() => void>();
  return {
    getState: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    setCamera(camera, recommendation) {
      state = {
        ...state,
        camera,
        document: {
          exercise: {
            camera: recommendation ?? state.document.exercise.camera,
          },
        },
      };
      for (const listener of [...listeners]) listener();
    },
  };
}

describe('framework-neutral camera rig runtime', () => {
  it('subscribes to camera state, updates on frames and disposes', () => {
    const camera = new PerspectiveCamera(38, 1, 0.05, 100);
    camera.position.set(2.3, 1.35, 2.7);
    const sceneState = createSceneState();
    const recommendation: CameraRecommendation = {
      preset: 'threeQuarter',
    };
    const store = createStore({
      camera: 'front',
      document: { exercise: { camera: recommendation } },
      selection: { bone: null },
    });
    const target = new Vector3(0, 1, 0);
    const update = vi.fn();
    const controls = { target, update };

    const runtime = createCameraRigRuntime({
      sceneState,
      camera,
      store,
      controls: () => controls,
    });

    expect(sceneState.consumers.subscriberCount).toBe(1);
    const before = camera.position.clone();
    sceneState.consumers.dispatch({ delta: 0.2, elapsed: 1, timestampMs: 1000 });
    expect(update).toHaveBeenCalled();
    expect(camera.position.distanceTo(before)).toBeGreaterThan(0);

    update.mockClear();
    store.setCamera('side');
    sceneState.consumers.dispatch({ delta: 0.2, elapsed: 2, timestampMs: 2000 });
    expect(update).toHaveBeenCalled();

    runtime.dispose();
    runtime.dispose();
    expect(sceneState.consumers.subscriberCount).toBe(0);
  });
});
