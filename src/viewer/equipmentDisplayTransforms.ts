import { Matrix4 } from 'three';
import type { CharacterBuild } from '../character/types';
import {
  anatomicalGripOffset,
  cableMatrix,
  socketWorldPoint,
  twoHandAttachmentMatrix,
} from '../equipment/attach';
import type { EquipmentTransform } from '../equipment/attach';
import { equipmentSocketForInstance } from '../equipment/library';
import { reflectPlacement } from '../equipment/mirror';
import type { EquipmentInstance } from '../equipment/types';
import { handAttachmentMatrix } from '../export/clipBuilder';

export type EquipmentDisplayCharacter = Pick<
  CharacterBuild,
  'handMatrix' | 'gripOffset' | 'mirrored'
>;

export interface EquipmentDisplayTransform {
  readonly visible: boolean;
  readonly matrix: Matrix4 | null;
}

/**
 * Resolve the matrices actually drawn by EquipmentView without depending on
 * React or R3F. This is intentionally still a temporary Three boundary:
 * Three.js is removed later, after R3F and React/ReactDOM.
 *
 * The distinction from the canonical frame equipment map matters for
 * proportion-aware characters. A held item follows the character's own hand,
 * a mirrored character reflects canonical world placements, and a cable joins
 * the item placements that are actually drawn rather than stale canonical
 * endpoints.
 */
export function resolveEquipmentDisplayTransforms(
  instances: readonly EquipmentInstance[],
  transforms: ReadonlyMap<string, Pick<EquipmentTransform, 'matrix'>>,
  character: EquipmentDisplayCharacter | null | undefined,
): Map<string, EquipmentDisplayTransform> {
  const drawn = new Map<string, EquipmentDisplayTransform>();
  const visibleInstances = instances.filter((instance) => instance.visible);
  const byId = new Map(visibleInstances.map((instance) => [instance.id, instance]));

  for (const instance of visibleInstances) {
    if (instance.attachment.mode === 'cable') continue;

    if (instance.attachment.mode === 'hand' && character?.handMatrix) {
      const held = character.handMatrix(instance.attachment.side, new Matrix4());
      if (held) {
        const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
        const grip =
          instance.attachment.gripOffset ??
          character.gripOffset?.(instance.attachment.side) ??
          anatomicalGripOffset(instance.attachment.side);
        const local = handAttachmentMatrix(
          grip,
          socket?.position ?? { x: 0, y: 0, z: 0 },
          {
            gripRotation: instance.attachment.gripRotation,
            socketRotation: socket?.rotation,
          },
        );
        drawn.set(instance.id, {
          visible: true,
          matrix: new Matrix4().multiplyMatrices(held, local),
        });
        continue;
      }
    }

    if (instance.attachment.mode === 'hands' && character?.handMatrix) {
      const left = character.handMatrix('l', new Matrix4());
      const right = character.handMatrix('r', new Matrix4());
      const matrix = left && right ? twoHandAttachmentMatrix(left, right, instance) : null;
      if (matrix) {
        drawn.set(instance.id, { visible: true, matrix });
        continue;
      }
    }

    const canonical = transforms.get(instance.id);
    if (!canonical) {
      drawn.set(instance.id, { visible: false, matrix: null });
      continue;
    }

    drawn.set(instance.id, {
      visible: true,
      matrix: character?.mirrored
        ? reflectPlacement(canonical.matrix, new Matrix4())
        : canonical.matrix.clone(),
    });
  }

  // Cables are deliberately second-pass: they join the placements that will
  // actually be drawn, including character-hand corrections and mirroring.
  for (const instance of visibleInstances) {
    if (instance.attachment.mode !== 'cable') continue;

    const end = (link: { equipment: string; socket: string }) => {
      const item = byId.get(link.equipment);
      const placement = drawn.get(link.equipment);
      return item && placement?.visible && placement.matrix
        ? socketWorldPoint(item, link.socket, placement.matrix)
        : null;
    };

    const from = end(instance.attachment.from);
    const to = end(instance.attachment.to);
    drawn.set(
      instance.id,
      from && to
        ? { visible: true, matrix: cableMatrix(from, to).matrix }
        : { visible: false, matrix: null },
    );
  }

  return drawn;
}
