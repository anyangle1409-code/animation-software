import { browserFrameScheduler } from '../core/frameLoop';
import { browserSceneSurface } from '../core/browserSceneSurface';
import { HgSceneLifecycle } from '../core/sceneLifecycle';
import { currentAnchors, skeleton, studioStore } from '../editor/storeCore';
import { driveSceneFrame } from './sceneFrameDriver';
import type { SceneState } from './sceneStateCore';
import {
  createFirstPartyWebGL2BoneRenderer,
  packBoneSegments,
} from './firstPartyWebGL2SkeletonPreview.mjs';

export interface NativeSkeletonPreview {
  dispose(): void;
}

/**
 * Opt-in, native browser-WebGL2 preview of REAL posed FK skeletal endpoints.
 *
 * Independence boundary: no import of threeSceneBoundary, ThreeSceneHost or
 * WebGLRenderer. Does not instantiate the production 3D scene controller,
 * materials, anatomy meshes, skin, picking or overlays. These remain on the
 * current supported viewer until separately verified.
 */
export function createNativeWebGL2SkeletonPreview(
  container: HTMLElement,
  canvas: HTMLCanvasElement,
  scene: SceneState,
): NativeSkeletonPreview {
  const renderer = createFirstPartyWebGL2BoneRenderer(canvas);
  const lifecycle = new HgSceneLifecycle(
    browserFrameScheduler(),
    browserSceneSurface(canvas, container),
    ({width,height,pixelRatio}) => renderer.setSize(width,height,pixelRatio),
  );

  let activeClip = studioStore.getState().document.clip;
  let anchors = currentAnchors(activeClip);
  // Some helper joints may be point-like. Never claim them as line segments.
  const drawable = skeleton.names.filter((name) => skeleton.bone(name).length > 1e-10);
  let disposed = false;

  lifecycle.onFrame((frame) => {
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
    const segments = packBoneSegments(skeleton, scene.evaluation, drawable);
    const drawn = renderer.render(segments);
    canvas.dataset.hgptNativePreview = 'skeleton-only-experimental';
    canvas.dataset.hgptNativeRenderer = renderer.kind;
    canvas.dataset.hgptNativeBoneCount = String(drawable.length);
    canvas.dataset.hgptNativeFrame = String(renderer.frameCount);
    canvas.dataset.hgptNativeContextLost = String(!drawn);
  }, 100);

  lifecycle.mount();

  return {
    dispose(): void {
      if (disposed) return;
      disposed = true;
      lifecycle.dispose();
      renderer.dispose();
    },
  };
}
