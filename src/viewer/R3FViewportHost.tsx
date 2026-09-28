import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Euler, Matrix4, Object3D, Quaternion, Vector3 } from 'three';
import { BACKDROPS, currentAnchors, showsMuscleBellies, skeleton, useStudio } from '../editor/store';
import type { BackdropStyle } from '../editor/store';
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
import { resolveCamera } from './cameras';
import { equipmentSocketForInstance } from '../equipment/library';
import { driveSceneFrame } from './sceneFrameDriver';
import {
  FirstPartyOrbitControls,
  type HgOrbitControlsHandle,
} from './FirstPartyOrbitControls';
import { FirstPartyTransformGizmo } from './FirstPartyTransformGizmo';
import { createStudioStage } from './studioStage';

/**
 * Advances playback and resolves the frame, once per rendered frame and before
 * anything else in the scene reads it.
 */
function FrameDriver() {
  const scene = useSceneState();
  const clip = useStudio((state) => state.document.clip);
  const anchors = useMemo(() => currentAnchors(clip), [clip]);

  useFrame((state, delta) => {
    driveSceneFrame({
      scene,
      skeleton,
      clip,
      anchors,
      playback: useStudio.getState(),
      frame: {
        delta,
        elapsed: state.clock.elapsedTime,
        timestampMs: state.clock.elapsedTime * 1000,
      },
    });
  }, -1);

  return null;
}

/** Moves the camera to the selected preset, then hands control back to orbit. */
function CameraRig({ controls }: { controls: React.RefObject<HgOrbitControlsHandle | null> }) {
  const scene = useSceneState();
  const preset = useStudio((state) => state.camera);
  const recommendation = useStudio((state) => state.document.exercise.camera);
  const selectedBone = useStudio((state) => state.selection.bone);
  const { camera } = useThree();
  const goal = useRef<{ position: Vector3; target: Vector3; fov: number } | null>(null);
  const focusTarget = useRef(new Vector3());
  const focusPosition = useRef(new Vector3());
  const focusOffset = useRef(new Vector3());

  useEffect(() => {
    const setup = resolveCamera(preset, recommendation);
    goal.current = setup
      ? { position: setup.position.clone(), target: setup.target.clone(), fov: setup.fov }
      : null;
  }, [preset, recommendation]);

  useSceneFrame(({ delta }) => {
    if (preset === 'focus' && selectedBone && controls.current) {
      scene.evaluation.head(selectedBone, focusTarget.current);
      const side = selectedBone.endsWith('_l') ? -1 : selectedBone.endsWith('_r') ? 1 : 1;
      focusOffset.current.set(side * 0.58, 0.20, 0.78);
      focusPosition.current.copy(focusTarget.current).add(focusOffset.current);
      const blend = Math.min(1, delta * 7);
      camera.position.lerp(focusPosition.current, blend);
      controls.current.target.lerp(focusTarget.current, blend);
      if ('fov' in camera) {
        camera.fov += (32 - camera.fov) * blend;
        camera.updateProjectionMatrix();
      }
      controls.current.update();
      return;
    }

    const destination = goal.current;
    if (!destination || !controls.current) return;
    const blend = Math.min(1, delta * 6);
    camera.position.lerp(destination.position, blend);
    controls.current.target.lerp(destination.target, blend);
    if ('fov' in camera) {
      camera.fov += (destination.fov - camera.fov) * blend;
      camera.updateProjectionMatrix();
    }
    controls.current.update();
    if (camera.position.distanceTo(destination.position) < 0.01) goal.current = null;
  }, SCENE_FRAME_PRIORITY.camera);

  return null;
}

