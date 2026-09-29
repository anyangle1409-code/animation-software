import {
  CylinderGeometry,
  Group,
  Mesh,
  MeshStandardMaterial,
  SphereGeometry,
} from './threeSceneBoundary';
import type { BoneName } from '../rig/boneNames';
import type { Skeleton } from '../rig/skeleton';
import type { HgScenePointerRouter } from './scenePointerRouter';
import {
  buildHgSkeletonSceneModel,
  HG_SKELETON_COLOURS,
  resolveHgSkeletonAppearance,
} from './skeletonSceneModel';

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

  const model = buildHgSkeletonSceneModel(rig, names, ghosted);
  for (const [name, visual] of model) {
    const boneGroup = new Group();
    boneGroup.name = `hgpt-bone-${name}`;
    boneGroup.matrixAutoUpdate = false;

    let shaft: Mesh<CylinderGeometry, MeshStandardMaterial> | null = null;
    if (visual.shaft) {
      shaft = new Mesh(
        new CylinderGeometry(
          visual.shaft.radiusTop,
          visual.shaft.radiusBottom,
          visual.shaft.length,
          visual.shaft.radialSegments,
        ),
        new MeshStandardMaterial({
          color: HG_SKELETON_COLOURS.bone,
          transparent: visual.shaft.transparent,
          opacity: visual.shaft.opacity,
          roughness: visual.shaft.roughness,
          metalness: visual.shaft.metalness,
        }),
      );
      shaft.name = `hgpt-bone-shaft-${name}`;
      shaft.position.y = visual.shaft.positionY;
      boneGroup.add(shaft);
    }

    const joint = new Mesh(
      new SphereGeometry(
        visual.joint.radius,
        visual.joint.widthSegments,
        visual.joint.heightSegments,
      ),
      new MeshStandardMaterial({
        color: HG_SKELETON_COLOURS.joint,
        emissive: HG_SKELETON_COLOURS.emissiveOff,
        emissiveIntensity: 0,
        transparent: visual.joint.transparent,
        opacity: visual.joint.opacity,
        roughness: visual.joint.roughness,
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
    const appearance = resolveHgSkeletonAppearance(name, selected, showJoints);
    if (objects.shaft) objects.shaft.material.color.set(appearance.shaftColour);
    objects.joint.visible = appearance.jointVisible;
    objects.joint.material.color.set(appearance.jointColour);
    objects.joint.material.emissive.set(appearance.jointEmissive);
    objects.joint.material.emissiveIntensity = appearance.jointEmissiveIntensity;
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
