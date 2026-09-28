import { describe, expect, it } from 'vitest';
import type { HgFrameScheduler } from './frameLoop';
import { HgSceneLifecycle } from './sceneLifecycle';

function fixture() {
  let nextHandle = 1;
  const frames = new Map<number, (timestamp: number) => void>();
  const scheduler: HgFrameScheduler = {
    request: (cb) => { const handle = nextHandle++; frames.set(handle, cb); return handle; },
    cancel: (handle) => { frames.delete(handle); },
  };
  let width = 640;
  let height = 360;
  let dpr = 3;
  const listeners = {
    resize: new Set<() => void>(),
    lost: new Set<() => void>(),
    restored: new Set<() => void>(),
  };
  const sizes: { width: number; height: number; pixelRatio: number }[] = [];
  const surface = {
    measure: () => ({ width, height, devicePixelRatio: dpr }),
    onResize: (cb: () => void) => { listeners.resize.add(cb); return () => { listeners.resize.delete(cb); }; },
    onContextLost: (cb: () => void) => { listeners.lost.add(cb); return () => { listeners.lost.delete(cb); }; },
    onContextRestored: (cb: () => void) => { listeners.restored.add(cb); return () => { listeners.restored.delete(cb); }; },
  };
  const host = new HgSceneLifecycle(scheduler, surface, size => sizes.push(size));
  return {
    host, frames, sizes, listeners,
    resize(w: number, h: number, ratio = dpr) {
      width = w; height = h; dpr = ratio;
      for (const cb of listeners.resize) cb();
    },
    lose() { for (const cb of listeners.lost) cb(); },
    restore() { for (const cb of listeners.restored) cb(); },
    fire(timestamp: number) {
      const [handle, cb] = [...frames][0] ?? [];
      if (!cb) throw new Error('No frame scheduled');
      frames.delete(handle);
      cb(timestamp);
    },
  };
}

describe('project-owned scene lifecycle foundation', () => {
  it('owns one frame loop, preserves resolve-before-consumer order and stops on disposal', () => {
    const x = fixture();
    const calls: string[] = [];
    x.host.onFrame(() => calls.push('visual'));
    x.host.onFrame(() => calls.push('resolve'), -1);
    x.host.mount();
    x.host.mount();
    expect(x.frames.size).toBe(1);
    x.fire(1000);
    expect(calls).toEqual(['resolve', 'visual']);
    expect(x.frames.size).toBe(1);
    x.host.dispose();
    x.host.dispose();
    expect(x.frames.size).toBe(0);
    expect(Object.values(x.listeners).every(set => set.size === 0)).toBe(true);
    expect(() => x.host.mount()).toThrow(/disposed/);
  });

  it('clamps DPR to the existing Canvas range and pauses for zero sized surfaces', () => {
    const x = fixture();
    x.host.mount();
    expect(x.sizes).toEqual([{ width: 640, height: 360, pixelRatio: 2 }]);
    x.resize(320, 200, .5);
    expect(x.sizes.at(-1)).toEqual({ width: 320, height: 200, pixelRatio: 1 });
    x.resize(0, 200);
    expect(x.frames.size).toBe(0);
    x.resize(320, 200);
    expect(x.frames.size).toBe(1);
  });

  it('pauses on context loss and resumes once on restoration with fresh size', () => {
    const x = fixture();
    x.host.mount();
    x.lose();
    expect(x.frames.size).toBe(0);
    x.resize(800, 400);
    expect(x.frames.size).toBe(0);
    x.restore();
    x.restore();
    expect(x.frames.size).toBe(1);
    expect(x.sizes.at(-1)).toEqual({ width: 800, height: 400, pixelRatio: 2 });
  });
});
