import { useEffect, useMemo, useRef, useState } from 'react';
import { Object3D, Quaternion, Vector3 } from 'three';
import type { Camera } from 'three';
import { HgQuat, HgVec3 } from '../core/linearMath';
import {
  HgTransformDrag,
  type HgTransformMode,
} from './transformGizmoInteraction';
import type { HgSceneRayEvent } from './scenePointerTypes';
import { SCENE_FRAME_PRIORITY, useSceneFrame } from './sceneState';
import {
  createTransformGizmoScene,
  registerTransformGizmoPointers,
  updateTransformGizmoActiveAxis,
  type HgGizmoAxis,
  type TransformGizmoPointerCallbacks,
} from './transformGizmoScene';
import { SceneObjectMount } from './SceneObjectMount';
import { useSceneHostBindings } from './sceneHostBindings';

interface FirstPartyTransformGizmoProps {
  object: Object3D;
  camera: Camera;
  mode: HgTransformMode;
  size?: number;
  onDragStart?: () => void;
  onDragEnd?: () => void;
  onObjectChange?: () => void;
}

const AXES: Record<HgGizmoAxis, HgVec3> = {
  x: new HgVec3(1, 0, 0),
  y: new HgVec3(0, 1, 0),
  z: new HgVec3(0, 0, 1),
};

const hgVector = (value: { x: number; y: number; z: number }) =>
  new HgVec3(value.x, value.y, value.z);

const hgQuaternion = (value: { x: number; y: number; z: number; w: number }) =>
  new HgQuat(value.x, value.y, value.z, value.w);

const hgRay = (event: HgSceneRayEvent) => ({
  origin: hgVector(event.ray.origin),
  direction: hgVector(event.ray.direction),
});

interface ActiveDrag {
  pointerId: number;
  interaction: HgTransformDrag;
}

/** Project-owned world-axis translation/rotation gizmo for the current renderer. */
export function FirstPartyTransformGizmo({
  object,
  camera,
  mode,
  size = 0.8,
  onDragStart,
  onDragEnd,
  onObjectChange,
}: FirstPartyTransformGizmoProps) {
  const drag = useRef<ActiveDrag | null>(null);
  const [activeAxis, setActiveAxis] = useState<HgGizmoAxis | null>(null);
  const worldPosition = useRef(new Vector3());
  const worldQuaternion = useRef(new Quaternion());
  const parentQuaternion = useRef(new Quaternion());
  const { pointers } = useSceneHostBindings();
  const resources = useMemo(() => createTransformGizmoScene(mode), [mode]);
  const callbacks = useRef<TransformGizmoPointerCallbacks | null>(null);

  useEffect(() => () => resources.dispose(), [resources]);

  useEffect(() => {
    updateTransformGizmoActiveAxis(resources, activeAxis);
  }, [resources, activeAxis]);

  useSceneFrame(() => {
    object.updateWorldMatrix(true, false);
    object.getWorldPosition(worldPosition.current);
    resources.group.position.copy(worldPosition.current);
    const distance = camera.position.distanceTo(worldPosition.current);
    const scale = Math.max(0.04, distance * 0.12 * size);
    resources.group.scale.setScalar(scale);
  }, SCENE_FRAME_PRIORITY.gizmo);

  const begin = (axis: HgGizmoAxis, event: HgSceneRayEvent) => {
    event.stopPropagation();
    object.updateWorldMatrix(true, false);
    object.getWorldPosition(worldPosition.current);
    object.getWorldQuaternion(worldQuaternion.current);
    drag.current = {
      pointerId: event.pointerId,
      interaction: new HgTransformDrag(
        mode,
        AXES[axis],
        hgRay(event),
        hgVector(worldPosition.current),
        hgQuaternion(worldQuaternion.current),
      ),
    };
    setActiveAxis(axis);
    (event.target as EventTarget & {
      setPointerCapture?: (pointerId: number) => void;
    } | null)?.setPointerCapture?.(event.pointerId);
    onDragStart?.();
  };

  const move = (event: HgSceneRayEvent) => {
    const active = drag.current;
    if (!active || active.pointerId !== event.pointerId) return;
    event.stopPropagation();
    const result = active.interaction.update(hgRay(event));
    if (!result) return;
    worldPosition.current.set(result.position.x, result.position.y, result.position.z);
    worldQuaternion.current.set(
      result.quaternion.x,
      result.quaternion.y,
      result.quaternion.z,
      result.quaternion.w,
    );
    if (object.parent) {
      object.parent.updateWorldMatrix(true, false);
      object.position.copy(object.parent.worldToLocal(worldPosition.current));
      object.parent.getWorldQuaternion(parentQuaternion.current);
      object.quaternion.copy(
        parentQuaternion.current.invert().multiply(worldQuaternion.current),
      );
    } else {
      object.position.copy(worldPosition.current);
      object.quaternion.copy(worldQuaternion.current);
    }
    object.updateMatrix();
    object.updateMatrixWorld(true);
    onObjectChange?.();
  };

  const end = (event: HgSceneRayEvent) => {
    const active = drag.current;
    if (!active || active.pointerId !== event.pointerId) return;
    event.stopPropagation();
    (event.target as EventTarget & {
      releasePointerCapture?: (pointerId: number) => void;
    } | null)?.releasePointerCapture?.(event.pointerId);
    drag.current = null;
    setActiveAxis(null);
    onDragEnd?.();
  };

  callbacks.current = {
    axisDown: begin,
    move,
    up: end,
    cancel: end,
  };

  useEffect(
    () =>
      registerTransformGizmoPointers(resources, pointers, {
        axisDown: (axis, event) => callbacks.current?.axisDown(axis, event),
        move: (event) => callbacks.current?.move(event),
        up: (event) => callbacks.current?.up(event),
        cancel: (event) => callbacks.current?.cancel(event),
      }),
    [resources, pointers],
  );

  return <SceneObjectMount object={resources.group} />;
}
