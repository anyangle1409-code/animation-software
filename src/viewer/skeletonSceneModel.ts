import type { BoneName } from '../rig/boneNames';
import type { Skeleton } from '../rig/skeleton';

export const HG_SKELETON_COLOURS = {
  bone: '#8fa3bf',
  selected: '#ffb43a',
  joint: '#cfe0ff',
  emissiveOff: '#000000',
} as const;

export interface HgSkeletonBoneVisual {
  readonly name: BoneName;
  readonly length: number;
  readonly shaft: {
    readonly radiusTop: number;
    readonly radiusBottom: number;
    readonly length: number;
    readonly radialSegments: number;
    readonly positionY: number;
    readonly roughness: number;
    readonly metalness: number;
    readonly transparent: boolean;
    readonly opacity: number;
  } | null;
  readonly joint: {
    readonly radius: number;
    readonly widthSegments: number;
    readonly heightSegments: number;
    readonly roughness: number;
    readonly transparent: boolean;
    readonly opacity: number;
  };
}

export interface HgSkeletonAppearance {
  readonly shaftColour: string;
  readonly jointColour: string;
  readonly jointEmissive: string;
  readonly jointEmissiveIntensity: number;
  readonly jointVisible: boolean;
}

/** Renderer-neutral geometry/material description for the skeleton overlay. */
export function buildHgSkeletonSceneModel(
  rig: Skeleton,
  names: readonly BoneName[],
  ghosted: boolean,
): Map<BoneName, HgSkeletonBoneVisual> {
  const out = new Map<BoneName, HgSkeletonBoneVisual>();

  for (const name of names) {
    const bone = rig.bone(name);
    const shaftRadius = Math.max(0.008, Math.min(0.022, bone.definition.radius * 0.28));
    const jointRadius = Math.max(0.012, Math.min(0.032, bone.definition.radius * 0.4));

    out.set(name, {
      name,
      length: bone.length,
      shaft: bone.length > 0.001
        ? {
            radiusTop: shaftRadius * 0.6,
            radiusBottom: shaftRadius,
            length: bone.length,
            radialSegments: 6,
            positionY: bone.length / 2,
            roughness: 0.55,
            metalness: 0.1,
            transparent: ghosted,
            opacity: ghosted ? 0.35 : 1,
          }
        : null,
      joint: {
        radius: jointRadius,
        widthSegments: 12,
        heightSegments: 10,
        roughness: 0.4,
        transparent: ghosted,
        opacity: ghosted ? 0.5 : 1,
      },
    });
  }

  return out;
}

/** Renderer-neutral selected/unselected appearance for one skeleton bone. */
export function resolveHgSkeletonAppearance(
  name: BoneName,
  selected: BoneName | null,
  showJoints: boolean,
): HgSkeletonAppearance {
  const active = name === selected;
  return {
    shaftColour: active ? HG_SKELETON_COLOURS.selected : HG_SKELETON_COLOURS.bone,
    jointColour: active ? HG_SKELETON_COLOURS.selected : HG_SKELETON_COLOURS.joint,
    jointEmissive: active ? HG_SKELETON_COLOURS.selected : HG_SKELETON_COLOURS.emissiveOff,
    jointEmissiveIntensity: active ? 0.45 : 0,
    jointVisible: showJoints,
  };
}
