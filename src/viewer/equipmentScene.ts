import { equipmentParts } from '../equipment/geometry';
import type { EquipmentInstance } from '../equipment/types';
import {
  createThreeEquipmentGroup,
  createThreeEquipmentPartMesh,
  isThreeEquipmentMesh,
  type EquipmentThreeGroup,
} from '../equipment/threeGeometryBoundary';
import type { EquipmentDisplayTransform } from './equipmentDisplayTransforms';
import type { HgScenePointerRouter } from './scenePointerRouter';

export interface EquipmentSceneResources {
  group: EquipmentThreeGroup;
  instances: ReadonlyMap<string, EquipmentThreeGroup>;
  dispose(): void;
}

/** Build visible equipment meshes as owned compatibility objects, independent of R3F JSX. */
export function createEquipmentScene(
  instances: readonly EquipmentInstance[],
): EquipmentSceneResources {
  const root = createThreeEquipmentGroup('hgpt-equipment-view');
  const groups = new Map<string, EquipmentThreeGroup>();

  for (const instance of instances) {
    if (!instance.visible) continue;
    const group = createThreeEquipmentGroup(`hgpt-equipment-${instance.id}`, false);
    for (const part of equipmentParts(instance.kind, instance.backAngle)) {
      group.add(createThreeEquipmentPartMesh(part, true));
    }
    root.add(group);
    groups.set(instance.id, group);
  }

  let disposed = false;
  return {
    group: root,
    instances: groups,
    dispose() {
      if (disposed) return;
      disposed = true;
      for (const group of groups.values()) {
        for (const child of group.children) {
          if (!isThreeEquipmentMesh(child)) continue;
          child.geometry.dispose();
          if (Array.isArray(child.material)) child.material.forEach((material) => material.dispose());
          else child.material.dispose();
        }
        group.clear();
      }
      root.clear();
    },
  };
}

export function applyEquipmentDisplayTransforms(
  resources: EquipmentSceneResources,
  placements: ReadonlyMap<string, EquipmentDisplayTransform>,
): void {
  for (const [id, group] of resources.instances) {
    const placement = placements.get(id);
    group.visible = Boolean(placement?.visible && placement.matrix);
    if (!placement?.visible || !placement.matrix) continue;
    group.matrix.copy(placement.matrix);
    group.matrixWorldNeedsUpdate = true;
  }
}

export function registerEquipmentPointers(
  resources: EquipmentSceneResources,
  pointers: Pick<HgScenePointerRouter, 'register'>,
  select: (id: string) => void,
): () => void {
  const remove: Array<() => void> = [];
  for (const [id, group] of resources.instances) {
    remove.push(
      pointers.register(group, {
        pointerdown: (event) => {
          event.stopPropagation();
          select(id);
        },
      }),
    );
  }
  return () => {
    for (const unregister of remove) unregister();
  };
}
