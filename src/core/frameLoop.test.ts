import { describe, expect, it } from 'vitest';
import { HgFrameLoop } from './frameLoop';
import type { HgFrameScheduler } from './frameLoop';

function fakeScheduler() {
  let nextHandle = 1;
  const callbacks = new Map<number, (time: number) => void>();
  const cancelled: number[] = [];

  const scheduler: HgFrameScheduler = {
    request(callback) {
      const handle = nextHandle++;
      callbacks.set(handle, callback);
      return handle;
    },
    cancel(handle) {
      callbacks.delete(handle);
      cancelled.push(handle);
    },
  };

  return {
    scheduler,
    callbacks,
    cancelled,
    fire(handle: number, time: number) {
      const callback = callbacks.get(handle);
      if (!callback) throw new Error(`No callback for handle ${handle}`);
      callbacks.delete(handle);
      callback(time);
    },
  };
}

describe('first-party frame loop', () => {
  it('runs lower priorities first and preserves insertion order within a priority', () => {
    const fake = fakeScheduler();
    const loop = new HgFrameLoop(fake.scheduler);
    const order: string[] = [];

    loop.add(() => order.push('normal-a'), 0);
    loop.add(() => order.push('resolve'), -1);
    loop.add(() => order.push('normal-b'), 0);
    loop.add(() => order.push('late'), 10);

    loop.tick(1000);
    expect(order).toEqual(['resolve', 'normal-a', 'normal-b', 'late']);
  });

  it('resolves exactly once before all pose consumers even when subscribed later', () => {
    const loop = new HgFrameLoop(fakeScheduler().scheduler);
    const seen: string[] = [];
    let resolved = 0;
    loop.add(() => { resolved += 1; seen.push(`resolve:${resolved}`); }, -1);
    loop.add(() => seen.push(`character:${resolved}`));
    loop.add(() => seen.push(`equipment:${resolved}`));
    loop.tick(1000);
    loop.tick(1016);
    expect(seen).toEqual([
      'resolve:1', 'character:1', 'equipment:1',
      'resolve:2', 'character:2', 'equipment:2',
    ]);
  });

  it('reports deterministic delta and elapsed time', () => {
    const fake = fakeScheduler();
    const loop = new HgFrameLoop(fake.scheduler);
    const frames: { delta: number; elapsed: number }[] = [];
    loop.add(({ delta, elapsed }) => frames.push({ delta, elapsed }));

    loop.tick(1000);
    loop.tick(1016);
    loop.tick(1050);

    expect(frames[0]).toEqual({ delta: 0, elapsed: 0 });
    expect(frames[1].delta).toBeCloseTo(0.016, 12);
    expect(frames[1].elapsed).toBeCloseTo(0.016, 12);
    expect(frames[2].delta).toBeCloseTo(0.034, 12);
    expect(frames[2].elapsed).toBeCloseTo(0.05, 12);
  });

  it('lets one callback remove a later callback safely', () => {
    const fake = fakeScheduler();
    const loop = new HgFrameLoop(fake.scheduler);
    const calls: string[] = [];

    let removeLater = () => {};
    loop.add(() => {
      calls.push('first');
      removeLater();
    }, -1);
    removeLater = loop.add(() => calls.push('later'), 0);

    loop.tick(0);
    expect(calls).toEqual(['first']);
  });

  it('starts and stops through the injected scheduler', () => {
    const fake = fakeScheduler();
    const loop = new HgFrameLoop(fake.scheduler);
    let calls = 0;
    loop.add(() => { calls += 1; });

    loop.start();
    expect(loop.isRunning).toBe(true);
    const firstHandle = [...fake.callbacks.keys()][0];
    fake.fire(firstHandle, 1000);
    expect(calls).toBe(1);
    expect(fake.callbacks.size).toBe(1);

    loop.stop();
    expect(loop.isRunning).toBe(false);
    expect(fake.callbacks.size).toBe(0);
    expect(fake.cancelled.length).toBe(1);
  });
});
