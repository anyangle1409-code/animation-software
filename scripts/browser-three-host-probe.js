import { BoxGeometry, Mesh, MeshNormalMaterial, WebGLRenderer } from 'three';
import { browserFrameScheduler } from '../src/core/frameLoop';
import { browserSceneSurface } from '../src/core/browserSceneSurface';
import { ThreeSceneHost } from '../src/viewer/threeSceneHost';

/**
 * Browser-smoke-only real WebGL fixture for the first-party scene host.
 *
 * It deliberately lives outside src/ so production source/import inventories
 * are unchanged. The Vite smoke server transforms it only when the browser
 * verification explicitly imports it.
 */
export function mountBrowserThreeHostProbe(container) {
  const canvas = document.createElement('canvas');
  canvas.dataset.hgptThreeHostProbe = 'true';
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvas.style.display = 'block';
  container.appendChild(canvas);

  const renderer = new WebGLRenderer({ canvas, antialias: true });
  const host = new ThreeSceneHost(
    browserFrameScheduler(),
    browserSceneSurface(canvas, container),
    renderer,
  );

  const geometry = new BoxGeometry(0.9, 0.9, 0.9);
  const material = new MeshNormalMaterial();
  const cube = new Mesh(geometry, material);
  host.scene.add(cube);

  const removeFrame = host.onFrame(({ elapsed }) => {
    cube.rotation.set(elapsed * 0.8, elapsed * 1.1, elapsed * 0.35);
    cube.updateMatrixWorld(true);
  }, 100);

  host.mount();

  return {
    canvas,
    host,
    dispose() {
      removeFrame();
      host.scene.remove(cube);
      geometry.dispose();
      material.dispose();
      host.dispose();
      canvas.remove();
    },
  };
}
