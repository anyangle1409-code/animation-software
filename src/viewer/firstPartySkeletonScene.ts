import type { BoneName } from '../rig/boneNames';
import type { HgScenePointerRouter } from './scenePointerRouter';
import type { Skeleton } from '../rig/skeleton';
import {
  cylinderPrimitiveData,
  spherePrimitiveData,
} from '../core/primitiveGeometry';
import { HgGroup } from '../core/sceneGraph';
import {
  HgPrimitiveMaterial,
  HgPrimitiveMesh,
} from '../core/sceneMesh';
import {
  buildHgSkeletonSceneModel,
  HG_SKELETON_COLOURS,
  resolveHgSkeletonAppearance,
} from './skeletonSceneModel';

export interface HgSkeletonBoneScene {
  readonly group: HgGroup;
  readonly shaft: HgPrimitiveMesh | null;
  readonly joint: HgPrimitiveMesh;
}

export interface HgSkeletonSceneResources {
  readonly group: HgGroup;
  readonly bones: ReadonlyMap<BoneName, HgSkeletonBoneScene>;
  dispose(): void;
}

/** Project-owned skeleton visual scene, parallel to the retained pointer adapter. */
export function createHgSkeletonScene(
  rig: Skeleton,
  names: readonly BoneName[],
  ghosted: boolean,
): HgSkeletonSceneResources {
  const root = new HgGroup();
  root.name = 'hgpt-skeleton-view';
  const bones = new Map<BoneName, HgSkeletonBoneScene>();

  const model = buildHgSkeletonSceneModel(rig, names, ghosted);
  for (const [name, visual] of model) {
    const group = new HgGroup();
    group.name = `hgpt-bone-${name}`;
    group.matrixAutoUpdate = false;

    let shaft: HgPrimitiveMesh | null = null;
    if (visual.shaft) {
      shaft = new HgPrimitiveMesh(
        cylinderPrimitiveData(
          visual.shaft.radiusBottom,
          visual.shaft.radiusTop,
          visual.shaft.length,
          visual.shaft.radialSegments,
        ),
        new HgPrimitiveMaterial(
          HG_SKELETON_COLOURS.bone,
          'lit',
          {
            roughness: visual.shaft.roughness,
            metalness: visual.shaft.metalness,
          },
        ).setOpacity(visual.shaft.opacity),
      );
      shaft.name = `hgpt-bone-shaft-${name}`;
      shaft.position.y = visual.shaft.positionY;
      group.add(shaft);
    }

    const joint = new HgPrimitiveMesh(
      spherePrimitiveData(
        visual.joint.radius,
        visual.joint.widthSegments,
        visual.joint.heightSegments,
      ),
      new HgPrimitiveMaterial(
        HG_SKELETON_COLOURS.joint,
        'lit',
        {
          emissive: HG_SKELETON_COLOURS.emissiveOff,
          emissiveIntensity: 0,
          roughness: visual.joint.roughness,
        },
      ).setOpacity(visual.joint.opacity),
    );
    joint.name = `hgpt-joint-${name}`;
    joint.userData.hgptBone = name;
    group.add(joint);

    root.add(group);
    bones.set(name, { group, shaft, joint });
  }

  let disposed = false;
  return {
    group: root,
    bones,
    dispose() {
      if (disposed) return;
      disposed = true;
      for (const bone of bones.values()) bone.group.clear();
      bones.clear();
      root.clear();
    },
  };
}

export function updateHgSkeletonAppearance(
  resources: HgSkeletonSceneResources,
  selected: BoneName | null,
  showJoints: boolean,
): void {
  for (const [name, bone] of resources.bones) {
    const appearance = resolveHgSkeletonAppearance(name, selected, showJoints);
    bone.shaft?.material.setColour(appearance.shaftColour);
    bone.joint.material
      .setColour(appearance.jointColour)
      .setEmissive(
        appearance.jointEmissive,
        appearance.jointEmissiveIntensity,
      );
    bone.joint.visible = appearance.jointVisible;
  }
}


export function registerHgSkeletonPointers(
  resources: HgSkeletonSceneResources,
  pointers: Pick<HgScenePointerRouter, 'register'>,
  select: (bone: BoneName) => void,
): () => void {
  const remove: Array<() => void> = [];
  for (const [name, bone] of resources.bones) {
    remove.push(
      pointers.register(bone.joint, {
        pointerdown(event) {
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
