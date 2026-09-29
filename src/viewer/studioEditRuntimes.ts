import {
  Object3D,
  type Camera,
  type Scene,
} from './threeSceneBoundary';
import { HgMat4, HgQuat, HgVec3 } from '../core/linearMath';
import type { StudioClip } from '../animation/clip';
import { toDeg } from '../core/math';
import { equipmentSocketForInstance } from '../equipment/library';
import type { EquipmentInstance } from '../equipment/types';
import { restWorldQuaternion } from '../ik/orient';
import type { IKChainId } from '../ik/types';
import { clampRotation } from '../rig/pose';
import type { BoneName } from '../rig/boneNames';
import type { Skeleton } from '../rig/skeleton';
import type { Vec3 } from '../rig/types';
import type { SceneState } from './sceneStateCore';
import { SCENE_FRAME_PRIORITY } from './sceneStateCore';
import type { HgScenePointerRouter } from './scenePointerRouter';
import {
  createTransformGizmoRuntime,
  type TransformGizmoRuntime,
} from './transformGizmoRuntime';
import type { HgOrbitControlsHandle } from './orbitControlsRuntime';

export interface StudioEditSelection {
  bone: BoneName | null;
  handle: { chain: IKChainId; kind: 'target' | 'pole' } | null;
  equipmentId: string | null;
  socketId: string | null;
}

export interface StudioEditState {
  document: { clip: StudioClip };
  time: number;
  selection: StudioEditSelection;
  gizmoMode: 'rotate' | 'translate';
  setBoneRotation(bone: BoneName, rotation: Vec3): void;
  setIKTarget(chain: IKChainId, kind: 'target' | 'pole', position: Vec3): void;
  setEquipmentTransform(
    instanceId: string,
    transform: { position?: Vec3; rotation?: Vec3 },
  ): void;
  setEquipmentSocketTransform(
    instanceId: string,
    socketId: string,
    transform: { position?: Vec3; rotation?: Vec3 } | null,
  ): void;
}

export interface StudioEditStorePort {
  getState(): StudioEditState;
  subscribe(listener: () => void): () => void;
}

export interface StudioEditRuntimeOptions {
  sceneState: SceneState;
  root: Pick<Scene, 'add' | 'remove'>;
  pointers: Pick<HgScenePointerRouter, 'register'>;
  camera: Camera;
  store: StudioEditStorePort;
  skeleton: Skeleton;
  controls(): HgOrbitControlsHandle | null;
}

export interface StudioEditRuntime {
  dispose(): void;
}

const selectedStaticEquipment = (
  state: StudioEditState,
): EquipmentInstance | null => {
  const id = state.selection.equipmentId;
  if (!id) return null;
  const instance =
    state.document.clip.equipment.find((candidate) => candidate.id === id) ?? null;
  return instance?.attachment.mode === 'static' ? instance : null;
};

const sampleGoal = (
  clip: StudioClip,
  time: number,
  chain: IKChainId,
) => {
  const keyframe = clip.keyframes.find((frame) => Math.abs(frame.time - time) < 1e-6);
  return (keyframe ?? clip.keyframes[0])?.ik[chain] ?? null;
};

