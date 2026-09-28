import { useMemo } from 'react';
import { createSceneState, SceneStateContext } from './sceneState';
import { FirstPartyViewportHost } from './FirstPartyViewportHost';

/** First-party Studio viewport entry point. */
export function Viewport() {
  const scene = useMemo(createSceneState, []);

  return (
    <SceneStateContext.Provider value={scene}>
      <FirstPartyViewportHost />
    </SceneStateContext.Provider>
  );
}
