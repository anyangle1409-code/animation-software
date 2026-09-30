import { describe, expect, it, vi } from 'vitest';
import { HgGroup, HgPerspectiveCamera, HgScene } from '../core/sceneGraph';
import { boxPrimitiveData } from '../core/primitiveGeometry';
import { HgPrimitiveMaterial, HgPrimitiveMesh } from '../core/sceneMesh';
import { HgScenePointerRouter, type HgPointerSurface } from './scenePointerRouter';

class FakeSurface extends EventTarget implements HgPointerSurface {
  readonly captured = new Set<number>();

  getBoundingClientRect() {
    return { left: 10, top: 20, width: 200, height: 100 };
  }

  setPointerCapture(pointerId: number): void {
    this.captured.add(pointerId);
  }

  releasePointerCapture(pointerId: number): void {
    this.captured.delete(pointerId);
  }

  hasPointerCapture(pointerId: number): boolean {
    return this.captured.has(pointerId);
  }
}

function fixture() {
  const scene = new HgScene();
  const camera = new HgPerspectiveCamera(50, 2, 0.1, 100);
  camera.position.set(0, 0, 5);
  camera.lookAt(0, 0, 0);
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);

  const parent = new HgGroup();
  const mesh = new HgPrimitiveMesh(
    boxPrimitiveData([1, 1, 1]),
    new HgPrimitiveMaterial('#ffffff'),
  );
  parent.add(mesh);
  scene.add(parent);

  const surface = new FakeSurface();
  const miss = vi.fn();
  const router = new HgScenePointerRouter(camera, scene, surface, miss);

  const center = {
    pointerId: 7,
    clientX: 110,
    clientY: 70,
    target: surface,
  };

  return { scene, camera, parent, mesh, surface, miss, router, center };
}

describe('first-party scene pointer router', () => {
  it('delivers the nearest registered hit then bubbles through registered ancestors', () => {
    const { parent, mesh, router, center } = fixture();
    const calls: string[] = [];

    router.register(mesh, {
      pointerdown: (event) => {
        calls.push('mesh');
        expect(event.pointerId).toBe(7);
        expect(event.ray.direction.z).toBeLessThan(-0.9);
      },
    });
    router.register(parent, {
      pointerdown: () => calls.push('parent'),
    });

    expect(router.dispatch('pointerdown', center)).toBe(true);
    expect(calls).toEqual(['mesh', 'parent']);
  });

  it('reports whether the current ray hits a registered visible target', () => {
    const { mesh, router } = fixture();
    router.register(mesh, { pointerdown: () => undefined });

    expect(router.hitsRegisteredTarget(110, 70)).toBe(true);
    expect(router.hitsRegisteredTarget(500, 500)).toBe(false);
    mesh.visible = false;
    expect(router.hitsRegisteredTarget(110, 70)).toBe(false);
  });

  it('honours stopPropagation before registered ancestors', () => {
    const { parent, mesh, router, center } = fixture();
    const parentDown = vi.fn();

    router.register(mesh, {
      pointerdown: (event) => event.stopPropagation(),
    });
    router.register(parent, { pointerdown: parentDown });

    router.dispatch('pointerdown', center);
    expect(parentDown).not.toHaveBeenCalled();
  });

  it('keeps captured drag events on the original target after the ray leaves it', () => {
    const { mesh, surface, router, center } = fixture();
    const moveDirections: number[] = [];
    const ups = vi.fn();

    router.register(mesh, {
      pointerdown: (event) => {
        (event.target as FakeSurface).setPointerCapture(event.pointerId);
      },
      pointermove: (event) => moveDirections.push(event.ray.direction.x),
      pointerup: (event) => {
        ups();
        (event.target as FakeSurface).releasePointerCapture(event.pointerId);
      },
    });

    router.dispatch('pointerdown', center);
    expect(surface.hasPointerCapture(7)).toBe(true);

    const outside = { ...center, clientX: 500, clientY: 500 };
    expect(router.dispatch('pointermove', outside)).toBe(true);
    expect(router.dispatch('pointerup', outside)).toBe(true);
    expect(moveDirections).toHaveLength(1);
    expect(Math.abs(moveDirections[0])).toBeGreaterThan(0.1);
    expect(ups).toHaveBeenCalledTimes(1);

    expect(router.dispatch('pointermove', outside)).toBe(false);
  });

  it('ignores invisible hits and reports pointer-down misses', () => {
    const { mesh, router, center, miss } = fixture();
    const down = vi.fn();
    mesh.visible = false;
    router.register(mesh, { pointerdown: down });

    expect(router.dispatch('pointerdown', center)).toBe(false);
    expect(down).not.toHaveBeenCalled();
    expect(miss).toHaveBeenCalledTimes(1);
  });

  it('unregisters target descendants from active capture', () => {
    const { parent, mesh, surface, router, center } = fixture();
    const move = vi.fn();
    const removeParent = router.register(parent, { pointermove: move });
    router.register(mesh, {
      pointerdown: (event) => (event.target as FakeSurface).setPointerCapture(event.pointerId),
    });

    router.dispatch('pointerdown', center);
    removeParent();

    const outside = { ...center, clientX: 500, clientY: 500 };
    expect(router.dispatch('pointermove', outside)).toBe(false);
    expect(move).not.toHaveBeenCalled();
    expect(surface.hasPointerCapture(7)).toBe(false);
  });
  it('accepts first-party scene/camera contracts without renderer-specific types', () => {
    const camera = new HgPerspectiveCamera(38, 1, 0.05, 100);
    camera.position.set(0, 0, 3);
    camera.updateMatrixWorld(true);
    const scene = new HgScene();
    scene.updateMatrixWorld(true);
    const surface = new EventTarget() as EventTarget & {
      getBoundingClientRect(): Pick<DOMRect, 'left' | 'top' | 'width' | 'height'>;
    };
    surface.getBoundingClientRect = () => ({
      left: 0, top: 0, width: 100, height: 100,
    }) as DOMRect;

    const router = new HgScenePointerRouter(camera, scene, surface);
    expect(router.hitsRegisteredTarget(50, 50)).toBe(false);
    router.dispose();
  });

});
