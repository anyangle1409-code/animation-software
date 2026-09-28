import { BoxGeometry, Mesh, MeshNormalMaterial, WebGLRenderer } from 'three';
import { generateClip } from '../src/animation/generate';
import { bicepCurl } from '../src/exercises/definitions/bicepCurl';
import { browserFrameScheduler } from '../src/core/frameLoop';
import { browserSceneSurface } from '../src/core/browserSceneSurface';
import { canonicalSkeleton } from '../src/rig/skeleton';
import { createSceneState } from '../src/viewer/sceneStateCore';
import { driveSceneFrame } from '../src/viewer/sceneFrameDriver';
import { createStudioStage } from '../src/viewer/studioStage';
import { BACKDROPS } from '../src/editor/store';
import { ThreeSceneHost } from '../src/viewer/threeSceneHost';

/**
 * Browser-smoke-only real WebGL fixture for the first-party scene host.
 *
 * It deliberately lives outside src/ so production source/import inventories
 * are unchanged. The Vite smoke server transforms it only when the browser
 * verification explicitly imports it.
 *
 * Unlike the earlier spinning-cube probe, this drives the real bicep-curl clip
 * through the renderer-neutral scene-frame driver and project-owned stage.
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

  const stage = createStudioStage(BACKDROPS.studio, true);
  host.scene.background = stage.background;
  host.scene.add(stage.root);

  const geometry = new BoxGeometry(0.12, 0.3, 0.12);
  const material = new MeshNormalMaterial();
  const cube = new Mesh(geometry, material);
  cube.matrixAutoUpdate = false;
  host.scene.add(cube);

  const sceneState = createSceneState();
  const clip = generateClip(canonicalSkeleton, bicepCurl);
  const playback = {
    time: 0,
    playing: true,
    loop: true,
    speed: 1,
    loopRange: null,
    setTime(time) {
      this.time = time;
    },
    pause() {
      this.playing = false;
    },
  };

  const removeConsumer = sceneState.consumers.add(() => {
    cube.matrix.copy(sceneState.evaluation.matrix('forearm_l'));
    cube.matrixWorldNeedsUpdate = true;
  }, 10);

  const removeFrame = host.onFrame((frame) => {
    driveSceneFrame({
      scene: sceneState,
      skeleton: canonicalSkeleton,
      clip,
      playback,
      frame,
    });
  }, -100);

  host.mount();

  return {
    canvas,
    host,
    getState() {
      return {
        playbackTime: playback.time,
        frameTime: sceneState.frame?.time ?? null,
        forearmMatrix: [...sceneState.evaluation.matrix('forearm_l').elements],
      };
    },
    dispose() {
      removeFrame();
      removeConsumer();
      host.scene.remove(cube);
      host.scene.remove(stage.root);
      geometry.dispose();
      material.dispose();
      stage.dispose();
      host.dispose();
      canvas.remove();
    },
  };
}
