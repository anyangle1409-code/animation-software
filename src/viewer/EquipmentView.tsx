import { useEffect, useMemo } from 'react';
import { useStudio } from '../editor/store';
import { useCharacter } from '../editor/characterStore';
import { resolveEquipmentDisplayTransforms } from './equipmentDisplayTransforms';
import {
  applyEquipmentDisplayTransforms,
  createEquipmentScene,
  registerEquipmentPointers,
} from './equipmentScene';
import { SCENE_FRAME_PRIORITY, useSceneFrame, useSceneState } from './sceneState';
import { SceneObjectMount } from './SceneObjectMount';
import { useSceneResourceDisposal } from './sceneResourceLifecycle';
import { useSceneHostBindings } from './sceneHostBindings';

/**
 * Equipment placed by the frame pipeline and mounted directly through the
 * shared first-party scene/pointer ports.
 */
export function EquipmentView() {
  const scene = useSceneState();
  const instances = useStudio((state) => state.document.clip.equipment);
  const selectEquipment = useStudio((state) => state.selectEquipment);
  const character = useCharacter((state) => state.active);
  const { pointers } = useSceneHostBindings();
  const resources = useMemo(() => createEquipmentScene(instances), [instances]);

  useSceneResourceDisposal(resources);

  useEffect(
    () => registerEquipmentPointers(resources, pointers, selectEquipment),
    [resources, pointers, selectEquipment],
  );

  useSceneFrame(() => {
    const transforms = scene.frame?.equipment;
    if (!transforms) return;
    applyEquipmentDisplayTransforms(
      resources,
      resolveEquipmentDisplayTransforms(instances, transforms, character),
    );
  }, SCENE_FRAME_PRIORITY.equipment);

  return <SceneObjectMount object={resources.group} />;
}
