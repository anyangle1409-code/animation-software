import { HgPerspectiveCamera } from '../core/sceneGraph';
import {
  ACESFilmicToneMapping,
  PCFSoftShadowMap,
  PerspectiveCamera,
  Scene,
  SRGBColorSpace,
  WebGLRenderer,
} from './threeSceneBoundary';
import type { HgThreeRendererPort } from './threeSceneHost';

export interface HgThreeRendererAdapter {
  readonly port: HgThreeRendererPort;
  frame(): number;
}

/**
 * Final viewer vendor adapter.
 *
 * Camera state is owned by the first-party scene graph. This adapter mirrors
 * that state into a private Three camera only at draw time while the WebGL
 * renderer itself is still being replaced.
 */
export function createThreeRendererAdapter(
  canvas: HTMLCanvasElement,
): HgThreeRendererAdapter {
  const renderer = new WebGLRenderer({ canvas, antialias: true });
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = PCFSoftShadowMap;
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = ACESFilmicToneMapping;

  const camera = new PerspectiveCamera(38, 1, 0.05, 100);

  const syncCamera = (source: HgPerspectiveCamera) => {
    camera.fov = source.fov;
    camera.aspect = source.aspect;
    camera.near = source.near;
    camera.far = source.far;
    camera.position.set(source.position.x, source.position.y, source.position.z);
    camera.quaternion.set(
      source.quaternion.x,
      source.quaternion.y,
      source.quaternion.z,
      source.quaternion.w,
    );
    camera.scale.set(source.scale.x, source.scale.y, source.scale.z);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld(true);
  };

  return {
    port: {
      setPixelRatio: (value) => renderer.setPixelRatio(value),
      setSize: (width, height, updateStyle) =>
        renderer.setSize(width, height, updateStyle),
      render(scene: Scene, sourceCamera: HgPerspectiveCamera) {
        syncCamera(sourceCamera);
        renderer.render(scene, camera);
      },
      dispose: () => renderer.dispose(),
    },
    frame: () => renderer.info.render.frame,
  };
}
