import { describe, expect, it, vi } from 'vitest';
import { HgPrimitiveMesh } from '../core/sceneMesh';
import {
  createHgTransformGizmoScene,
  registerHgTransformGizmoPointers,
  updateHgTransformGizmoActiveAxis,
} from './firstPartyTransformGizmoScene';

describe('first-party transform gizmo scene', () => {
  it('builds translation axes with visible shaft/tip and invisible hit geometry', () => {
    const resources = createHgTransformGizmoScene('translate');
    expect(resources.targets.size).toBe(3);
    for (const target of resources.targets.values()) {
      expect(target.children).toHaveLength(3);
      const hit = target.children[2] as HgPrimitiveMesh;
      expect(hit.material.colour[3]).toBe(0);
      expect(hit.geometry.indices.length).toBeGreaterThan(0);
    }
    updateHgTransformGizmoActiveAxis(resources, 'x');
    expect(resources.materials.get('x')?.colour[0]).toBeGreaterThan(
      resources.materials.get('y')?.colour[0] ?? 0,
    );
  });

  it('builds rotation rings and registers project pointer targets', () => {
    const resources = createHgTransformGizmoScene('rotate');
    expect(resources.group.children).toHaveLength(3);
    const register = vi.fn(() => vi.fn());
    const remove = registerHgTransformGizmoPointers(
      resources,
      { register },
      {
        axisDown: vi.fn(),
        move: vi.fn(),
        up: vi.fn(),
        cancel: vi.fn(),
      },
    );
    expect(register).toHaveBeenCalledTimes(4);
    remove();
    resources.dispose();
    expect(resources.group.children).toHaveLength(0);
  });
});
