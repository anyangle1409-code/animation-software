import { describe, expect, it, vi } from 'vitest';
import { Matrix4, type Object3D } from 'three';
import type { EquipmentInstance } from '../equipment/types';
import type { HgSceneRayEvent } from './scenePointerTypes';
import type { HgScenePointerHandlers } from './scenePointerRouter';
import {
  applyEquipmentDisplayTransforms,
  createEquipmentScene,
  registerEquipmentPointers,
} from './equipmentScene';

const dumbbell: EquipmentInstance = {
  id: 'db_l',
  kind: 'dumbbell',
  position: { x: 0, y: 0, z: 0 },
  rotation: { x: 0, y: 0, z: 0 },
  attachment: { mode: 'static' },
  visible: true,
};

describe('first-party equipment scene', () => {
  it('builds the shared equipment geometry data into owned Three meshes', () => {
    const resources = createEquipmentScene([dumbbell]);
    const group = resources.instances.get('db_l')!;

    expect(group.matrixAutoUpdate).toBe(false);
    expect(group.children).toHaveLength(3);
    expect(group.children.every((child) => child.name === '' || child.name.startsWith('hgpt-'))).toBe(true);
    expect(group.children.every((child) => 'castShadow' in child && child.castShadow)).toBe(true);

    resources.dispose();
  });

  it('applies the already-verified display matrix policy without recomputing it', () => {
    const resources = createEquipmentScene([dumbbell]);
    const matrix = new Matrix4().makeTranslation(1, 2, 3);

    applyEquipmentDisplayTransforms(
      resources,
      new Map([['db_l', { visible: true, matrix }]]),
    );
    const group = resources.instances.get('db_l')!;
    expect(group.visible).toBe(true);
    expect(group.matrix.elements).toEqual(matrix.elements);

    applyEquipmentDisplayTransforms(
      resources,
      new Map([['db_l', { visible: false, matrix: null }]]),
    );
    expect(group.visible).toBe(false);

    resources.dispose();
  });

  it('registers one project pointer target per equipment instance', () => {
    const resources = createEquipmentScene([dumbbell]);
    const handlers = new Map<Object3D, HgScenePointerHandlers>();
    const unregister = vi.fn();
    const pointers = {
      register(object: Object3D, callbacks: HgScenePointerHandlers) {
        handlers.set(object, callbacks);
        return unregister;
      },
    };
    const select = vi.fn();
    const remove = registerEquipmentPointers(resources, pointers, select);
    const group = resources.instances.get('db_l')!;

    expect(handlers.has(group)).toBe(true);
    let stopped = false;
    const event: HgSceneRayEvent = {
      pointerId: 5,
      ray: {
        origin: { x: 0, y: 0, z: 2 },
        direction: { x: 0, y: 0, z: -1 },
      },
      target: null,
      stopPropagation: () => {
        stopped = true;
      },
    };
    handlers.get(group)?.pointerdown?.(event);
    expect(stopped).toBe(true);
    expect(select).toHaveBeenCalledWith('db_l');

    remove();
    expect(unregister).toHaveBeenCalledTimes(1);
    resources.dispose();
  });
});
