import { useEffect } from 'react';
import { skeleton, studioStore } from '../editor/store';
import { useSceneState } from './sceneState';
import { useSceneHostBindings } from './sceneHostBindings';
import { createSkeletonViewRuntime } from './skeletonViewRuntime';

export interface SkeletonViewProps {
  /** Dim the skeleton when it sits behind the muscle or character layer. */
  ghosted?: boolean;
  includeFingers?: boolean;
}

/** Temporary React adapter over the framework-neutral skeleton runtime. */
export function SkeletonView({
  ghosted = false,
  includeFingers = false,
}: SkeletonViewProps) {
  const sceneState = useSceneState();
  const { scene: root, pointers } = useSceneHostBindings();

  useEffect(() => {
    const runtime = createSkeletonViewRuntime({
      sceneState,
      root,
      pointers,
      store: studioStore,
      skeleton,
      ghosted,
      includeFingers,
    });
    return () => runtime.dispose();
  }, [sceneState, root, pointers, ghosted, includeFingers]);

  return null;
}
