import { describe, expect, it } from 'vitest';
import type { HgFrame, HgFrameScheduler } from '../core/frameLoop';
import type { HgSceneSurface } from '../core/sceneLifecycle';
import { HgScene } from '../core/sceneGraph';
import { FirstPartySceneHost } from './firstPartySceneHost';

function fixture() {
  let handle = 0;
  const pending = new Map<number, (timestamp: number) => void>();
  const scheduler: HgFrameScheduler = {
    request(cb) { pending.set(++handle, cb); return handle; },
    cancel(id) { pending.delete(id); },
  };
  const listeners = {
    resize: new Set<() => void>(),
    lost: new Set<() => void>(),
    restored: new Set<() => void>(),
  };
  let width = 600;
  let height = 300;
  const surface: HgSceneSurface = {
    measure: () => ({ width, height, devicePixelRatio: 2.5 }),
    onResize(cb) { listeners.resize.add(cb); return () => { listeners.resize.delete(cb); }; },
    onContextLost(cb) { listeners.lost.add(cb); return () => { listeners.lost.delete(cb); }; },
    onContextRestored(cb) { listeners.restored.add(cb); return () => { listeners.restored.delete(cb); }; },
  };
  const calls: string[] = [];
  let disposed = 0;
  const renderer = {
    setPixelRatio(value: number) { calls.push(`dpr:${value}`); },
    setSize(w: number, h: number, updateStyle: boolean) {
      calls.push(`size:${w}:${h}:${updateStyle}`);
    },
    render(scene: HgScene) { calls.push(`render:${scene.type}`); },
    dispose() { disposed += 1; },
  };
  const host = new FirstPartySceneHost(scheduler, surface, renderer);
  return {
    host, calls, pending, listeners,
    get disposed() { return disposed; },
    resize(w: number, h: number) {
      width = w; height = h;
      for (const cb of listeners.resize) cb();
    },
    lose() { for (const cb of listeners.lost) cb(); },
    restore() { for (const cb of listeners.restored) cb(); },
    fire(time: number) {
      const [id, cb] = [...pending][0] ?? [];
      if (!cb) throw new Error('no scheduled frame');
      pending.delete(id);
      cb(time);
    },
  };
}

describe('first-party scene host', () => {
  it('matches live camera defaults and renders after resolved-pose consumers', () => {
    const x = fixture();
    expect(x.host.scene).toBeInstanceOf(HgScene);
    expect(x.host.camera.position.toArray()).toEqual([2.3, 1.35, 2.7]);
    expect([x.host.camera.fov, x.host.camera.near, x.host.camera.far])
      .toEqual([38, 0.05, 100]);
    expect(() => x.host.onFrame(() => {}, 1000)).toThrow(/precede render/);
    x.host.onFrame(() => x.calls.push('pose'), 0);
    x.host.onFrame((_frame: HgFrame) => x.calls.push('resolve'), -1);
    x.host.mount();
    expect(x.host.camera.aspect).toBe(2);
    expect(x.calls).toEqual(['dpr:2', 'size:600:300:false']);
    x.fire(1000);
    expect(x.calls.slice(-3)).toEqual(['resolve', 'pose', 'render:Scene']);
    expect(x.pending.size).toBe(1);
  });

  it('updates projection and respects context-loss/disposal lifecycle', () => {
    const x = fixture();
    x.host.mount();
    x.resize(400, 400);
    expect(x.host.camera.aspect).toBe(1);
    expect(x.calls.slice(-2)).toEqual(['dpr:2', 'size:400:400:false']);
    x.lose();
    expect(x.pending.size).toBe(0);
    x.restore();
    expect(x.pending.size).toBe(1);
    x.host.dispose();
    x.host.dispose();
    expect(x.disposed).toBe(1);
    expect(x.pending.size).toBe(0);
    expect(Object.values(x.listeners).every((set) => set.size === 0)).toBe(true);
  });
});
