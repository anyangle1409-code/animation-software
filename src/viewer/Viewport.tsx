import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Grid, OrbitControls, TransformControls } from '@react-three/drei';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Euler, Object3D, Quaternion, Vector3 } from 'three';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { currentAnchors, skeleton, useStudio } from '../editor/store';
import { useCharacter } from '../editor/characterStore';
import { resolveFrame } from '../animation/pipeline';
import { EULER_ORDER } from '../rig/types';
import { clampRotation } from '../rig/pose';
import { restWorldQuaternion } from '../ik/orient';
import { createSceneState, SceneStateContext, useSceneState } from './sceneState';
import { SkeletonView } from './SkeletonView';
import { MannequinView } from './MannequinView';
import { CharacterView } from './CharacterView';
import { MuscleView } from './MuscleView';
import { EquipmentView } from './EquipmentView';
import { IKHandles } from './IKHandles';
import { resolveCamera } from './cameras';
import { applyRetarget } from '../retargeting/retarget';
import { resolveRetargetedEquipment } from '../equipment/attach';

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
      time += Math.min(delta, 0.1) * store.speed;
      if (time >= clip.duration) {
        if (store.loop) time %= clip.duration;
        else {
          time = clip.duration;
          store.pause();
        }
      }
      store.setTime(time);
    }
    scene.frame = resolveFrame(skeleton, scene.evaluation, clip, time, { anchors });
    scene.evaluation.apply(scene.frame.pose);

    // When the real character is visible, drive it first and derive equipment
    // from its retargeted hands rather than from the mannequin's proportions.
    const character = useCharacter.getState();
    if (store.viewMode === 'character' && character.binding) {
      applyRetarget(character.binding, scene.frame.pose);
      scene.frame.equipment = resolveRetargetedEquipment(
        character.binding,
        clip.equipment,
      );
    }
  }, -1);

  return null;
}

/** Moves the camera to the selected preset, then hands control back to orbit. */
function CameraRig({ controls }: { controls: React.RefObject<OrbitControlsImpl | null> }) {
  const preset = useStudio((state) => state.camera);
  const recommendation = useStudio((state) => state.document.exercise.camera);
  const { camera } = useThree();
  const goal = useRef<{ position: Vector3; target: Vector3; fov: number } | null>(null);

  useEffect(() => {
    const setup = resolveCamera(preset, recommendation);
    goal.current = setup
      ? { position: setup.position.clone(), target: setup.target.clone(), fov: setup.fov }
      : null;
  }, [preset, recommendation]);

  useFrame((_, delta) => {
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
  const [proxy] = useState(() => new Object3D());
  const dragging = useRef(false);
  const { scene: root } = useThree();

  useEffect(() => {
    root.add(proxy);
    return () => {
      root.remove(proxy);
    };
  }, [root, proxy]);

  useFrame(() => {
    if (dragging.current) return;
    if (!selection.bone) return;
    proxy.position.copy(scene.evaluation.head(selection.bone, new Vector3()));
    proxy.quaternion.copy(scene.evaluation.quaternion(selection.bone));
  });

  const target = selection.bone ? proxy : null;
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
        const bone = useStudio.getState().selection.bone;
        if (!bone) return;
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
  const hasCharacter = useCharacter((state) => state.binding !== null);

  return (
    <>
      {(viewMode === 'skeleton' || viewMode === 'combined') && (
        <SkeletonView ghosted={viewMode === 'combined'} />
      )}
      {(viewMode === 'muscles' || viewMode === 'combined') && <MuscleView />}
      {viewMode === 'character' && (hasCharacter ? <CharacterView /> : <MannequinView />)}
      {viewMode === 'muscles' && (
        <MannequinView opacity={0.1} colour="#93a2b8" depthWrite={false} />
      )}
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

  return (
    <SceneStateContext.Provider value={scene}>
      <Canvas
        shadows
        dpr={[1, 2]}
        camera={{ position: [2.3, 1.35, 2.7], fov: 38, near: 0.05, far: 100 }}
        onPointerMissed={() => selectBone(null)}
      >
        <color attach="background" args={['#12151a']} />
        <hemisphereLight intensity={0.55} groundColor="#20242c" color="#dfe8f5" />
        <directionalLight
          position={[3, 5, 4]}
          intensity={1.5}
          castShadow
          shadow-mapSize={[1024, 1024]}
          shadow-camera-left={-3}
          shadow-camera-right={3}
          shadow-camera-top={3}
          shadow-camera-bottom={-3}
        />
        <directionalLight position={[-3, 2.5, -2]} intensity={0.45} color="#9fc4ff" />

        <FrameDriver />
        <Figure />
        <Gizmo />
        <HandleGizmo />

        {showGrid && (
          <Grid
            args={[12, 12]}
            cellSize={0.25}
            cellColor="#2a313c"
            sectionSize={1}
            sectionColor="#3d4756"
            fadeDistance={14}
            infiniteGrid
            position={[0, 0.001, 0]}
          />
        )}
        <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[24, 24]} />
          <meshStandardMaterial color="#171b21" roughness={0.95} />
        </mesh>

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
