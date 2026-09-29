import { describe, expect, it, vi } from 'vitest';
import { HgObject3D, HgPerspectiveCamera, HgScene } from '../core/sceneGraph';
import { createSceneState } from './sceneStateCore';
import type { HgSceneRayEvent } from './scenePointerTypes';
import type { HgScenePointerHandlers } from './scenePointerRouter';
import { createFirstPartyTransformGizmoRuntime } from './firstPartyTransformGizmoRuntime';

const event = (
  pointerId: number,
  origin: { x: number; y: number; z: number },
  target: EventTarget | null,
): HgSceneRayEvent => ({
  pointerId,
  ray: {
    origin,
    direction: { x: 0, y: -1, z: 0 },
  },
  target,
  stopPropagation: vi.fn(),
});

describe('first-party transform gizmo runtime', () => {
  it('mounts, scales, drags and disposes using only Home Gym PT scene nodes', () => {
    const sceneState = createSceneState();
    const root = new HgScene();
    const camera = new HgPerspectiveCamera();
    camera.position.set(0, 0, 10);

    const object = new HgObject3D();
    object.position.set(4, 5, 6);
    root.add(object);

    const handlers = new Map<HgObject3D, HgScenePointerHandlers>();
    const pointers = {
      register(target: HgObject3D, callbacks: HgScenePointerHandlers) {
        handlers.set(target, callbacks);
        return () => handlers.delete(target);
      },
    };
    const capture = {
      setPointerCapture: vi.fn(),
      releasePointerCapture: vi.fn(),
    } as unknown as EventTarget;
    const onDragStart = vi.fn();
    const onDragEnd = vi.fn();
    const onObjectChange = vi.fn();

    const runtime = createFirstPartyTransformGizmoRuntime({
      sceneState,
      root,
      pointers,
      camera,
      object,
      mode: 'translate',
      onDragStart,
      onDragEnd,
      onObjectChange,
    });

    expect(root.children).toContain(runtime.resources.group);
    expect(sceneState.consumers.subscriberCount).toBe(1);

    sceneState.consumers.dispatch({ delta: 0.016, elapsed: 1, timestampMs: 1000 });
    expect(runtime.resources.group.position.toArray()).toEqual([4, 5, 6]);
    expect(runtime.resources.group.scale.x).toBeGreaterThan(0.04);

    const x = runtime.resources.targets.get('x')!;
    handlers.get(x)?.pointerdown?.(event(7, { x: 1, y: 2, z: 0 }, capture));
    expect(onDragStart).toHaveBeenCalledTimes(1);

    handlers.get(runtime.resources.group)?.pointermove?.(
      event(7, { x: 3.5, y: 2, z: 0 }, capture),
    );
    expect(object.position.x).toBeCloseTo(6.5, 12);
    expect(onObjectChange).toHaveBeenCalledTimes(1);

    handlers.get(runtime.resources.group)?.pointerup?.(
      event(7, { x: 3.5, y: 2, z: 0 }, capture),
    );
    expect(onDragEnd).toHaveBeenCalledTimes(1);

    runtime.dispose();
    runtime.dispose();
    expect(root.children).not.toContain(runtime.resources.group);
    expect(sceneState.consumers.subscriberCount).toBe(0);
    expect(handlers.size).toBe(0);
  });
});
