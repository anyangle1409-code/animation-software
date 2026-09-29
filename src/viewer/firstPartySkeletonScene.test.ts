import { describe, expect, it } from 'vitest';
import { hgRgbaFromHex } from '../core/sceneMesh';
import { canonicalSkeleton } from '../rig/skeleton';
import {
  createHgSkeletonScene,
  updateHgSkeletonAppearance,
} from './firstPartySkeletonScene';
import {
  HG_SKELETON_COLOURS,
  buildHgSkeletonSceneModel,
} from './skeletonSceneModel';

describe('first-party skeleton visual scene', () => {
  const names = ['upperarm_l', 'forearm_l'] as const;

  it('builds the renderer-neutral skeleton model into project-owned primitives', () => {
    const resources = createHgSkeletonScene(
      canonicalSkeleton,
      [...names],
      false,
    );
    const model = buildHgSkeletonSceneModel(
      canonicalSkeleton,
      [...names],
      false,
    );

    expect(resources.bones.size).toBe(2);
    for (const name of names) {
      const visual = model.get(name)!;
      const built = resources.bones.get(name)!;
      expect(built.group.matrixAutoUpdate).toBe(false);
      expect(built.joint.name).toBe(`hgpt-joint-${name}`);
      expect(built.joint.userData.hgptBone).toBe(name);
      expect(built.joint.geometry.positions.length).toBeGreaterThan(0);
      expect(built.joint.material.colour).toEqual(
        hgRgbaFromHex(HG_SKELETON_COLOURS.joint),
      );
      if (visual.shaft) {
        expect(built.shaft).not.toBeNull();
        expect(built.shaft!.position.y).toBeCloseTo(
          visual.shaft.positionY,
          12,
        );
        expect(built.shaft!.material.roughness).toBe(
          visual.shaft.roughness,
        );
        expect(built.shaft!.material.metalness).toBe(
          visual.shaft.metalness,
        );
      }
    }

    resources.dispose();
  });

  it('preserves selected colours, emissive metadata, opacity and joint visibility', () => {
    const resources = createHgSkeletonScene(
      canonicalSkeleton,
      [...names],
      true,
    );
    updateHgSkeletonAppearance(resources, 'forearm_l', false);

    const upper = resources.bones.get('upperarm_l')!;
    const forearm = resources.bones.get('forearm_l')!;
    expect(upper.shaft!.material.colour).toEqual(
      hgRgbaFromHex(HG_SKELETON_COLOURS.bone, 0.35),
    );
    expect(forearm.shaft!.material.colour).toEqual(
      hgRgbaFromHex(HG_SKELETON_COLOURS.selected, 0.35),
    );
    expect(forearm.joint.material.emissive).toEqual(
      hgRgbaFromHex(HG_SKELETON_COLOURS.selected),
    );
    expect(forearm.joint.material.emissiveIntensity).toBe(0.45);
    expect(upper.joint.visible).toBe(false);
    expect(forearm.joint.visible).toBe(false);
    expect(forearm.joint.material.colour[3]).toBe(0.5);

    resources.dispose();
  });

  it('accepts exact canonical frame matrices without renderer conversion', () => {
    const resources = createHgSkeletonScene(
      canonicalSkeleton,
      ['upperarm_l'],
      false,
    );
    const bone = resources.bones.get('upperarm_l')!;
    const source = canonicalSkeleton
      .evaluation()
      .matrix('upperarm_l')
      .elements;
    bone.group.matrix.fromArray(source);
    bone.group.matrixWorldNeedsUpdate = true;
    resources.group.updateMatrixWorld(true);
    expect(bone.group.matrix.toArray()).toEqual(Array.from(source));
    resources.dispose();
  });
});