/**
 * The transform gizmo. On a joint it rotates that joint within its anatomical
 * limits; on an IK handle it drags the target or pole. Both write through the
 * store, so every gizmo move is undoable like any other edit.
 */
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
  const { scene: root, camera } = useThree();

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
          socketScratch.position.set(selectedSocket.position.x, selectedSocket.position.y, selectedSocket.position.z),
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
        socketScratch.world.decompose(proxy.position, proxy.quaternion, socketScratch.scale);
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
          if (gizmoMode === 'translate') {
            // Translating a joint is meaningless on a fixed-length skeleton; the
            // gizmo drives IK targets instead, handled below.
            return;
          }
          const rest = restWorldQuaternion(skeleton, scene.evaluation, bone, new Quaternion());
          const local = rest.clone().invert().multiply(proxy.quaternion);
          const euler = new Euler().setFromQuaternion(local, EULER_ORDER);
          setBoneRotation(
            bone,
            clampRotation(skeleton.bone(bone), { x: euler.x, y: euler.y, z: euler.z }),
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
          const euler = new Euler().setFromQuaternion(socketScratch.quaternion, EULER_ORDER);
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
            position: { x: proxy.position.x, y: proxy.position.y, z: proxy.position.z },
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

/** Gizmo for the selected IK target or pole handle. */
function HandleGizmo({ controls }: { controls: React.RefObject<HgOrbitControlsHandle | null> }) {
  const selection = useStudio((state) => state.selection.handle);
  const setIKTarget = useStudio((state) => state.setIKTarget);
  const scene = useSceneState();
  const [proxy] = useState(() => new Object3D());
  const dragging = useRef(false);
  const { scene: root, camera } = useThree();
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
    const frame = scene.frame;
    if (!frame) return;
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

function OrbitControlsBridge({ controls }: { controls: React.RefObject<HgOrbitControlsHandle | null> }) {
  const { camera, gl } = useThree();
  return <FirstPartyOrbitControls ref={controls} camera={camera} element={gl.domElement} />;
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
  // Asked, not assumed: a textured import carries no écorché mapping, and the
  // anatomy view falls back to the plain surface rather than rendering noise.
  const anatomy = activeCapabilities(useCharacter((state) => state.sourceId)).anatomy;

  return (
    <>
      {(viewMode === 'skeleton' || viewMode === 'combined') && (
        <SkeletonView ghosted={viewMode === 'combined'} />
      )}
      {showsMuscleBellies(viewMode) && <MuscleView />}
      {viewMode === 'character' && <CharacterFigure />}
      {/*
        The anatomy view is one continuous surface and nothing else: the muscle
        bellies are never mounted beside it, at any activation, because a
        balloon floating inside the arm is exactly what this view exists to
        replace.
      */}
      {viewMode === 'anatomy' && <CharacterFigure variant={anatomy ? 'ecorche' : 'skin'} />}
      {viewMode === 'muscles' && <CharacterFigure opacity={0.24} depthWrite={false} />}
      {showEquipment && <EquipmentView />}
      {showIkHandles && <IKHandles />}
    </>
  );
}

export function StaticStageBridge({
  backdrop,
  showGrid,
}: {
  backdrop: BackdropStyle;
  showGrid: boolean;
}) {
  const { scene: root } = useThree();
  const stage = useMemo(() => createStudioStage(backdrop, showGrid), [backdrop, showGrid]);

  useEffect(() => {
    const previousBackground = root.background;
    root.background = stage.background;
    return () => {
      if (root.background === stage.background) root.background = previousBackground;
      stage.dispose();
    };
  }, [root, stage]);

  return <primitive object={stage.root} />;
}

function R3FViewportHost() {
  const controls = useRef<HgOrbitControlsHandle | null>(null);
  const showGrid = useStudio((state) => state.showGrid);
  const selectBone = useStudio((state) => state.selectBone);
  const backdrop = BACKDROPS[useStudio((state) => state.backdrop)];

  return (
      <Canvas
        shadows
        dpr={[1, 2]}
        camera={{ position: [2.3, 1.35, 2.7], fov: 38, near: 0.05, far: 100 }}
        onPointerMissed={() => selectBone(null)}
      >
        <StaticStageBridge backdrop={backdrop} showGrid={showGrid} />

        <FrameDriver />
        <Figure />
        <Gizmo controls={controls} />
        <HandleGizmo controls={controls} />

        <OrbitControlsBridge controls={controls} />
        <CameraRig controls={controls} />
      </Canvas>
  );
}
