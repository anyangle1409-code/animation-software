import { forwardRef, useEffect, useImperativeHandle, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Vector3 } from 'three';
import { HgVec3 } from '../core/linearMath';
import { HgOrbitModel } from './orbitModel';
import { HgOrbitPointerTracker, wheelZoomFactor } from './orbitInput';

export interface HgOrbitControlsHandle {
  target: Vector3;
  enabled: boolean;
  /** Synchronise after a camera preset/focus update changed camera and target. */
  update: () => void;
}

const hgVector = (value: { x: number; y: number; z: number }) =>
  new HgVec3(value.x, value.y, value.z);

/** R3F adapter around the project-owned renderer-neutral orbit model. */
export const FirstPartyOrbitControls = forwardRef<HgOrbitControlsHandle>(
  function FirstPartyOrbitControls(_, forwardedRef) {
    const { camera, gl } = useThree();
    const target = useMemo(() => new Vector3(0, 1, 0), []);
    const model = useRef<HgOrbitModel | null>(null);
    const input = useRef(new HgOrbitPointerTracker());

    if (!model.current) {
      model.current = new HgOrbitModel(hgVector(camera.position), hgVector(target), {
        minDistance: 0.6,
        maxDistance: 12,
        damping: 0.12,
      });
    }

    const handle = useMemo<HgOrbitControlsHandle>(() => ({
      target,
      enabled: true,
      update: () => {
        model.current?.sync(hgVector(camera.position), hgVector(target));
        camera.lookAt(target);
        camera.updateMatrixWorld();
      },
    }), [camera, target]);

    useImperativeHandle(forwardedRef, () => handle, [handle]);

    useEffect(() => {
      const element = gl.domElement;
      const previousTouchAction = element.style.touchAction;
      element.style.touchAction = 'none';

      const pointerDown = (event: PointerEvent) => {
        if (!handle.enabled) return;
        if (event.pointerType === 'mouse' && event.button !== 0) return;
        input.current.pointerDown(event.pointerId, event.clientX, event.clientY);
        element.setPointerCapture?.(event.pointerId);
      };
      const pointerMove = (event: PointerEvent) => {
        if (!handle.enabled) return;
        const delta = input.current.pointerMove(
          event.pointerId,
          event.clientX,
          event.clientY,
        );
        if (!delta) return;
        if (delta.zoomFactor !== undefined) {
          model.current?.zoomByFactor(delta.zoomFactor);
        } else {
          model.current?.rotatePixels(
            delta.rotateX ?? 0,
            delta.rotateY ?? 0,
            Math.max(1, element.clientHeight),
          );
        }
      };
      const pointerUp = (event: PointerEvent) => {
        input.current.pointerUp(event.pointerId);
        if (element.hasPointerCapture?.(event.pointerId)) {
          element.releasePointerCapture?.(event.pointerId);
        }
      };
      const wheel = (event: WheelEvent) => {
        if (!handle.enabled) return;
        event.preventDefault();
        model.current?.zoomByFactor(wheelZoomFactor(event.deltaY));
      };

      element.addEventListener('pointerdown', pointerDown);
      element.addEventListener('pointermove', pointerMove);
      element.addEventListener('pointerup', pointerUp);
      element.addEventListener('pointercancel', pointerUp);
      element.addEventListener('wheel', wheel, { passive: false });

      return () => {
        input.current.clear();
        element.style.touchAction = previousTouchAction;
        element.removeEventListener('pointerdown', pointerDown);
        element.removeEventListener('pointermove', pointerMove);
        element.removeEventListener('pointerup', pointerUp);
        element.removeEventListener('pointercancel', pointerUp);
        element.removeEventListener('wheel', wheel);
      };
    }, [gl, handle]);

    useFrame((_, delta) => {
      if (!handle.enabled || !model.current) return;
      const snapshot = model.current.step(delta);
      camera.position.set(snapshot.position.x, snapshot.position.y, snapshot.position.z);
      target.set(snapshot.target.x, snapshot.target.y, snapshot.target.z);
      camera.lookAt(target);
      camera.updateMatrixWorld();
    });

    return null;
  },
);
