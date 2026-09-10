import { Bone, Skeleton as ThreeSkeleton } from 'three';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';

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
    bone.position.copy(rigBone.offset);
    bone.quaternion.copy(rigBone.restLocalQuaternion);
    bones.push(bone);
    boneByName.set(rigBone.name, bone);
    if (rigBone.parent) boneByName.get(rigBone.parent)!.add(bone);
  }

  const root = boneByName.get(rig.bones[0].name)!;
  root.updateMatrixWorld(true);

  return { root, bones, boneByName, skeleton: new ThreeSkeleton(bones) };
}
