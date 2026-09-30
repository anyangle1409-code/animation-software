import { HgMat4, HgQuat } from '../core/linearMath';
import { HgBone, HgObject3D } from '../core/sceneGraph';
import {
  HgBufferAttribute,
  HgBufferGeometry,
  HgMaterial,
  HgSkeleton,
  HgSkinnedMesh,
  HgStandardMaterial,
  type HgStandardMaterialParameters,
} from '../core/sceneSkin';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { measureSceneHeight } from './sceneBounds';

export type CharacterBone = HgBone;
export type CharacterBufferAttribute = HgBufferAttribute;
export type CharacterBufferGeometry = HgBufferGeometry;

export type CharacterMaterial = HgMaterial;
export type CharacterStandardMaterial = HgStandardMaterial;
export type CharacterStandardMaterialParameters = HgStandardMaterialParameters;

export function createCharacterBufferGeometry(): CharacterBufferGeometry {
  return new HgBufferGeometry();
}

export function createCharacterUint16BufferAttribute(
  values: Uint16Array,
  itemSize: number,
): CharacterBufferAttribute {
  return new HgBufferAttribute(values, itemSize);
}

export function createCharacterSkinnedMeshObject(
  geometry: CharacterBufferGeometry,
  material: CharacterMaterial,
): CharacterSkinnedMesh {
  return new HgSkinnedMesh(geometry, material);
}

export function createCharacterStandardMaterialObject(
  parameters?: CharacterStandardMaterialParameters,
): CharacterStandardMaterial {
  return new HgStandardMaterial(parameters);
}

export function isCharacterStandardMaterial(
  material: unknown,
): material is CharacterStandardMaterial {
  return material instanceof HgStandardMaterial;
}

/**
 * Kept as a structural alias while imported assets/tests may still mention the
 * former interleaved attribute type. First-party GLB materialisation normalises
 * supported attributes into contiguous project-owned buffers.
 */
export type CharacterInterleavedBufferAttribute = HgBufferAttribute;

export function createCharacterBufferAttribute(
  values: Float32Array,
  itemSize: number,
): CharacterBufferAttribute {
  return new HgBufferAttribute(values, itemSize);
}

export type CharacterQuaternion = HgQuat;

export function createCharacterQuaternion(
  x = 0,
  y = 0,
  z = 0,
  w = 1,
): CharacterQuaternion {
  return new HgQuat(x, y, z, w);
}

export type CharacterMatrix4 = HgMat4;

export interface CharacterMatrixLike {
  readonly elements: ArrayLike<number>;
}

export function createCharacterMatrix(): CharacterMatrix4 {
  return new HgMat4();
}

export function copyCharacterMatrix(
  source: CharacterMatrixLike,
  target = createCharacterMatrix(),
): CharacterMatrix4 {
  return target.copy(source);
}

export function multiplyCharacterMatrices(
  left: CharacterMatrix4,
  right: CharacterMatrix4,
  target = createCharacterMatrix(),
): CharacterMatrix4 {
  return target.multiplyMatrices(left, right);
}

export type CharacterObject3D = HgObject3D;
export type CharacterSkinnedMesh = HgSkinnedMesh;

export function measureCharacterObjectHeight(object: CharacterObject3D): number {
  return measureSceneHeight(object);
}

export type CharacterThreeSkeleton = HgSkeleton;

export interface CanonicalBones {
  root: CharacterBone;
  bones: CharacterBone[];
  boneByName: Map<BoneName, CharacterBone>;
  skeleton: CharacterThreeSkeleton;
}

/**
 * Canonical Home Gym PT bone hierarchy in the project-owned scene runtime.
 *
 * Every character is bound to this shared hierarchy unless it preserves an
 * imported skeleton and is driven through retargeting.
 */
export function buildCanonicalBones(rig: Skeleton = canonicalSkeleton): CanonicalBones {
  const bones: CharacterBone[] = [];
  const boneByName = new Map<BoneName, CharacterBone>();

  for (const rigBone of rig.bones) {
    const bone = new HgBone();
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

  return { root, bones, boneByName, skeleton: new HgSkeleton(bones) };
}
