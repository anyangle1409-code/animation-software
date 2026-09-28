import { Vector3 } from 'three';
import type { Camera } from 'three';
import { HgVec3 } from '../core/linearMath';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';
import { HgOrbitModel } from './orbitModel';
import { HgOrbitPointerTracker, wheelZoomFactor } from './orbitInput';

export interface HgOrbitControlsHandle {
  target: Vector3;
  enabled: boolean;
  /** Synchronise after a camera preset/focus update changed camera and target. */
  update(): void;
}

export interface OrbitControlsRuntime {
  handle: HgOrbitControlsHandle;
  dispose(): void;
}

const hgVector = (value: { x: number; y: number; z: number }) =>
  new HgVec3(value.x, value.y, value.z);

/** Framework-neutral orbit input/model/frame lifecycle. */
export function createOrbitControlsRuntime(
  camera: Camera,
  element: HTMLCanvasElement,
  sceneState: SceneState,
): OrbitControlsRuntime {
  const target = new Vector3(0, 1, 0);
  const model = new HgOrbitModel(hgVector(camera.position), hgVector(target), {
    minDistance: 0.6,
    maxDistance: 12,
    damping: 0.12,
  });
  const input = new HgOrbitPointerTracker();

  const handle: HgOrbitControlsHandle = {
    target,
    enabled: true,
    update: () => {
      model.sync(hgVector(camera.position), hgVector(target));
      camera.lookAt(target);
      camera.updateMatrixWorld();
    },
  };

  const previousTouchAction = element.style.touchAction;
  element.style.touchAction = 'none';

  const pointerDown = (event: PointerEvent) => {
    if (!handle.enabled) return;
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    input.pointerDown(event.pointerId, event.clientX, event.clientY);
    element.setPointerCapture?.(event.pointerId);
  };
  const pointerMove = (event: PointerEvent) => {
    if (!handle.enabled) return;
    const delta = input.pointerMove(
      event.pointerId,
      event.clientX,
      event.clientY,
    );
    if (!delta) return;
    if (delta.zoomFactor !== undefined) {
      model.zoomByFactor(delta.zoomFactor);
    } else {
      model.rotatePixels(
        delta.rotateX ?? 0,
        delta.rotateY ?? 0,
        Math.max(1, element.clientHeight),
      );
    }
  };
  const pointerUp = (event: PointerEvent) => {
    input.pointerUp(event.pointerId);
    if (element.hasPointerCapture?.(event.pointerId)) {
      element.releasePointerCapture?.(event.pointerId);
    }
  };
  const wheel = (event: WheelEvent) => {
    if (!handle.enabled) return;
    event.preventDefault();
    model.zoomByFactor(wheelZoomFactor(event.deltaY));
  };

  element.addEventListener('pointerdown', pointerDown);
  element.addEventListener('pointermove', pointerMove);
  element.addEventListener('pointerup', pointerUp);
  element.addEventListener('pointercancel', pointerUp);
  element.addEventListener('wheel', wheel, { passive: false });

  const removeFrame = sceneState.consumers.add(({ delta }) => {
    if (!handle.enabled) return;
    const snapshot = model.step(delta);
    camera.position.set(
      snapshot.position.x,
      snapshot.position.y,
      snapshot.position.z,
    );
    target.set(snapshot.target.x, snapshot.target.y, snapshot.target.z);
    camera.lookAt(target);
    camera.updateMatrixWorld();
  }, SCENE_FRAME_PRIORITY.orbit);

  let disposed = false;
  return {
    handle,
    dispose() {
      if (disposed) return;
      disposed = true;
      removeFrame();
      input.clear();
      element.style.touchAction = previousTouchAction;
      element.removeEventListener('pointerdown', pointerDown);
      element.removeEventListener('pointermove', pointerMove);
      element.removeEventListener('pointerup', pointerUp);
      element.removeEventListener('pointercancel', pointerUp);
      element.removeEventListener('wheel', wheel);
    },
  };
}
