import { useEffect } from 'react';
import { studioStore } from '../editor/store';
import { useSceneState } from './sceneState';
import { useSceneHostBindings } from './sceneHostBindings';
import { createMuscleViewRuntime } from './muscleViewRuntime';

/** Temporary React adapter over the framework-neutral muscle runtime. */
export function MuscleView() {
  const sceneState = useSceneState();
  const { scene: root } = useSceneHostBindings();

  useEffect(() => {
    const runtime = createMuscleViewRuntime({
      sceneState,
      root,
      store: studioStore,
    });
    return () => runtime.dispose();
  }, [sceneState, root]);

  return null;
}
