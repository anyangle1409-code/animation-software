import {
  BoxGeometry,
  BufferGeometry,
  CylinderGeometry,
  Group,
  Mesh,
  MeshStandardMaterial,
  SphereGeometry,
  TorusGeometry,
} from 'three';
import { equipmentParts, MATERIALS, type Part } from '../equipment/geometry';
import type { EquipmentInstance } from '../equipment/types';
import type { EquipmentDisplayTransform } from './equipmentDisplayTransforms';
import type { HgScenePointerRouter } from './scenePointerRouter';

export interface EquipmentSceneResources {
  group: Group;
  instances: ReadonlyMap<string, Group>;
  dispose(): void;
}

function geometryForPart(part: Part): BufferGeometry {
  switch (part.shape) {
    case 'cylinder':
      return new CylinderGeometry(
        part.radiusTop ?? part.radius,
        part.radius,
        part.length,
        part.segments ?? 16,
      );
    case 'box':
      return new BoxGeometry(...part.size);
    case 'sphere':
      return new SphereGeometry(part.radius, 16, 12);
    case 'torus':
      return new TorusGeometry(part.radius, part.tube, 10, 24, part.arc ?? Math.PI * 2);
  }
}

function partMesh(part: Part): Mesh<BufferGeometry, MeshStandardMaterial> {
  const spec = MATERIALS[part.material];
  const mesh = new Mesh(
    geometryForPart(part),
    new MeshStandardMaterial(spec),
  );
  const position = part.position ?? [0, 0, 0];
  const rotation = 'rotation' in part ? part.rotation ?? [0, 0, 0] : [0, 0, 0];
  mesh.position.set(position[0], position[1], position[2]);
  mesh.rotation.set(rotation[0], rotation[1], rotation[2]);
  mesh.castShadow = true;
  return mesh;
}

/** Build visible equipment meshes as owned Three objects, independent of R3F JSX. */
export function createEquipmentScene(
  instances: readonly EquipmentInstance[],
): EquipmentSceneResources {
  const root = new Group();
  root.name = 'hgpt-equipment-view';
  const groups = new Map<string, Group>();

  for (const instance of instances) {
    if (!instance.visible) continue;
    const group = new Group();
    group.name = `hgpt-equipment-${instance.id}`;
    group.matrixAutoUpdate = false;
    for (const part of equipmentParts(instance.kind, instance.backAngle)) {
      group.add(partMesh(part));
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
          if (!(child instanceof Mesh)) continue;
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
