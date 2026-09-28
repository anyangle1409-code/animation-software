import { useEffect, useRef, useState } from 'react';
import { useSceneState } from './sceneState';
import { SceneHostBindingsProvider } from './sceneHostBindings';
import type { SceneHostBindings } from './sceneHostTypes';
import { createFirstPartyViewportRuntime } from './firstPartyViewportRuntime';
import { StudioSceneContent } from './StudioSceneContent';

/**
 * Temporary React mount wrapper around the project-owned viewport runtime.
 *
 * The renderer/canvas/frame/pointer lifecycle is framework-neutral. React is
 * still used only to own DOM refs and mount the current scene-content adapters.
 */
export function FirstPartyViewportHost() {
  const scene = useSceneState();
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [bindings, setBindings] = useState<SceneHostBindings | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const runtime = createFirstPartyViewportRuntime(container, canvas, scene);
    setBindings(runtime.bindings);
    return () => runtime.dispose();
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
