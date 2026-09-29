import type { HgScenePointerRouter } from './scenePointerRouter';
import type { ThreeSceneHost } from './threeSceneHost';

type SceneHostCamera = ThreeSceneHost['camera'];
type SceneHostScene = ThreeSceneHost['scene'];

export interface SceneHostBindings {
  camera: SceneHostCamera;
  scene: SceneHostScene;
  element: HTMLCanvasElement;
  pointers: HgScenePointerRouter;
}
