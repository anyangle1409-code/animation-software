import { describe, expect, it, vi } from 'vitest';
import {
  DeferredSceneResourceDisposer,
  type DeferredDisposalScheduler,
} from './sceneResourceLifecycle';

function scheduler() {
  let next = 1;
  const tasks = new Map<number, () => void>();
  const value: DeferredDisposalScheduler = {
    schedule(callback) {
      const id = next++;
      tasks.set(id, callback);
      return id as unknown as ReturnType<typeof setTimeout>;
    },
    cancel(handle) {
      tasks.delete(handle as unknown as number);
    },
  };
  return {
    value,
    flush() {
      const pending = [...tasks.values()];
      tasks.clear();
      for (const task of pending) task();
    },
    pending: () => tasks.size,
  };
}

describe('Strict-Mode-safe scene resource disposal', () => {
  it('cancels disposal when the same resource is immediately reactivated', () => {
    const clock = scheduler();
    const dispose = vi.fn();
    const resource = { dispose };
    const lifetime = new DeferredSceneResourceDisposer(clock.value);

    lifetime.activate(resource);
    lifetime.deactivate(resource);
    expect(clock.pending()).toBe(1);

    lifetime.activate(resource);
    expect(clock.pending()).toBe(0);
    clock.flush();
    expect(dispose).not.toHaveBeenCalled();
  });

  it('still disposes a replaced resource while the new one stays active', () => {
    const clock = scheduler();
    const oldDispose = vi.fn();
    const nextDispose = vi.fn();
    const oldResource = { dispose: oldDispose };
    const nextResource = { dispose: nextDispose };
    const lifetime = new DeferredSceneResourceDisposer(clock.value);

    lifetime.activate(oldResource);
    lifetime.deactivate(oldResource);
    lifetime.activate(nextResource);
    clock.flush();

    expect(oldDispose).toHaveBeenCalledTimes(1);
    expect(nextDispose).not.toHaveBeenCalled();
  });

  it('disposes once after a genuine unmount', () => {
    const clock = scheduler();
    const dispose = vi.fn();
    const resource = { dispose };
    const lifetime = new DeferredSceneResourceDisposer(clock.value);

    lifetime.activate(resource);
    lifetime.deactivate(resource);
    lifetime.deactivate(resource);
    expect(clock.pending()).toBe(1);

    clock.flush();
    expect(dispose).toHaveBeenCalledTimes(1);
  });
});
