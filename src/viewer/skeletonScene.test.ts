import { describe, expect, it, vi } from 'vitest';
import type { Object3D } from 'three';
import { canonicalSkeleton } from '../rig/skeleton';
import type { HgSceneRayEvent } from './scenePointerTypes';
import type { HgScenePointerHandlers } from './scenePointerRouter';
import {
  createSkeletonScene,
  registerSkeletonPointers,
  updateSkeletonAppearance,
} from './skeletonScene';

describe('first-party skeleton scene', () => {
  const names = ['upperarm_l', 'forearm_l'] as const;

  it('builds bone-local shaft and joint objects with frozen local transforms', () => {
    const resources = createSkeletonScene(canonicalSkeleton, [...names], false);
    expect(resources.bones.size).toBe(2);

    const upper = resources.bones.get('upperarm_l')!;
    expect(upper.group.matrixAutoUpdate).toBe(false);
    expect(upper.shaft).not.toBeNull();
    expect(upper.shaft!.position.y).toBeCloseTo(canonicalSkeleton.bone('upperarm_l').length / 2, 12);
    expect(upper.joint.name).toBe('hgpt-joint-upperarm_l');
    expect(upper.joint.visible).toBe(true);

    resources.dispose();
  });

  it('updates selected colours and joint visibility without rebuilding geometry', () => {
    const resources = createSkeletonScene(canonicalSkeleton, [...names], true);
    updateSkeletonAppearance(resources, 'forearm_l', false);

    const upper = resources.bones.get('upperarm_l')!;
    const forearm = resources.bones.get('forearm_l')!;
    expect(upper.shaft!.material.color.getHexString()).toBe('8fa3bf');
    expect(forearm.shaft!.material.color.getHexString()).toBe('ffb43a');
    expect(forearm.joint.material.emissive.getHexString()).toBe('ffb43a');
    expect(forearm.joint.material.emissiveIntensity).toBe(0.45);
    expect(upper.joint.visible).toBe(false);
    expect(forearm.joint.visible).toBe(false);
    expect(forearm.shaft!.material.opacity).toBe(0.35);
    expect(forearm.joint.material.opacity).toBe(0.5);

    resources.dispose();
  });

  it('registers only joints as project pointer targets', () => {
    const resources = createSkeletonScene(canonicalSkeleton, [...names], false);
    const handlers = new Map<Object3D, HgScenePointerHandlers>();
    const unregister = vi.fn();
    const pointers = {
      register(object: Object3D, callbacks: HgScenePointerHandlers) {
        handlers.set(object, callbacks);
        return unregister;
      },
    };
    const select = vi.fn();
    const remove = registerSkeletonPointers(resources, pointers, select);

    expect(handlers.size).toBe(2);
    expect(handlers.has(resources.bones.get('upperarm_l')!.joint)).toBe(true);
    expect(handlers.has(resources.bones.get('upperarm_l')!.shaft!)).toBe(false);

    let stopped = false;
    const event: HgSceneRayEvent = {
      pointerId: 2,
      ray: {
        origin: { x: 0, y: 0, z: 2 },
        direction: { x: 0, y: 0, z: -1 },
      },
      target: null,
      stopPropagation: () => {
        stopped = true;
      },
    };
    handlers.get(resources.bones.get('forearm_l')!.joint)?.pointerdown?.(event);
    expect(stopped).toBe(true);
    expect(select).toHaveBeenCalledWith('forearm_l');

    remove();
    expect(unregister).toHaveBeenCalledTimes(2);
    resources.dispose();
  });
});
