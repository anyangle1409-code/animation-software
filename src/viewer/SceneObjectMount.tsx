import { useEffect } from 'react';
import type { Object3D } from 'three';
import { useSceneHostBindings } from './sceneHostBindings';

/** Mount an owned Three object directly through the shared host scene port. */
export function SceneObjectMount({ object }: { object: Object3D }) {
  const { scene } = useSceneHostBindings();

  useEffect(() => {
    scene.add(object);
    return () => {
      scene.remove(object);
    };
  }, [scene, object]);

  return null;
}
