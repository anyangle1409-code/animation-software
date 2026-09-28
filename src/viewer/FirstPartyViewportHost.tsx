import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ACESFilmicToneMapping,
  PCFSoftShadowMap,
  SRGBColorSpace,
  WebGLRenderer,
} from 'three';
import { browserFrameScheduler } from '../core/frameLoop';
import { browserSceneSurface } from '../core/browserSceneSurface';
import { currentAnchors, skeleton, useStudio } from '../editor/store';
import { useSceneState } from './sceneState';
import { driveSceneFrame } from './sceneFrameDriver';
import {
  SceneHostBindingsProvider,
  type SceneHostBindings,
} from './sceneHostBindings';
import { HgScenePointerRouter } from './scenePointerRouter';
import { ThreeSceneHost } from './threeSceneHost';
import { StudioSceneContent } from './StudioSceneContent';

/**
 * Reversible project-owned Studio host.
 *
 * React is still used for editor/component lifecycle at this stage, but the
 * canvas, WebGL renderer, scene/camera lifecycle, frame clock and pointer
 * router are all outside R3F.
 */
export function FirstPartyViewportHost() {
  const scene = useSceneState();
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [bindings, setBindings] = useState<SceneHostBindings | null>(null);

  const clip = useStudio((state) => state.document.clip);
  const anchors = useMemo(() => currentAnchors(clip), [clip]);
  const clipRef = useRef(clip);
  const anchorsRef = useRef(anchors);
  clipRef.current = clip;
  anchorsRef.current = anchors;

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const renderer = new WebGLRenderer({ canvas, antialias: true });
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = PCFSoftShadowMap;
    renderer.outputColorSpace = SRGBColorSpace;
    renderer.toneMapping = ACESFilmicToneMapping;

    const host = new ThreeSceneHost(
      browserFrameScheduler(),
      browserSceneSurface(canvas, container),
      renderer,
    );

    const pointers = new HgScenePointerRouter(
      host.camera,
      host.scene,
      canvas,
      () => useStudio.getState().selectBone(null),
    );
    pointers.mount();

    const removeFrame = host.onFrame((frame) => {
      driveSceneFrame({
        scene,
        skeleton,
        clip: clipRef.current,
        anchors: anchorsRef.current,
        playback: useStudio.getState(),
        frame,
      });
    }, -1);

    setBindings({
      camera: host.camera,
      scene: host.scene,
      element: canvas,
      pointers,
    });
    host.mount();

    return () => {
      removeFrame();
      pointers.dispose();
      host.dispose();
    };
  }, [scene]);

  return (
    <div
      ref={containerRef}
      data-hgpt-scene-host="first-party"
      style={{ width: '100%', height: '100%', minHeight: 0, position: 'relative' }}
    >
      <canvas
        ref={canvasRef}
        style={{ display: 'block', width: '100%', height: '100%' }}
      />
      {bindings && (
        <SceneHostBindingsProvider value={bindings}>
          <StudioSceneContent />
        </SceneHostBindingsProvider>
      )}
    </div>
  );
}
