import { describe, expect, it, vi } from 'vitest';
import type { Object3D } from 'three';
import type { HgSceneRayEvent } from './scenePointerTypes';
import type { HgScenePointerHandlers } from './scenePointerRouter';
import {
  createTransformGizmoScene,
  registerTransformGizmoPointers,
  updateTransformGizmoActiveAxis,
} from './transformGizmoScene';

const event = (): HgSceneRayEvent => ({
  pointerId: 4,
  ray: {
    origin: { x: 0, y: 0, z: 3 },
    direction: { x: 0, y: 0, z: -1 },
  },
  target: null,
  stopPropagation: () => undefined,
});

describe('first-party transform gizmo scene', () => {
  it('builds three enlarged translation targets with project-owned visuals', () => {
    const resources = createTransformGizmoScene('translate');

    expect(resources.targets.size).toBe(3);
    expect(resources.group.children).toHaveLength(3);
    expect(resources.targets.get('x')?.children).toHaveLength(3);
    expect(resources.materials.get('x')?.depthTest).toBe(false);

    resources.dispose();
  });

  it('builds rotation rings and updates the active-axis colour without rebuilding', () => {
    const resources = createTransformGizmoScene('rotate');
    expect(resources.group.children).toHaveLength(3);

    updateTransformGizmoActiveAxis(resources, 'z');
    expect(resources.materials.get('x')?.color.getHexString()).toBe('f05a5a');
    expect(resources.materials.get('z')?.color.getHexString()).toBe('ffd35a');

    resources.dispose();
  });

  it('routes axis-down separately from captured root move/up/cancel handlers', () => {
    const resources = createTransformGizmoScene('translate');
    const registered = new Map<Object3D, HgScenePointerHandlers>();
    const unregister = vi.fn();
    const pointers = {
      register(object: Object3D, callbacks: HgScenePointerHandlers) {
        registered.set(object, callbacks);
        return unregister;
      },
    };
    const callbacks = {
      axisDown: vi.fn(),
      move: vi.fn(),
      up: vi.fn(),
      cancel: vi.fn(),
    };
    const remove = registerTransformGizmoPointers(resources, pointers, callbacks);

    registered.get(resources.targets.get('y')!)?.pointerdown?.(event());
    registered.get(resources.group)?.pointermove?.(event());
    registered.get(resources.group)?.pointerup?.(event());
    registered.get(resources.group)?.pointercancel?.(event());

    expect(callbacks.axisDown).toHaveBeenCalledWith('y', expect.anything());
    expect(callbacks.move).toHaveBeenCalledTimes(1);
    expect(callbacks.up).toHaveBeenCalledTimes(1);
    expect(callbacks.cancel).toHaveBeenCalledTimes(1);

    remove();
    expect(unregister).toHaveBeenCalledTimes(4);
    resources.dispose();
  });
});
