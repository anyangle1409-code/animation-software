import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import {
  buildHgSkeletonSceneModel,
  HG_SKELETON_COLOURS,
  resolveHgSkeletonAppearance,
} from './skeletonSceneModel';

describe('first-party skeleton scene model', () => {
  it('derives shaft/joint geometry and ghosted material values without renderer objects', () => {
    const model = buildHgSkeletonSceneModel(
      canonicalSkeleton,
      ['upperarm_l', 'forearm_l'],
      true,
    );
    const upper = model.get('upperarm_l')!;
    const definition = canonicalSkeleton.bone('upperarm_l');

    expect(upper.length).toBe(definition.length);
    expect(upper.shaft).not.toBeNull();
    expect(upper.shaft?.positionY).toBeCloseTo(definition.length / 2, 12);
    expect(upper.shaft?.radialSegments).toBe(6);
    expect(upper.shaft?.opacity).toBe(0.35);
    expect(upper.joint.opacity).toBe(0.5);
    expect(upper.joint.widthSegments).toBe(12);
    expect(upper.joint.heightSegments).toBe(10);
  });

  it('owns selected colours, emissive state and joint visibility', () => {
    expect(resolveHgSkeletonAppearance('upperarm_l', null, true)).toEqual({
      shaftColour: HG_SKELETON_COLOURS.bone,
      jointColour: HG_SKELETON_COLOURS.joint,
      jointEmissive: HG_SKELETON_COLOURS.emissiveOff,
      jointEmissiveIntensity: 0,
      jointVisible: true,
    });
    expect(resolveHgSkeletonAppearance('upperarm_l', 'upperarm_l', false)).toEqual({
      shaftColour: HG_SKELETON_COLOURS.selected,
      jointColour: HG_SKELETON_COLOURS.selected,
      jointEmissive: HG_SKELETON_COLOURS.selected,
      jointEmissiveIntensity: 0.45,
      jointVisible: false,
    });
  });
});
