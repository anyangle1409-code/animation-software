import type { HgPerspectiveCamera, HgScene } from '../core/sceneGraph';
import type { HgScenePointerRouter } from './scenePointerRouter';

export interface FirstPartySceneHostBindings {
  camera: HgPerspectiveCamera;
  scene: HgScene;
  element: HTMLCanvasElement;
  pointers: HgScenePointerRouter;
}
