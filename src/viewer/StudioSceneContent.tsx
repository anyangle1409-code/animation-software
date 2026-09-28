import { useEffect, useMemo, useRef, useState } from 'react';
import { Euler, Matrix4, Object3D, Quaternion, Vector3 } from 'three';
import { showsMuscleBellies, skeleton, studioStore, useStudio } from '../editor/store';
import { activeCapabilities, useCharacter } from '../editor/characterStore';
import { EULER_ORDER } from '../rig/types';
import { clampRotation } from '../rig/pose';
import { toDeg } from '../core/math';
import { restWorldQuaternion } from '../ik/orient';
import { SCENE_FRAME_PRIORITY, useSceneFrame, useSceneState } from './sceneState';
import { SkeletonView } from './SkeletonView';
import { CharacterFigure } from './CharacterFigure';
import { MuscleView } from './MuscleView';
import { EquipmentView } from './EquipmentView';
import { IKHandles } from './IKHandles';
import { equipmentSocketForInstance } from '../equipment/library';
import {
  createOrbitControlsRuntime,
  type HgOrbitControlsHandle,
} from './orbitControlsRuntime';
import { FirstPartyTransformGizmo } from './FirstPartyTransformGizmo';
import { createCameraRigRuntime } from './cameraRigRuntime';
import { useSceneHostBindings } from './sceneHostBindings';
import { createStaticStageRuntime } from './staticStageRuntime';

function Gizmo({ controls }: { controls: React.RefObject<HgOrbitControlsHandle | null> }) {
  const scene = useSceneState();
  const selection = useStudio((state) => state.selection);
  const gizmoMode = useStudio((state) => state.gizmoMode);
  const setBoneRotation = useStudio((state) => state.setBoneRotation);
  const setEquipmentTransform = useStudio((state) => state.setEquipmentTransform);
  const setEquipmentSocketTransform = useStudio((state) => state.setEquipmentSocketTransform);
  const equipment = useStudio((state) => state.document.clip.equipment);
  const [proxy] = useState(() => new Object3D());
  const socketScratch = useMemo(() => ({
    local: new Matrix4(),
    world: new Matrix4(),
    inverse: new Matrix4(),
    position: new Vector3(),
    quaternion: new Quaternion(),
    scale: new Vector3(),
  }), []);
  const dragging = useRef(false);
  const { scene: root, camera } = useSceneHostBindings();

  useEffect(() => {
    root.add(proxy);
    return () => {
      root.remove(proxy);
    };
  }, [root, proxy]);

  const selectedEquipment = selection.equipmentId
    ? equipment.find((instance) => instance.id === selection.equipmentId) ?? null
    : null;
  const editableEquipment = selectedEquipment?.attachment.mode === 'static' ? selectedEquipment : null;
  const selectedSocket =
    editableEquipment && selection.socketId
      ? equipmentSocketForInstance(editableEquipment, selection.socketId)
      : null;

  useSceneFrame(() => {
    if (dragging.current) return;
    if (selection.bone) {
      proxy.position.copy(scene.evaluation.head(selection.bone, new Vector3()));
      proxy.quaternion.copy(scene.evaluation.quaternion(selection.bone));
      return;
    }
    if (editableEquipment) {
      const transform = scene.frame?.equipment.get(editableEquipment.id);
      if (!transform) return;
      if (selectedSocket) {
        socketScratch.local.compose(
          socketScratch.position.set(
            selectedSocket.position.x,
            selectedSocket.position.y,
            selectedSocket.position.z,
          ),
          socketScratch.quaternion.setFromEuler(
            new Euler(
              (selectedSocket.rotation?.x ?? 0) * Math.PI / 180,
              (selectedSocket.rotation?.y ?? 0) * Math.PI / 180,
              (selectedSocket.rotation?.z ?? 0) * Math.PI / 180,
              EULER_ORDER,
            ),
          ),
          socketScratch.scale.set(1, 1, 1),
        );
        socketScratch.world.multiplyMatrices(transform.matrix, socketScratch.local);
        socketScratch.world.decompose(
          proxy.position,
          proxy.quaternion,
          socketScratch.scale,
        );
        return;
      }
      proxy.position.copy(transform.position);
      proxy.quaternion.copy(transform.quaternion);
    }
  }, SCENE_FRAME_PRIORITY.proxy);

  const target = selection.bone || editableEquipment ? proxy : null;
  if (!target) return null;

  return (
    <FirstPartyTransformGizmo
      object={target}
      camera={camera}
      mode={gizmoMode === 'translate' ? 'translate' : 'rotate'}
      size={0.8}
      onDragStart={() => {
        dragging.current = true;
        if (controls.current) controls.current.enabled = false;
      }}
      onDragEnd={() => {
        dragging.current = false;
        if (controls.current) controls.current.enabled = true;
      }}
      onObjectChange={() => {
        const state = useStudio.getState();
        const bone = state.selection.bone;
        if (bone) {
          if (gizmoMode === 'translate') return;
          const rest = restWorldQuaternion(
            skeleton,
            scene.evaluation,
            bone,
            new Quaternion(),
          );
          const local = rest.clone().invert().multiply(proxy.quaternion);
          const euler = new Euler().setFromQuaternion(local, EULER_ORDER);
          setBoneRotation(
            bone,
            clampRotation(skeleton.bone(bone), {
              x: euler.x,
              y: euler.y,
              z: euler.z,
            }),
          );
          return;
        }

        const equipmentId = state.selection.equipmentId;
        if (!equipmentId || !editableEquipment || editableEquipment.id !== equipmentId) return;
        const socketId = state.selection.socketId;
        if (socketId && selectedSocket) {
          const transform = scene.frame?.equipment.get(equipmentId);
          if (!transform) return;
          proxy.updateMatrix();
          socketScratch.inverse.copy(transform.matrix).invert();
          socketScratch.local.multiplyMatrices(socketScratch.inverse, proxy.matrix);
          socketScratch.local.decompose(
            socketScratch.position,
            socketScratch.quaternion,
            socketScratch.scale,
          );
          const euler = new Euler().setFromQuaternion(
            socketScratch.quaternion,
            EULER_ORDER,
          );
          setEquipmentSocketTransform(equipmentId, socketId, {
            position: {
              x: socketScratch.position.x,
              y: socketScratch.position.y,
              z: socketScratch.position.z,
            },
            rotation: { x: toDeg(euler.x), y: toDeg(euler.y), z: toDeg(euler.z) },
          });
          return;
        }
        if (gizmoMode === 'translate') {
          setEquipmentTransform(equipmentId, {
            position: {
              x: proxy.position.x,
              y: proxy.position.y,
              z: proxy.position.z,
            },
          });
          return;
        }
        const euler = new Euler().setFromQuaternion(proxy.quaternion, EULER_ORDER);
        setEquipmentTransform(equipmentId, {
          rotation: { x: toDeg(euler.x), y: toDeg(euler.y), z: toDeg(euler.z) },
        });
      }}
    />
  );
}

