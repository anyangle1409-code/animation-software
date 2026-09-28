import { useEffect, useRef } from 'react';
import { characterStore } from '../editor/characterStoreCore';
import { skeleton, studioStore } from '../editor/storeCore';
import { useSceneState } from './sceneState';
import { createFirstPartyViewportRuntime } from './firstPartyViewportRuntime';
import { createStudioSceneController } from './studioSceneController';

/**
 * Temporary React DOM mount wrapper around the project-owned viewport/runtime.
 *
 * React owns only the container/canvas refs and effect lifetime. Renderer,
 * frame, pointer and complete Studio scene composition are plain TypeScript.
 */
export function FirstPartyViewportHost() {
  const scene = useSceneState();
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const runtime = createFirstPartyViewportRuntime(container, canvas, scene);
    const controller = createStudioSceneController({
      sceneState: scene,
      bindings: runtime.bindings,
      studioStore,
      characterStore,
      skeleton,
    });

    return () => {
      controller.dispose();
      runtime.dispose();
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
    </div>
  );
}
