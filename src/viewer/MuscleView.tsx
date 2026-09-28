import { useEffect, useMemo } from 'react';
import { MUSCLES, createMuscleTransform, resolveMuscle } from '../muscles/model';
import { useStudio } from '../editor/store';
import { SCENE_FRAME_PRIORITY, useSceneFrame, useSceneState } from './sceneState';
import { createMuscleScene } from './muscleScene';
import { SceneObjectMount } from './SceneObjectMount';

/**
 * The muscle overlay. Scene objects are owned directly through the shared host
 * port; R3F is no longer responsible for reconciling this subtree.
 */
export function MuscleView() {
  const scene = useSceneState();
  const involvement = useStudio((state) => state.document.exercise.muscles);
  const resources = useMemo(() => createMuscleScene(involvement), [involvement]);
  const transform = useMemo(createMuscleTransform, []);

  useEffect(() => () => resources.dispose(), [resources]);

  useSceneFrame(() => {
    for (const muscle of MUSCLES) {
      const mesh = resources.meshes.get(muscle.id);
      if (!mesh) continue;
      resolveMuscle(scene.evaluation, muscle, transform);
      mesh.position.copy(transform.position);
      mesh.quaternion.copy(transform.quaternion);
      mesh.scale.copy(transform.scale);
    }
  }, SCENE_FRAME_PRIORITY.muscle);

  return <SceneObjectMount object={resources.group} />;
}
