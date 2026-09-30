import { HgPerspectiveCamera } from '../core/sceneGraph';
import { describe, expect, it, vi } from 'vitest';
import { createSceneState } from './sceneStateCore';
import { createOrbitControlsRuntime } from './orbitControlsRuntime';

interface ListenerMap {
  [type: string]: EventListenerOrEventListenerObject | undefined;
}

function fakeCanvas() {
  const listeners: ListenerMap = {};
  const captured = new Set<number>();
  const element = {
    style: { touchAction: 'auto' },
    clientHeight: 600,
    addEventListener: vi.fn((type: string, listener: EventListenerOrEventListenerObject) => {
      listeners[type] = listener;
    }),
    removeEventListener: vi.fn((type: string) => {
      delete listeners[type];
    }),
    setPointerCapture: vi.fn((id: number) => captured.add(id)),
    hasPointerCapture: vi.fn((id: number) => captured.has(id)),
    releasePointerCapture: vi.fn((id: number) => captured.delete(id)),
  } as unknown as HTMLCanvasElement;
  return { element, listeners, captured };
}

function fire(
  listeners: ListenerMap,
  type: string,
  event: Partial<PointerEvent & WheelEvent>,
) {
  const listener = listeners[type];
  if (!listener) throw new Error(`Missing ${type} listener`);
  const payload = event as Event;
  if (typeof listener === 'function') listener(payload);
  else listener.handleEvent(payload);
}

describe('framework-neutral orbit runtime', () => {
  it('owns input/frame lifecycle and restores the canvas on dispose', () => {
    const camera = new HgPerspectiveCamera(38, 1, 0.05, 100);
    camera.position.set(2.3, 1.35, 2.7);
    const sceneState = createSceneState();
    const { element, listeners, captured } = fakeCanvas();

    const runtime = createOrbitControlsRuntime(camera, element, sceneState);

    expect(element.style.touchAction).toBe('none');
    expect(sceneState.consumers.subscriberCount).toBe(1);
    expect(Object.keys(listeners).sort()).toEqual([
      'pointercancel',
      'pointerdown',
      'pointermove',
      'pointerup',
      'wheel',
    ]);

    const before = camera.position.clone();
    fire(listeners, 'pointerdown', {
      pointerId: 1,
      pointerType: 'mouse',
      button: 0,
      clientX: 100,
      clientY: 100,
    });
    expect(captured.has(1)).toBe(true);
    fire(listeners, 'pointermove', {
      pointerId: 1,
      pointerType: 'mouse',
      clientX: 160,
      clientY: 120,
    });
    sceneState.consumers.dispatch({ delta: 0.016, elapsed: 1, timestampMs: 1000 });
    expect(camera.position.distanceTo(before)).toBeGreaterThan(0);

    const preventDefault = vi.fn();
    fire(listeners, 'wheel', { deltaY: 120, preventDefault });
    expect(preventDefault).toHaveBeenCalledTimes(1);

    fire(listeners, 'pointerup', { pointerId: 1 });
    expect(captured.has(1)).toBe(false);

    runtime.dispose();
    runtime.dispose();

    expect(sceneState.consumers.subscriberCount).toBe(0);
    expect(element.style.touchAction).toBe('auto');
    expect(Object.keys(listeners)).toHaveLength(0);
  });
});
