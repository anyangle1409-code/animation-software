import { HgGroup } from '../core/sceneGraph';
import {
  HgPrimitiveMaterial,
  HgPrimitiveMesh,
} from '../core/sceneMesh';
import { equipmentParts, MATERIALS, type Part } from '../equipment/geometry';
import { equipmentPartPrimitiveData } from '../equipment/primitive';
import type { EquipmentInstance } from '../equipment/types';
import type { EquipmentDisplayTransform } from './equipmentDisplayTransforms';

export interface HgEquipmentInstanceScene {
  readonly group: HgGroup;
  readonly parts: readonly HgPrimitiveMesh[];
}

export interface HgEquipmentSceneResources {
  readonly group: HgGroup;
  readonly instances: ReadonlyMap<string, HgEquipmentInstanceScene>;
  dispose(): void;
}

const partMesh = (part: Part): HgPrimitiveMesh => {
  const surface = MATERIALS[part.material];
  const mesh = new HgPrimitiveMesh(
    equipmentPartPrimitiveData(part),
    new HgPrimitiveMaterial(surface.color, 'lit'),
  );
  const position = part.position ?? [0, 0, 0];
  const rotation = 'rotation' in part ? part.rotation ?? [0, 0, 0] : [0, 0, 0];
  mesh.position.set(position[0], position[1], position[2]);
  mesh.rotation.set(rotation[0], rotation[1], rotation[2]);
  return mesh;
};

/**
 * Project-owned equipment visual scene.
 *
 * This is deliberately parallel to the retained Three adapter for now. It uses
 * the exact shared equipment part data and first-party primitive geometry, so
 * it can be switched into the live WebGL scene renderer once host/pointer
 * parity is ready.
 */
export function createHgEquipmentScene(
  instances: readonly EquipmentInstance[],
): HgEquipmentSceneResources {
  const root = new HgGroup();
  root.name = 'hgpt-equipment-view';
  const groups = new Map<string, HgEquipmentInstanceScene>();

  for (const instance of instances) {
    if (!instance.visible) continue;
    const group = new HgGroup();
    group.name = `hgpt-equipment-${instance.id}`;
    group.matrixAutoUpdate = false;
    const parts = equipmentParts(instance.kind, instance.backAngle).map(partMesh);
    group.add(...parts);
    root.add(group);
    groups.set(instance.id, { group, parts });
  }

  let disposed = false;
  return {
    group: root,
    instances: groups,
    dispose() {
      if (disposed) return;
      disposed = true;
      for (const instance of groups.values()) instance.group.clear();
      groups.clear();
      root.clear();
    },
  };
}

export function applyHgEquipmentDisplayTransforms(
  resources: HgEquipmentSceneResources,
  placements: ReadonlyMap<string, EquipmentDisplayTransform>,
): void {
  for (const [id, instance] of resources.instances) {
    const placement = placements.get(id);
    instance.group.visible = Boolean(placement?.visible && placement.matrix);
    if (!placement?.visible || !placement.matrix) continue;
    instance.group.matrix.copy(placement.matrix);
    instance.group.matrixWorldNeedsUpdate = true;
  }
}
