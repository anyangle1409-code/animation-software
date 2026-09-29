import {
  Bone,
  BufferAttribute,
  BufferGeometry,
  InterleavedBufferAttribute,
  Quaternion,
  Skeleton as ThreeSkeleton,
  Matrix4,
  Material,
  MeshStandardMaterial,
  SkinnedMesh,
  type Object3D,
} from './threeSceneBoundary';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { measureSceneHeight } from './sceneBounds';

export type CharacterBone = Bone;
export type CharacterBufferAttribute = BufferAttribute;
export type CharacterBufferGeometry = BufferGeometry;

export type CharacterMaterial = Material;
export type CharacterStandardMaterial = MeshStandardMaterial;
export type CharacterStandardMaterialParameters =
  ConstructorParameters<typeof MeshStandardMaterial>[0];

export function createCharacterBufferGeometry(): CharacterBufferGeometry {
  return new BufferGeometry();
}

export function createCharacterUint16BufferAttribute(
  values: Uint16Array,
  itemSize: number,
): CharacterBufferAttribute {
  return new BufferAttribute(values, itemSize);
}

export function createCharacterSkinnedMeshObject(
  geometry: CharacterBufferGeometry,
  material: CharacterMaterial,
): CharacterSkinnedMesh {
  return new SkinnedMesh(geometry, material);
}

export function createCharacterStandardMaterialObject(
  parameters?: CharacterStandardMaterialParameters,
): CharacterStandardMaterial {
  return new MeshStandardMaterial(parameters);
}

export function isCharacterStandardMaterial(
  material: unknown,
): material is CharacterStandardMaterial {
  return material instanceof MeshStandardMaterial;
}
export type CharacterInterleavedBufferAttribute = InterleavedBufferAttribute;

export function createCharacterBufferAttribute(
  values: Float32Array,
  itemSize: number,
): CharacterBufferAttribute {
  return new BufferAttribute(values, itemSize);
}
export type CharacterQuaternion = Quaternion;

export function createCharacterQuaternion(
  x = 0,
  y = 0,
  z = 0,
  w = 1,
): CharacterQuaternion {
  return new Quaternion(x, y, z, w);
}

export type CharacterMatrix4 = Matrix4;

export interface CharacterMatrixLike {
  readonly elements: ArrayLike<number>;
}

export function createCharacterMatrix(): CharacterMatrix4 {
  return new Matrix4();
}

export function copyCharacterMatrix(
  source: CharacterMatrixLike,
  target = createCharacterMatrix(),
): CharacterMatrix4 {
  for (let index = 0; index < 16; index += 1) target.elements[index] = source.elements[index];
  return target;
}

export function multiplyCharacterMatrices(
  left: CharacterMatrix4,
  right: CharacterMatrix4,
  target = createCharacterMatrix(),
): CharacterMatrix4 {
  return target.multiplyMatrices(left, right);
}
export type CharacterObject3D = Object3D;
export type CharacterSkinnedMesh = SkinnedMesh;
export function measureCharacterObjectHeight(object: CharacterObject3D): number {
  return measureSceneHeight(object);
}
export type CharacterThreeSkeleton = ThreeSkeleton;

export interface CanonicalBones {
  root: Bone;
  bones: Bone[];
  boneByName: Map<BoneName, Bone>;
  skeleton: ThreeSkeleton;
}

/**
 * The canonical rig as three.js bones, in the rig's own order.
 *
 * Every character is bound to a hierarchy built here, whatever surface it
 * wears. That is what lets one animation, one set of IK chains and one grip
 * solver drive any of them — and why equipment parented to `hand_r` stays in
 * the hand no matter which mesh is on screen.
 */
export function buildCanonicalBones(rig: Skeleton = canonicalSkeleton): CanonicalBones {
  const bones: Bone[] = [];
  const boneByName = new Map<BoneName, Bone>();

  for (const rigBone of rig.bones) {
    const bone = new Bone();
    bone.name = rigBone.name;
    bone.position.set(rigBone.offset.x, rigBone.offset.y, rigBone.offset.z);
    bone.quaternion.set(
      rigBone.restLocalQuaternion.x,
      rigBone.restLocalQuaternion.y,
      rigBone.restLocalQuaternion.z,
      rigBone.restLocalQuaternion.w,
    );
    bones.push(bone);
    boneByName.set(rigBone.name, bone);
    if (rigBone.parent) boneByName.get(rigBone.parent)!.add(bone);
  }

  const root = boneByName.get(rig.bones[0].name)!;
  root.updateMatrixWorld(true);

  return { root, bones, boneByName, skeleton: new ThreeSkeleton(bones) };
}
