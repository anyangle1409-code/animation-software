import type { Camera, Scene } from 'three';
import type { HgScenePointerRouter } from './scenePointerRouter';

export interface SceneHostBindings {
  camera: Camera;
  scene: Scene;
  element: HTMLCanvasElement;
  pointers: HgScenePointerRouter;
}
