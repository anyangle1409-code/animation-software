import {
  BoxGeometry,
  BufferGeometry,
  CylinderGeometry,
  Euler,
  Matrix4,
  Mesh,
  MeshStandardMaterial,
  Object3D,
  Quaternion,
  SphereGeometry,
  TorusGeometry,
  Vector3,
} from 'three';
import { EQUIPMENT_PARTS, MATERIALS } from '../equipment/geometry';
import type { Part } from '../equipment/geometry';
import type { EquipmentKind } from '../equipment/types';

/**
 * The character itself lives in `body/`, because the viewport builds the same
 * mesh from the same profiles — what the studio shows is what the file holds.
 */
export { buildSkinnedRig, MANNEQUIN_NAME } from '../body/skin';
export type { BuiltRig } from '../body/skin';

/** Build a plain three.js object for a piece of equipment, from the shared data. */
export function buildEquipmentObject(kind: EquipmentKind): Object3D {
  const group = new Object3D();
  group.name = kind;
  for (const part of EQUIPMENT_PARTS[kind]) {
    const material = new MeshStandardMaterial(MATERIALS[part.material]);
    const mesh = new Mesh(geometryForPart(part), material);
    const position = part.position ?? [0, 0, 0];
    mesh.position.set(position[0], position[1], position[2]);
    const rotation = 'rotation' in part ? part.rotation : undefined;
    if (rotation) mesh.rotation.set(rotation[0], rotation[1], rotation[2]);
    group.add(mesh);
  }
  return group;
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

export const composeMatrix = (
  position: Vector3,
  rotation: Euler,
  target = new Matrix4(),
): Matrix4 => target.compose(position, new Quaternion().setFromEuler(rotation), new Vector3(1, 1, 1));
