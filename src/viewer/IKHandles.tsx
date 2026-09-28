import { useEffect } from 'react';
import { studioStore } from '../editor/store';
import { useSceneState } from './sceneState';
import { useSceneHostBindings } from './sceneHostBindings';
import { createIKHandlesRuntime } from './ikHandlesRuntime';

/** Temporary React adapter over the framework-neutral IK-handle runtime. */
export function IKHandles() {
  const sceneState = useSceneState();
  const { scene: root, pointers } = useSceneHostBindings();

  useEffect(() => {
    const runtime = createIKHandlesRuntime({
      sceneState,
      root,
      pointers,
      store: studioStore,
    });
    return () => runtime.dispose();
  }, [sceneState, root, pointers]);

  return null;
}
