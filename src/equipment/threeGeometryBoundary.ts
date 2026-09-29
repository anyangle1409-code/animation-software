import {
  BoxGeometry,
  BufferGeometry,
  CylinderGeometry,
  Euler,
  Group,
  Matrix4,
  Mesh,
  MeshStandardMaterial,
  Object3D,
  Quaternion,
  SphereGeometry,
  TorusGeometry,
  Vector3,
} from 'three';
import { equipmentParts, MATERIALS, type Part } from './geometry';
import type { EquipmentKind } from './types';

export type EquipmentThreeEuler = Euler;
export type EquipmentThreeGroup = Group;
export type EquipmentThreeMatrix4 = Matrix4;
export type EquipmentThreeMesh = Mesh<BufferGeometry, MeshStandardMaterial>;
export type EquipmentThreeObject = Object3D;
export type EquipmentThreeVector3 = Vector3;

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

export function createThreeEquipmentPartMesh(
  part: Part,
  castShadow = false,
): EquipmentThreeMesh {
  const mesh = new Mesh(
    geometryForPart(part),
    new MeshStandardMaterial(MATERIALS[part.material]),
  );
  const position = part.position ?? [0, 0, 0];
  const rotation = 'rotation' in part ? part.rotation ?? [0, 0, 0] : [0, 0, 0];
  mesh.position.set(position[0], position[1], position[2]);
  mesh.rotation.set(rotation[0], rotation[1], rotation[2]);
  mesh.castShadow = castShadow;
  return mesh;
}

export function createThreeEquipmentGroup(
  name: string,
  matrixAutoUpdate = true,
): EquipmentThreeGroup {
  const group = new Group();
  group.name = name;
  group.matrixAutoUpdate = matrixAutoUpdate;
  return group;
}

export function isThreeEquipmentMesh(object: Object3D): object is EquipmentThreeMesh {
  return object instanceof Mesh;
}

export function buildThreeEquipmentObject(
  kind: EquipmentKind,
  backAngle?: number,
): EquipmentThreeObject {
  const group = new Object3D();
  group.name = kind;
  for (const part of equipmentParts(kind, backAngle)) {
    group.add(createThreeEquipmentPartMesh(part));
  }
  return group;
}

export function composeThreeEquipmentMatrix(
  position: EquipmentThreeVector3,
  rotation: EquipmentThreeEuler,
  target = new Matrix4(),
): EquipmentThreeMatrix4 {
  return target.compose(
    position,
    new Quaternion().setFromEuler(rotation),
    new Vector3(1, 1, 1),
  );
}
