import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useEffect, useMemo, useRef } from 'react';
import { currentAnchors, skeleton, useStudio } from '../editor/store';
import { useSceneState } from './sceneState';
import { driveSceneFrame } from './sceneFrameDriver';
import { SceneHostBindingsProvider } from './sceneHostBindings';
import { HgScenePointerRouter } from './scenePointerRouter';
import { StudioSceneContent } from './StudioSceneContent';

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

export function R3FViewportHost() {
  const selectBone = useStudio((state) => state.selectBone);
  const pointerRouter = useRef<HgScenePointerRouter | null>(null);

  return (
    <Canvas
      shadows
      dpr={[1, 2]}
      camera={{ position: [2.3, 1.35, 2.7], fov: 38, near: 0.05, far: 100 }}
      onPointerMissed={(event) => {
        if (pointerRouter.current?.hitsRegisteredTarget(event.clientX, event.clientY)) return;
        selectBone(null);
      }}
    >
      <R3FHostBindingsWithRef pointerRouter={pointerRouter}>
        <FrameDriver />
        <StudioSceneContent />
      </R3FHostBindingsWithRef>
    </Canvas>
  );
}

function R3FHostBindingsWithRef({
  children,
  pointerRouter,
}: {
  children: React.ReactNode;
  pointerRouter: React.MutableRefObject<HgScenePointerRouter | null>;
}) {
  const { camera, scene, gl } = useThree();
  const pointers = useMemo(
    () => new HgScenePointerRouter(camera, scene, gl.domElement),
    [camera, scene, gl.domElement],
  );

  useEffect(() => {
    pointerRouter.current = pointers;
    pointers.mount();
    return () => {
      if (pointerRouter.current === pointers) pointerRouter.current = null;
      pointers.dispose();
    };
  }, [pointerRouter, pointers]);

  const value = useMemo(
    () => ({ camera, scene, element: gl.domElement, pointers }),
    [camera, scene, gl.domElement, pointers],
  );

  return <SceneHostBindingsProvider value={value}>{children}</SceneHostBindingsProvider>;
}
