import {
  CylinderGeometry,
  Group,
  Mesh,
  MeshStandardMaterial,
  SphereGeometry,
} from 'three';
import type { BoneName } from '../rig/boneNames';
import type { Skeleton } from '../rig/skeleton';
import type { HgScenePointerRouter } from './scenePointerRouter';

const BONE_COLOUR = '#8fa3bf';
const SELECTED_COLOUR = '#ffb43a';
const JOINT_COLOUR = '#cfe0ff';

export interface SkeletonBoneScene {
  group: Group;
  shaft: Mesh<CylinderGeometry, MeshStandardMaterial> | null;
  joint: Mesh<SphereGeometry, MeshStandardMaterial>;
}

export interface SkeletonSceneResources {
  group: Group;
  bones: ReadonlyMap<BoneName, SkeletonBoneScene>;
  dispose(): void;
}

export function createSkeletonScene(
  rig: Skeleton,
  names: BoneName[],
  ghosted: boolean,
): SkeletonSceneResources {
  const root = new Group();
  root.name = 'hgpt-skeleton-view';
  const bones = new Map<BoneName, SkeletonBoneScene>();

  for (const name of names) {
    const bone = rig.bone(name);
    const shaftRadius = Math.max(0.008, Math.min(0.022, bone.definition.radius * 0.28));
    const jointRadius = Math.max(0.012, Math.min(0.032, bone.definition.radius * 0.4));

    const boneGroup = new Group();
    boneGroup.name = `hgpt-bone-${name}`;
    boneGroup.matrixAutoUpdate = false;

    let shaft: Mesh<CylinderGeometry, MeshStandardMaterial> | null = null;
    if (bone.length > 0.001) {
      shaft = new Mesh(
        new CylinderGeometry(shaftRadius * 0.6, shaftRadius, bone.length, 6),
        new MeshStandardMaterial({
          color: BONE_COLOUR,
          transparent: ghosted,
          opacity: ghosted ? 0.35 : 1,
          roughness: 0.55,
          metalness: 0.1,
        }),
      );
      shaft.name = `hgpt-bone-shaft-${name}`;
      shaft.position.y = bone.length / 2;
      boneGroup.add(shaft);
    }

    const joint = new Mesh(
      new SphereGeometry(jointRadius, 12, 10),
      new MeshStandardMaterial({
        color: JOINT_COLOUR,
        emissive: '#000000',
        emissiveIntensity: 0,
        transparent: ghosted,
        opacity: ghosted ? 0.5 : 1,
        roughness: 0.4,
      }),
    );
    joint.name = `hgpt-joint-${name}`;
    boneGroup.add(joint);

    root.add(boneGroup);
    bones.set(name, { group: boneGroup, shaft, joint });
  }

  let disposed = false;
  return {
    group: root,
    bones,
    dispose() {
      if (disposed) return;
      disposed = true;
      for (const objects of bones.values()) {
        if (objects.shaft) {
          objects.shaft.geometry.dispose();
          objects.shaft.material.dispose();
        }
        objects.joint.geometry.dispose();
        objects.joint.material.dispose();
      }
      root.clear();
    },
  };
}

export function updateSkeletonAppearance(
  resources: SkeletonSceneResources,
  selected: BoneName | null,
  showJoints: boolean,
): void {
  for (const [name, objects] of resources.bones) {
    const active = name === selected;
    if (objects.shaft) {
      objects.shaft.material.color.set(active ? SELECTED_COLOUR : BONE_COLOUR);
    }
    objects.joint.visible = showJoints;
    objects.joint.material.color.set(active ? SELECTED_COLOUR : JOINT_COLOUR);
    objects.joint.material.emissive.set(active ? SELECTED_COLOUR : '#000000');
    objects.joint.material.emissiveIntensity = active ? 0.45 : 0;
  }
}

export function registerSkeletonPointers(
  resources: SkeletonSceneResources,
  pointers: Pick<HgScenePointerRouter, 'register'>,
  select: (bone: BoneName) => void,
): () => void {
  const remove: Array<() => void> = [];
  for (const [name, objects] of resources.bones) {
    remove.push(
      pointers.register(objects.joint, {
        pointerdown: (event) => {
          event.stopPropagation();
          select(name);
        },
      }),
    );
  }
  return () => {
    for (const unregister of remove) unregister();
  };
}
