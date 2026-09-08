import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import { Group } from 'three';
import { useStudio } from '../editor/store';
import { EquipmentMesh } from './equipmentMeshes';
import { useSceneState } from './sceneState';

/**
 * Equipment placed by the frame pipeline. The transforms come from the
 * attachment solver, so a dumbbell is where the hand puts it — the mesh here
 * never guesses.
 */
export function EquipmentView() {
  const scene = useSceneState();
  const instances = useStudio((state) => state.document.clip.equipment);
  const selectEquipment = useStudio((state) => state.selectEquipment);
  const groups = useRef(new Map<string, Group>());

  useFrame(() => {
    const transforms = scene.frame?.equipment;
    if (!transforms) return;
    for (const [id, group] of groups.current) {
      const transform = transforms.get(id);
      if (!transform) {
        group.visible = false;
        continue;
      }
      group.visible = true;
      group.matrix.copy(transform.matrix);
      group.matrixWorldNeedsUpdate = true;
    }
  });

  return (
    <>
      {instances
        .filter((instance) => instance.visible)
        .map((instance) => (
          <group
            key={instance.id}
            matrixAutoUpdate={false}
            onPointerDown={(event) => {
              event.stopPropagation();
              selectEquipment(instance.id);
            }}
            ref={(group) => {
              if (group) groups.current.set(instance.id, group);
              else groups.current.delete(instance.id);
            }}
          >
            <EquipmentMesh kind={instance.kind} />
          </group>
        ))}
    </>
  );
}
