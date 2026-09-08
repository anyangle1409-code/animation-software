import {
  BoxGeometry,
  Bone,
  BufferGeometry,
  CapsuleGeometry,
  CylinderGeometry,
  Euler,
  Float32BufferAttribute,
  Matrix4,
  Mesh,
  MeshStandardMaterial,
  Object3D,
  Quaternion,
  Skeleton as ThreeSkeleton,
  SkinnedMesh,
  SphereGeometry,
  TorusGeometry,
  Vector3,
} from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { EQUIPMENT_PARTS, MATERIALS } from '../equipment/geometry';
import type { Part } from '../equipment/geometry';
import type { EquipmentKind } from '../equipment/types';

export interface BuiltRig {
  root: Bone;
  bones: Bone[];
  boneByName: Map<BoneName, Bone>;
  mesh: SkinnedMesh;
  skeleton: ThreeSkeleton;
}

/**
 * Build a real skinned rig for export: a bone hierarchy matching the canonical
 * skeleton, and one mesh bound to it.
 *
 * Each body segment is weighted entirely to its own bone. That is exactly right
 * for a mannequin — the segments are rigid — and it means the exported GLB
 * animates in any engine that can play skinned glTF, with no custom code.
 */
export function buildSkinnedRig(rig: Skeleton = canonicalSkeleton): BuiltRig {
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

  const pieces: BufferGeometry[] = [];
  rig.bones.forEach((rigBone, index) => {
    if (rigBone.length < 0.004 || rigBone.name === 'root') return;
    const radius = rigBone.definition.radius;
    const geometry = new CapsuleGeometry(
      radius,
      Math.max(0.001, rigBone.length - radius * 0.6),
      3,
      8,
    );
    geometry.translate(0, rigBone.length / 2, 0);
    // Place the segment in the bind pose, so the bind matrix stays identity.
    geometry.applyMatrix4(boneByName.get(rigBone.name)!.matrixWorld);

    const count = geometry.attributes.position.count;
    const skinIndices = new Uint16Array(count * 4);
    const skinWeights = new Float32Array(count * 4);
    for (let vertex = 0; vertex < count; vertex += 1) {
      skinIndices[vertex * 4] = index;
      skinWeights[vertex * 4] = 1;
    }
    geometry.setAttribute('skinIndex', new Float32BufferAttribute(skinIndices, 4));
    geometry.setAttribute('skinWeight', new Float32BufferAttribute(skinWeights, 4));
    pieces.push(geometry);
  });

  const merged = mergeGeometries(pieces, false);
  if (!merged) throw new Error('Failed to merge the mannequin geometry');

  const mesh = new SkinnedMesh(
    merged,
    new MeshStandardMaterial({ color: '#c9d3e0', roughness: 0.72, metalness: 0.04 }),
  );
  mesh.name = 'HGPT_Mannequin';
  const skeleton = new ThreeSkeleton(bones);
  mesh.add(root);
  mesh.bind(skeleton);

  return { root, bones, boneByName, mesh, skeleton };
}

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
