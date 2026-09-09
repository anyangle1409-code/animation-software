import {
  Bone,
  MeshStandardMaterial,
  Skeleton as ThreeSkeleton,
  SkinnedMesh,
} from 'three';
import type { BufferGeometry, Material } from 'three';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { buildBodyGeometry, BODY_MATERIAL } from './mesh';

export interface BuiltRig {
  root: Bone;
  bones: Bone[];
  boneByName: Map<BoneName, Bone>;
  mesh: SkinnedMesh;
  skeleton: ThreeSkeleton;
}

export const MANNEQUIN_NAME = 'HGPT_Mannequin';

/**
 * A different surface on the same bones — the anatomy view swaps both, and
 * nothing else does. Omitting them gives the character the exporter writes.
 */
export interface SkinnedRigOptions {
  geometry?: BufferGeometry;
  material?: Material;
}

/**
 * Build the character: a bone hierarchy matching the canonical skeleton, and
 * one skinned body bound to it.
 *
 * The same function backs the studio viewport and the GLB exporter, so the
 * figure on screen is the figure in the exported file — there is no second,
 * drifting copy of the character.
 */
export function buildSkinnedRig(
  rig: Skeleton = canonicalSkeleton,
  options: SkinnedRigOptions = {},
): BuiltRig {
  const bones: Bone[] = [];
  const boneByName = new Map<BoneName, Bone>();

  for (const rigBone of rig.bones) {
    const bone = new Bone();
    bone.name = rigBone.name;
    bone.position.copy(rigBone.offset);
    bone.quaternion.copy(rigBone.restLocalQuaternion);
    bones.push(bone);
    boneByName.set(rigBone.name, bone);
    if (rigBone.parent) boneByName.get(rigBone.parent)!.add(bone);
  }

  const root = boneByName.get(rig.bones[0].name)!;
  root.updateMatrixWorld(true);

  const geometry = options.geometry ?? buildBodyGeometry(rig).geometry;
  const material = options.material ?? new MeshStandardMaterial({ ...BODY_MATERIAL });
  const mesh = new SkinnedMesh(geometry, material);
  mesh.name = MANNEQUIN_NAME;
  mesh.castShadow = true;
  mesh.receiveShadow = true;

  const skeleton = new ThreeSkeleton(bones);
  mesh.add(root);
  mesh.bind(skeleton);

  return { root, bones, boneByName, mesh, skeleton };
}
