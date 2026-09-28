import { useMemo } from 'react';
import { createSceneState, SceneStateContext } from './sceneState';
import { R3FViewportHost } from './R3FViewportHost';
import { FirstPartyViewportHost } from './FirstPartyViewportHost';
import { viewportHostFromSearch } from './viewportHostSelection';

/**
 * Host-agnostic viewport entry point.
 *
 * R3F remains the default parity reference until the first-party path passes
 * the same browser/physical gates. The query switch is deliberately reversible.
 */
export function Viewport() {
  const scene = useMemo(createSceneState, []);
  const host = viewportHostFromSearch(
    typeof window === 'undefined' ? '' : window.location.search,
  );
  const Host = host === 'first-party' ? FirstPartyViewportHost : R3FViewportHost;

  return (
    <SceneStateContext.Provider value={scene}>
      <Host />
    </SceneStateContext.Provider>
  );
}
