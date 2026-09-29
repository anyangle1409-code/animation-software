import { type Scene } from './threeSceneBoundary';
import { HgMat4, HgQuat, HgVec3 } from '../core/linearMath';
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

export interface TransformGizmoCameraPort {
  position: { x: number; y: number; z: number };
}

export interface TransformObjectPort {
  parent: {
    readonly matrixWorld: { readonly elements: ArrayLike<number> };
    updateWorldMatrix(updateParents: boolean, updateChildren: boolean): void;
  } | null;
  readonly position: {
    x: number;
    y: number;
    z: number;
    set(x: number, y: number, z: number): unknown;
  };
  readonly quaternion: {
    x: number;
    y: number;
    z: number;
    w: number;
    set(x: number, y: number, z: number, w: number): unknown;
  };
  readonly matrixWorld: { readonly elements: ArrayLike<number> };
  updateWorldMatrix(updateParents: boolean, updateChildren: boolean): void;
  updateMatrix(): void;
  updateMatrixWorld(force?: boolean): void;
}

export interface TransformGizmoRuntimeOptions {
  sceneState: SceneState;
  root: Pick<Scene, 'add' | 'remove'>;
  pointers: Pick<HgScenePointerRouter, 'register'>;
  camera: TransformGizmoCameraPort;
  object: TransformObjectPort;
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
  const worldPosition = new HgVec3();
  const worldQuaternion = new HgQuat();
  const parentQuaternion = new HgQuat();
  const matrix = new HgMat4();
  let drag: ActiveDrag | null = null;
  let disposed = false;

  root.add(resources.group);

  const begin = (axis: HgGizmoAxis, event: HgSceneRayEvent) => {
    event.stopPropagation();
    object.updateWorldMatrix(true, false);
    worldPosition.setFromMatrixPosition(object.matrixWorld);
    worldQuaternion.setFromRotationMatrix(
      matrix.extractRotation(object.matrixWorld),
    );
    drag = {
      pointerId: event.pointerId,
      interaction: new HgTransformDrag(
        mode,
        AXES[axis],
        hgRay(event),
        worldPosition.clone(),
        worldQuaternion.clone(),
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

    worldPosition.copy(result.position);
    worldQuaternion.copy(result.quaternion);

    if (object.parent) {
      object.parent.updateWorldMatrix(true, false);
      const localPosition = worldPosition.clone().applyMatrix4(
        matrix.copy(object.parent.matrixWorld).invert(),
      );
      parentQuaternion.setFromRotationMatrix(
        matrix.extractRotation(object.parent.matrixWorld),
      );
      const localQuaternion = parentQuaternion.invert().multiply(worldQuaternion);
      object.position.set(localPosition.x, localPosition.y, localPosition.z);
      object.quaternion.set(
        localQuaternion.x,
        localQuaternion.y,
        localQuaternion.z,
        localQuaternion.w,
      );
    } else {
      object.position.set(worldPosition.x, worldPosition.y, worldPosition.z);
      object.quaternion.set(
        worldQuaternion.x,
        worldQuaternion.y,
        worldQuaternion.z,
        worldQuaternion.w,
      );
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
    worldPosition.setFromMatrixPosition(object.matrixWorld);
    resources.group.position.set(worldPosition.x, worldPosition.y, worldPosition.z);
    const distance = Math.hypot(
      camera.position.x - worldPosition.x,
      camera.position.y - worldPosition.y,
      camera.position.z - worldPosition.z,
    );
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