function HandleGizmo({ controls }: { controls: React.RefObject<HgOrbitControlsHandle | null> }) {
  const selection = useStudio((state) => state.selection.handle);
  const setIKTarget = useStudio((state) => state.setIKTarget);
  const scene = useSceneState();
  const [proxy] = useState(() => new Object3D());
  const dragging = useRef(false);
  const { scene: root, camera } = useSceneHostBindings();
  const clip = useStudio((state) => state.document.clip);
  const time = useStudio((state) => state.time);

  useEffect(() => {
    root.add(proxy);
    return () => {
      root.remove(proxy);
    };
  }, [root, proxy]);

  useSceneFrame(() => {
    if (dragging.current || !selection) return;
    if (!scene.frame) return;
    const goal = sampleGoal(clip, time, selection.chain);
    if (!goal) return;
    const point = selection.kind === 'target' ? goal.target : goal.pole;
    proxy.position.set(point.x, point.y, point.z);
  }, SCENE_FRAME_PRIORITY.proxy);

  if (!selection) return null;

  return (
    <FirstPartyTransformGizmo
      object={proxy}
      camera={camera}
      mode="translate"
      size={0.6}
      onDragStart={() => {
        dragging.current = true;
        if (controls.current) controls.current.enabled = false;
      }}
      onDragEnd={() => {
        dragging.current = false;
        if (controls.current) controls.current.enabled = true;
      }}
      onObjectChange={() => {
        setIKTarget(selection.chain, selection.kind, {
          x: proxy.position.x,
          y: proxy.position.y,
          z: proxy.position.z,
        });
      }}
    />
  );
}

function sampleGoal(
  clip: ReturnType<typeof useStudio.getState>['document']['clip'],
  time: number,
  chain: Parameters<ReturnType<typeof useStudio.getState>['setIKTarget']>[0],
) {
  const keyframe = clip.keyframes.find((frame) => Math.abs(frame.time - time) < 1e-6);
  return (keyframe ?? clip.keyframes[0])?.ik[chain] ?? null;
}

function Figure() {
  const viewMode = useStudio((state) => state.viewMode);
  const showEquipment = useStudio((state) => state.showEquipment);
  const showIkHandles = useStudio((state) => state.showIkHandles);
  const anatomy = activeCapabilities(useCharacter((state) => state.sourceId)).anatomy;

  return (
    <>
      {(viewMode === 'skeleton' || viewMode === 'combined') && (
        <SkeletonView ghosted={viewMode === 'combined'} />
      )}
      {showsMuscleBellies(viewMode) && <MuscleView />}
      {viewMode === 'character' && <CharacterFigure />}
      {viewMode === 'anatomy' && (
        <CharacterFigure variant={anatomy ? 'ecorche' : 'skin'} />
      )}
      {viewMode === 'muscles' && (
        <CharacterFigure opacity={0.24} depthWrite={false} />
      )}
      {showEquipment && <EquipmentView />}
      {showIkHandles && <IKHandles />}
    </>
  );
}

function StaticStageBridge() {
  const { scene: root } = useSceneHostBindings();

  useEffect(() => {
    const runtime = createStaticStageRuntime(root, studioStore);
    return () => runtime.dispose();
  }, [root]);

  return null;
}

/**
 * Host-neutral React scene composition.
 *
 * Every Three object is mounted through SceneObjectMount/shared scene ports.
 * The host only supplies camera/scene/canvas bindings and a frame clock.
 */
export function StudioSceneContent() {
  const controls = useRef<HgOrbitControlsHandle | null>(null);
  const sceneState = useSceneState();
  const { camera, element } = useSceneHostBindings();

  useEffect(() => {
    const orbit = createOrbitControlsRuntime(camera, element, sceneState);
    controls.current = orbit.handle;
    const cameraRig = createCameraRigRuntime({
      sceneState,
      camera,
      store: studioStore,
      controls: () => controls.current,
    });
    return () => {
      cameraRig.dispose();
      controls.current = null;
      orbit.dispose();
    };
  }, [camera, element, sceneState]);

  return (
    <>
      <StaticStageBridge />
      <Figure />
      <Gizmo controls={controls} />
      <HandleGizmo controls={controls} />
    </>
  );
}