export function createStudioSelectionGizmoRuntime(
  options: StudioEditRuntimeOptions,
): StudioEditRuntime {
  const {
    sceneState,
    root,
    pointers,
    camera,
    store,
    skeleton,
    controls,
  } = options;

  const proxy = new Object3D();
  const socketScratch = {
    local: new HgMat4(),
    world: new HgMat4(),
    inverse: new HgMat4(),
    position: new HgVec3(),
    quaternion: new HgQuat(),
    scale: new HgVec3(),
    proxyQuaternion: new HgQuat(),
  };
  let dragging = false;
  let gizmo: TransformGizmoRuntime | null = null;
  let gizmoMode: StudioEditState['gizmoMode'] | null = null;
  let disposed = false;

  root.add(proxy);

  const selectedSocket = (state: StudioEditState) => {
    const equipment = selectedStaticEquipment(state);
    return equipment && state.selection.socketId
      ? equipmentSocketForInstance(equipment, state.selection.socketId)
      : null;
  };

  const syncGizmo = () => {
    const state = store.getState();
    const hasTarget = Boolean(
      state.selection.bone || selectedStaticEquipment(state),
    );
    if (!hasTarget) {
      gizmo?.dispose();
      gizmo = null;
      gizmoMode = null;
      return;
    }
    if (gizmo && gizmoMode === state.gizmoMode) return;

    gizmo?.dispose();
    gizmoMode = state.gizmoMode;
    gizmo = createTransformGizmoRuntime({
      sceneState,
      root,
      pointers,
      camera,
      object: proxy,
      mode: state.gizmoMode,
      size: 0.8,
      onDragStart: () => {
        dragging = true;
        const orbit = controls();
        if (orbit) orbit.enabled = false;
      },
      onDragEnd: () => {
        dragging = false;
        const orbit = controls();
        if (orbit) orbit.enabled = true;
      },
      onObjectChange: () => {
        const current = store.getState();
        const bone = current.selection.bone;
        if (bone) {
          if (current.gizmoMode === 'translate') return;
          const rest = restWorldQuaternion(
            skeleton,
            sceneState.evaluation,
            bone,
            new HgQuat(),
          );
          const local = rest.clone().invert().multiply(
            socketScratch.proxyQuaternion.copy(proxy.quaternion),
          );
          const euler = local.toEulerXZY();
          current.setBoneRotation(
            bone,
            clampRotation(skeleton.bone(bone), {
              x: euler.x,
              y: euler.y,
              z: euler.z,
            }),
          );
          return;
        }

        const equipment = selectedStaticEquipment(current);
        const equipmentId = current.selection.equipmentId;
        if (!equipment || !equipmentId) return;

        const socket = selectedSocket(current);
        const socketId = current.selection.socketId;
        if (socket && socketId) {
          const transform = sceneState.frame?.equipment.get(equipmentId);
          if (!transform) return;
          proxy.updateMatrix();
          socketScratch.inverse.copy(transform.matrix).invert();
          socketScratch.local.multiplyMatrices(
            socketScratch.inverse,
            proxy.matrix,
          );
          socketScratch.local.decompose(
            socketScratch.position,
            socketScratch.quaternion,
            socketScratch.scale,
          );
          const euler = socketScratch.quaternion.toEulerXZY();
          current.setEquipmentSocketTransform(equipmentId, socketId, {
            position: {
              x: socketScratch.position.x,
              y: socketScratch.position.y,
              z: socketScratch.position.z,
            },
            rotation: {
              x: toDeg(euler.x),
              y: toDeg(euler.y),
              z: toDeg(euler.z),
            },
          });
          return;
        }

        if (current.gizmoMode === 'translate') {
          current.setEquipmentTransform(equipmentId, {
            position: {
              x: proxy.position.x,
              y: proxy.position.y,
              z: proxy.position.z,
            },
          });
          return;
        }

        const euler = socketScratch.proxyQuaternion
          .copy(proxy.quaternion)
          .toEulerXZY();
        current.setEquipmentTransform(equipmentId, {
          rotation: {
            x: toDeg(euler.x),
            y: toDeg(euler.y),
            z: toDeg(euler.z),
          },
        });
      },
    });
  };

  const unsubscribe = store.subscribe(syncGizmo);
  syncGizmo();

  const removeFrame = sceneState.consumers.add(() => {
    if (dragging) return;
    const state = store.getState();

    if (state.selection.bone) {
      const head = sceneState.evaluation.firstPartyEvaluation.head(
        state.selection.bone,
        socketScratch.position,
      );
      proxy.position.set(head.x, head.y, head.z);
      const rotation = sceneState.evaluation.firstPartyEvaluation.quaternion(
        state.selection.bone,
      );
      proxy.quaternion.set(rotation.x, rotation.y, rotation.z, rotation.w);
      return;
    }

    const equipment = selectedStaticEquipment(state);
    if (!equipment) return;
    const transform = sceneState.frame?.equipment.get(equipment.id);
    if (!transform) return;

    const socket = selectedSocket(state);
    if (socket) {
      socketScratch.local.compose(
        socketScratch.position.set(
          socket.position.x,
          socket.position.y,
          socket.position.z,
        ),
        socketScratch.quaternion.setFromEulerXZY(
          (socket.rotation?.x ?? 0) * Math.PI / 180,
          (socket.rotation?.y ?? 0) * Math.PI / 180,
          (socket.rotation?.z ?? 0) * Math.PI / 180,
        ),
        socketScratch.scale.set(1, 1, 1),
      );
      socketScratch.world.copy(transform.matrix).multiply(socketScratch.local);
      socketScratch.world.decompose(
        socketScratch.position,
        socketScratch.quaternion,
        socketScratch.scale,
      );
      proxy.position.set(
        socketScratch.position.x,
        socketScratch.position.y,
        socketScratch.position.z,
      );
      proxy.quaternion.set(
        socketScratch.quaternion.x,
        socketScratch.quaternion.y,
        socketScratch.quaternion.z,
        socketScratch.quaternion.w,
      );
      return;
    }

    proxy.position.copy(transform.position);
    proxy.quaternion.copy(transform.quaternion);
  }, SCENE_FRAME_PRIORITY.proxy);

  return {
    dispose() {
      if (disposed) return;
      disposed = true;
      removeFrame();
      unsubscribe();
      gizmo?.dispose();
      gizmo = null;
      root.remove(proxy);
    },
  };
}

