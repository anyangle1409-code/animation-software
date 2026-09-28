import { useMemo } from 'react';
import { createSceneState, SceneStateContext } from './sceneState';
import { R3FViewportHost } from './R3FViewportHost';

/**
 * Host-agnostic viewport entry point.
 *
 * Scene state ownership lives here so the current R3F host and the future
 * first-party host consume the same evaluation/frame/consumer contract.
 */
export function Viewport() {
  const scene = useMemo(createSceneState, []);
  return (
    <SceneStateContext.Provider value={scene}>
      <R3FViewportHost />
    </SceneStateContext.Provider>
  );
}
