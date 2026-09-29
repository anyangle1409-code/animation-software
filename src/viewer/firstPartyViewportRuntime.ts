import { browserFrameScheduler } from '../core/frameLoop';
import { browserSceneSurface } from '../core/browserSceneSurface';
import { currentAnchors, skeleton, studioStore } from '../editor/storeCore';
import type { SceneState } from './sceneStateCore';
import { driveSceneFrame } from './sceneFrameDriver';
import type { SceneHostBindings } from './sceneHostTypes';
import { HgScenePointerRouter } from './scenePointerRouter';
import { ThreeSceneHost } from './threeSceneHost';
import { createThreeRendererAdapter } from './threeRendererAdapter';

export interface FirstPartyViewportRuntime {
  bindings: SceneHostBindings;
  dispose(): void;
}

/**
 * Framework-neutral live viewport runtime.
 *
 * React currently mounts the DOM nodes and scene-content adapters, but it no
 * longer owns the renderer, frame loop, clip tracking, pointer router or host
 * disposal semantics.
 */
export function createFirstPartyViewportRuntime(
  container: HTMLElement,
  canvas: HTMLCanvasElement,
  scene: SceneState,
): FirstPartyViewportRuntime {
  const renderer = createThreeRendererAdapter(canvas);

  const host = new ThreeSceneHost(
    browserFrameScheduler(),
    browserSceneSurface(canvas, container),
    renderer.port,
  );

  const pointers = new HgScenePointerRouter(
    host.camera,
    host.scene,
    canvas,
    () => studioStore.getState().selectBone(null),
  );
  pointers.mount();

  let activeClip = studioStore.getState().document.clip;
  let anchors = currentAnchors(activeClip);
  let frameCount = 0;

  const removeFrame = host.onFrame((frame) => {
    const playback = studioStore.getState();
    if (playback.document.clip !== activeClip) {
      activeClip = playback.document.clip;
      anchors = currentAnchors(activeClip);
    }

    driveSceneFrame({
      scene,
      skeleton,
      clip: activeClip,
      anchors,
      playback,
      frame,
    });

    frameCount += 1;
    canvas.dataset.hgptFrameCount = String(frameCount);
    canvas.dataset.hgptSceneChildren = String(host.scene.children.length);
    canvas.dataset.hgptCameraPosition = host.camera.position
      .toArray()
      .map((value) => value.toFixed(6))
      .join(',');
    canvas.dataset.hgptCameraQuaternion = host.camera.quaternion
      .toArray()
      .map((value) => value.toFixed(6))
      .join(',');
    canvas.dataset.hgptRendererFrame = String(renderer.frame());
    canvas.dataset.hgptSceneNames = host.scene.children
      .map((child) => child.name || child.type)
      .join('|');
  }, -1);

  const bindings: SceneHostBindings = {
    camera: host.camera,
    scene: host.scene,
    element: canvas,
    pointers,
  };

  host.mount();

  let disposed = false;
  return {
    bindings,
    dispose() {
      if (disposed) return;
      disposed = true;
      removeFrame();
      pointers.dispose();
      host.dispose();
    },
  };
}
