import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Grid, OrbitControls, TransformControls } from '@react-three/drei';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Euler, Matrix4, Object3D, Quaternion, Vector3 } from 'three';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { BACKDROPS, currentAnchors, showsMuscleBellies, skeleton, useStudio } from '../editor/store';
import { activeCapabilities, useCharacter } from '../editor/characterStore';
import { resolveFrame } from '../animation/pipeline';
import { EULER_ORDER } from '../rig/types';
import { clampRotation } from '../rig/pose';
import { toDeg } from '../core/math';
import { restWorldQuaternion } from '../ik/orient';
import { createSceneState, SceneStateContext, useSceneState } from './sceneState';
import { SkeletonView } from './SkeletonView';
import { CharacterFigure } from './CharacterFigure';
import { MuscleView } from './MuscleView';
import { EquipmentView } from './EquipmentView';
import { IKHandles } from './IKHandles';
import { resolveCamera } from './cameras';
import { advancePlaybackTime } from '../editor/playback';
import { equipmentSocketForInstance } from '../equipment/library';

/**
 * Advances playback and resolves the frame, once per rendered frame and before
 * anything else in the scene reads it.
 */
function FrameDriver() {
  const scene = useSceneState();
  const clip = useStudio((state) => state.document.clip);
  const anchors = useMemo(() => currentAnchors(clip), [clip]);

  useFrame((_, delta) => {
    const store = useStudio.getState();
    let time = store.time;
    if (store.playing) {
      const advanced = advancePlaybackTime(
        time,
        Math.min(delta, 0.1) * store.speed,
        clip.duration,
        store.loop,
        store.loopRange,
      );
      time = advanced.time;
      if (advanced.ended) store.pause();
      store.setTime(time);
    }
    scene.frame = resolveFrame(skeleton, scene.evaluation, clip, time, { anchors });
    scene.evaluation.apply(scene.frame.pose);
  }, -1);

  return null;
}

/** Moves the camera to the selected preset, then hands control back to orbit. */
function CameraRig({ controls }: { controls: React.RefObject<OrbitControlsImpl | null> }) {
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

  useFrame((_, delta) => {
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
  });

  return null;
}

/**
 * The transform gizmo. On a joint it rotates that joint within its anatomical
 * limits; on an IK handle it drags the target or pole. Both write through the
 * store, so every gizmo move is undoable like any other edit.
 */
function Gizmo() {
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
  const { scene: root } = useThree();

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

  useFrame(() => {
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
  });

  const target = selection.bone || editableEquipment ? proxy : null;
  if (!target) return null;

  return (
    <TransformControls
      object={target}
      mode={gizmoMode === 'translate' ? 'translate' : 'rotate'}
      size={0.8}
      onMouseDown={() => {
        dragging.current = true;
      }}
      onMouseUp={() => {
        dragging.current = false;
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
function HandleGizmo() {
  const selection = useStudio((state) => state.selection.handle);
  const setIKTarget = useStudio((state) => state.setIKTarget);
  const scene = useSceneState();
  const [proxy] = useState(() => new Object3D());
  const dragging = useRef(false);
  const { scene: root } = useThree();
  const clip = useStudio((state) => state.document.clip);
  const time = useStudio((state) => state.time);

  useEffect(() => {
    root.add(proxy);
    return () => {
      root.remove(proxy);
    };
  }, [root, proxy]);

  useFrame(() => {
    if (dragging.current || !selection) return;
    const frame = scene.frame;
    if (!frame) return;
    const goal = sampleGoal(clip, time, selection.chain);
    if (!goal) return;
    const point = selection.kind === 'target' ? goal.target : goal.pole;
    proxy.position.set(point.x, point.y, point.z);
  });

  if (!selection) return null;

  return (
    <TransformControls
      object={proxy}
      mode="translate"
      size={0.6}
      onMouseDown={() => {
        dragging.current = true;
      }}
      onMouseUp={() => {
        dragging.current = false;
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

export function Viewport() {
  const scene = useMemo(createSceneState, []);
  const controls = useRef<OrbitControlsImpl | null>(null);
  const showGrid = useStudio((state) => state.showGrid);
  const selectBone = useStudio((state) => state.selectBone);
  const backdrop = BACKDROPS[useStudio((state) => state.backdrop)];

  return (
    <SceneStateContext.Provider value={scene}>
      <Canvas
        shadows
        dpr={[1, 2]}
        camera={{ position: [2.3, 1.35, 2.7], fov: 38, near: 0.05, far: 100 }}
        onPointerMissed={() => selectBone(null)}
      >
        <color attach="background" args={[backdrop.background]} />
        <hemisphereLight
          intensity={backdrop.lighting.ambient}
          groundColor={backdrop.ground}
          color="#f0f4fb"
        />
        <directionalLight
          position={[3, 5, 4]}
          intensity={backdrop.lighting.key}
          castShadow={!backdrop.floorless}
          shadow-mapSize={[1024, 1024]}
          shadow-camera-left={-3}
          shadow-camera-right={3}
          shadow-camera-top={3}
          shadow-camera-bottom={-3}
        />
        <directionalLight
          position={[-3, 2.5, -2]}
          intensity={backdrop.lighting.rim}
          color={backdrop.lighting.rimColour}
        />

        <FrameDriver />
        <Figure />
        <Gizmo />
        <HandleGizmo />

        {showGrid && !backdrop.floorless && (
          <Grid
            args={[12, 12]}
            cellSize={0.25}
            cellColor={backdrop.cell}
            sectionSize={1}
            sectionColor={backdrop.section}
            fadeDistance={14}
            infiniteGrid
            position={[0, 0.001, 0]}
          />
        )}
        {!backdrop.floorless && (
          <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
            <planeGeometry args={[24, 24]} />
            <meshStandardMaterial color={backdrop.ground} roughness={0.95} />
          </mesh>
        )}

        <OrbitControls
          ref={controls}
          makeDefault
          target={[0, 1.0, 0]}
          minDistance={0.6}
          maxDistance={12}
          enableDamping
          dampingFactor={0.12}
        />
        <CameraRig controls={controls} />
      </Canvas>
    </SceneStateContext.Provider>
  );
}
