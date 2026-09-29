import {
  Object3D,
  Quaternion,
  Vector3,
  type Camera,
  type Scene,
} from './threeSceneBoundary';
import { HgQuat, HgVec3 } from '../core/linearMath';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';
import {
  HgTransformDrag,
  type HgTransformMode,
} from './transformGizmoInteraction';
import type { HgSceneRayEvent } from './scenePointerTypes';
import type { HgScenePointerRouter } from './scenePointerRouter';
import {
  createTransformGizmoScene,
  registerTransformGizmoPointers,
  updateTransformGizmoActiveAxis,
  type HgGizmoAxis,
  type TransformGizmoSceneResources,
} from './transformGizmoScene';

export interface TransformGizmoRuntimeOptions {
  sceneState: SceneState;
  root: Pick<Scene, 'add' | 'remove'>;
  pointers: Pick<HgScenePointerRouter, 'register'>;
  camera: Camera;
  object: Object3D;
  mode: HgTransformMode;
  size?: number;
  onDragStart?(): void;
  onDragEnd?(): void;
  onObjectChange?(): void;
}

export interface TransformGizmoRuntime {
  readonly resources: TransformGizmoSceneResources;
  dispose(): void;
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

/**
 * Framework-neutral world-axis translation/rotation gizmo runtime.
 *
 * Owns scene resources, pointer registration/capture semantics, frame-based
 * screen scaling, object mutation and deterministic disposal.
 */
export function createTransformGizmoRuntime(
  options: TransformGizmoRuntimeOptions,
): TransformGizmoRuntime {
  const {
    sceneState,
    root,
    pointers,
    camera,
    object,
    mode,
    size = 0.8,
    onDragStart,
    onDragEnd,
    onObjectChange,
  } = options;

  const resources = createTransformGizmoScene(mode);
  const worldPosition = new Vector3();
  const worldQuaternion = new Quaternion();
  const parentQuaternion = new Quaternion();
  let drag: ActiveDrag | null = null;
  let disposed = false;

  root.add(resources.group);

  const begin = (axis: HgGizmoAxis, event: HgSceneRayEvent) => {
    event.stopPropagation();
    object.updateWorldMatrix(true, false);
    object.getWorldPosition(worldPosition);
    object.getWorldQuaternion(worldQuaternion);
    drag = {
      pointerId: event.pointerId,
      interaction: new HgTransformDrag(
        mode,
        AXES[axis],
        hgRay(event),
        hgVector(worldPosition),
        hgQuaternion(worldQuaternion),
      ),
    };
    updateTransformGizmoActiveAxis(resources, axis);
    (event.target as EventTarget & {
      setPointerCapture?: (pointerId: number) => void;
    } | null)?.setPointerCapture?.(event.pointerId);
    onDragStart?.();
  };

  const move = (event: HgSceneRayEvent) => {
    const active = drag;
    if (!active || active.pointerId !== event.pointerId) return;
    event.stopPropagation();
    const result = active.interaction.update(hgRay(event));
    if (!result) return;

    worldPosition.set(result.position.x, result.position.y, result.position.z);
    worldQuaternion.set(
      result.quaternion.x,
      result.quaternion.y,
      result.quaternion.z,
      result.quaternion.w,
    );

    if (object.parent) {
      object.parent.updateWorldMatrix(true, false);
      object.position.copy(object.parent.worldToLocal(worldPosition));
      object.parent.getWorldQuaternion(parentQuaternion);
      object.quaternion.copy(
        parentQuaternion.invert().multiply(worldQuaternion),
      );
    } else {
      object.position.copy(worldPosition);
      object.quaternion.copy(worldQuaternion);
    }
    object.updateMatrix();
    object.updateMatrixWorld(true);
    onObjectChange?.();
  };

  const end = (event: HgSceneRayEvent) => {
    const active = drag;
    if (!active || active.pointerId !== event.pointerId) return;
    event.stopPropagation();
    (event.target as EventTarget & {
      releasePointerCapture?: (pointerId: number) => void;
    } | null)?.releasePointerCapture?.(event.pointerId);
    drag = null;
    updateTransformGizmoActiveAxis(resources, null);
    onDragEnd?.();
  };

  const removePointers = registerTransformGizmoPointers(resources, pointers, {
    axisDown: begin,
    move,
    up: end,
    cancel: end,
  });

  const removeFrame = sceneState.consumers.add(() => {
    object.updateWorldMatrix(true, false);
    object.getWorldPosition(worldPosition);
    resources.group.position.copy(worldPosition);
    const distance = camera.position.distanceTo(worldPosition);
    const scale = Math.max(0.04, distance * 0.12 * size);
    resources.group.scale.setScalar(scale);
  }, SCENE_FRAME_PRIORITY.gizmo);

  return {
    resources,
    dispose() {
      if (disposed) return;
      disposed = true;
      if (drag) onDragEnd?.();
      drag = null;
      removeFrame();
      removePointers();
      root.remove(resources.group);
      resources.dispose();
    },
  };
}
