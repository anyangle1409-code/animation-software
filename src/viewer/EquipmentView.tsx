import { useFrame } from '@react-three/fiber';
import { useMemo, useRef } from 'react';
import { Group, Matrix4 } from 'three';
import { useStudio } from '../editor/store';
import { useCharacter } from '../editor/characterStore';
import { equipmentSocketForInstance } from '../equipment/library';
import { handAttachmentMatrix } from '../export/clipBuilder';
import { EquipmentMesh } from './equipmentMeshes';
import { useSceneState } from './sceneState';

/**
 * Equipment placed by the frame pipeline. The transforms come from the
 * attachment solver, so a dumbbell is where the hand puts it — the mesh here
 * never guesses.
 *
 * One exception, and it is the point of the character layer: a character that
 * kept its own skeleton has its own proportions, so its hand is not where the
 * canonical hand is. For those, a hand-held item follows the character's hand
 * instead — through the same grip offsets, restated in the canonical hand's
 * frame by the character itself.
 */
export function EquipmentView() {
  const scene = useSceneState();
  const instances = useStudio((state) => state.document.clip.equipment);
  const selectEquipment = useStudio((state) => state.selectEquipment);
  const character = useCharacter((state) => state.active);
  const groups = useRef(new Map<string, Group>());
  const scratch = useMemo(() => ({ hand: new Matrix4(), local: new Matrix4() }), []);

  useFrame(() => {
    const transforms = scene.frame?.equipment;
    if (!transforms) return;
    for (const [id, group] of groups.current) {
      const instance = instances.find((entry) => entry.id === id);
      const transform = transforms.get(id);

      // The character's own hand, when it has one of its own.
      const held =
        instance?.attachment.mode === 'hand' && character?.handMatrix
          ? character.handMatrix(instance.attachment.side, scratch.hand)
          : null;

      if (held && instance?.attachment.mode === 'hand') {
        const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
        const grip = instance.attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };
        scratch.local.copy(handAttachmentMatrix(grip, socket?.position ?? { x: 0, y: 0, z: 0 }));
        group.visible = true;
        group.matrix.multiplyMatrices(held, scratch.local);
        group.matrixWorldNeedsUpdate = true;
        continue;
      }

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