export function createStudioHandleGizmoRuntime(
  options: StudioEditRuntimeOptions,
): StudioEditRuntime {
  const { sceneState, root, pointers, camera, store, controls } = options;
  const proxy = new Object3D();
  let dragging = false;
  let gizmo: TransformGizmoRuntime | null = null;
  let disposed = false;

  root.add(proxy);

  const syncGizmo = () => {
    const selected = store.getState().selection.handle;
    if (!selected) {
      gizmo?.dispose();
      gizmo = null;
      return;
    }
    if (gizmo) return;

    gizmo = createTransformGizmoRuntime({
      sceneState,
      root,
      pointers,
      camera,
      object: proxy,
      mode: 'translate',
      size: 0.6,
      onDragStart: () => {
        dragging = true;
        const orbit = controls();
        if (orbit) orbit.enabled = false;
      },
      onDragEnd: () => {
        dragging = false;
        const orbit = controls();
        if (orbit) orbit.enabled = true;
      },
      onObjectChange: () => {
        const state = store.getState();
        const selectedHandle = state.selection.handle;
        if (!selectedHandle) return;
        state.setIKTarget(
          selectedHandle.chain,
          selectedHandle.kind,
          { x: proxy.position.x, y: proxy.position.y, z: proxy.position.z },
        );
      },
    });
  };

  const unsubscribe = store.subscribe(syncGizmo);
  syncGizmo();

  const removeFrame = sceneState.consumers.add(() => {
    if (dragging) return;
    const state = store.getState();
    const selected = state.selection.handle;
    if (!selected || !sceneState.frame) return;
    const goal = sampleGoal(
      state.document.clip,
      state.time,
      selected.chain,
    );
    if (!goal) return;
    const point = selected.kind === 'target' ? goal.target : goal.pole;
    proxy.position.set(point.x, point.y, point.z);
  }, SCENE_FRAME_PRIORITY.proxy);

  return {
    dispose() {
      if (disposed) return;
      disposed = true;
      removeFrame();
      unsubscribe();
      gizmo?.dispose();
      gizmo = null;
      root.remove(proxy);
    },
  };
}
