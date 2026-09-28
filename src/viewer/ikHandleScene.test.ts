import { describe, expect, it, vi } from 'vitest';
import type { Object3D } from 'three';
import type { HgSceneRayEvent } from './scenePointerTypes';
import type { HgScenePointerHandlers } from './scenePointerRouter';
import {
  createIKHandleScene,
  registerIKHandlePointers,
  updateIKHandleSelection,
} from './ikHandleScene';

describe('first-party IK handle scene', () => {
  it('builds target/pole meshes for all four chains with the current visual defaults', () => {
    const resources = createIKHandleScene();

    expect(resources.handles.size).toBe(8);
    expect(resources.handles.get('arm_l:target')?.visible).toBe(false);
    expect(resources.handles.get('arm_l:target')?.name).toBe('hgpt-ik-arm_l-target');
    expect(resources.handles.get('leg_r:pole')?.name).toBe('hgpt-ik-leg_r-pole');

    const targetMaterial = resources.handles.get('arm_l:target')!.material;
    const poleMaterial = resources.handles.get('arm_l:pole')!.material;
    expect(Array.isArray(targetMaterial)).toBe(false);
    expect(Array.isArray(poleMaterial)).toBe(false);
    if (!Array.isArray(targetMaterial) && !Array.isArray(poleMaterial)) {
      expect(targetMaterial.color.getHexString()).toBe('4fd6a0');
      expect(poleMaterial.color.getHexString()).toBe('6aa9ff');
      expect(targetMaterial.opacity).toBe(0.9);
      expect(targetMaterial.depthTest).toBe(false);
    }

    resources.dispose();
  });

  it('updates only the selected handle highlight', () => {
    const resources = createIKHandleScene();
    updateIKHandleSelection(resources, { chain: 'arm_l', kind: 'target' });

    const selected = resources.handles.get('arm_l:target')!.material;
    const neighbour = resources.handles.get('arm_l:pole')!.material;
    if (!Array.isArray(selected) && !Array.isArray(neighbour)) {
      expect(selected.color.getHexString()).toBe('ffb43a');
      expect(selected.emissive.getHexString()).toBe('ffb43a');
      expect(selected.emissiveIntensity).toBe(0.5);
      expect(neighbour.color.getHexString()).toBe('6aa9ff');
      expect(neighbour.emissiveIntensity).toBe(0);
    }

    resources.dispose();
  });

  it('registers project-pointer selection handlers and unregisters them together', () => {
    const resources = createIKHandleScene();
    const handlers = new Map<Object3D, HgScenePointerHandlers>();
    const unregister = vi.fn();
    const pointers = {
      register(object: Object3D, callbacks: HgScenePointerHandlers) {
        handlers.set(object, callbacks);
        return unregister;
      },
    };
    const select = vi.fn();
    const remove = registerIKHandlePointers(resources, pointers, select);
    expect(handlers.size).toBe(8);

    let stopped = false;
    const event: HgSceneRayEvent = {
      pointerId: 3,
      ray: {
        origin: { x: 0, y: 0, z: 2 },
        direction: { x: 0, y: 0, z: -1 },
      },
      target: null,
      stopPropagation: () => {
        stopped = true;
      },
    };
    const target = resources.handles.get('leg_r:pole')!;
    handlers.get(target)?.pointerdown?.(event);

    expect(stopped).toBe(true);
    expect(select).toHaveBeenCalledWith({ chain: 'leg_r', kind: 'pole' });

    remove();
    expect(unregister).toHaveBeenCalledTimes(8);
    resources.dispose();
  });
});
