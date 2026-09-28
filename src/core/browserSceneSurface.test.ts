import { describe, expect, it } from 'vitest';
import { browserSceneSurface } from './browserSceneSurface';

function fixture() {
  const canvasEvents = new Map<string, Set<(event: Event) => void>>();
  const windowEvents = new Map<string, Set<() => void>>();
  const canvas = {
    addEventListener(name: string, cb: (event: Event) => void) {
      if (!canvasEvents.has(name)) canvasEvents.set(name, new Set());
      canvasEvents.get(name)!.add(cb);
    },
    removeEventListener(name: string, cb: (event: Event) => void) { canvasEvents.get(name)?.delete(cb); },
  } as unknown as HTMLCanvasElement;
  let width = 500;
  let height = 300;
  const container = { getBoundingClientRect: () => ({ width, height }) } as Element;
  const browser = {
    devicePixelRatio: 2.5,
    addEventListener(name: string, cb: () => void) {
      if (!windowEvents.has(name)) windowEvents.set(name, new Set());
      windowEvents.get(name)!.add(cb);
    },
    removeEventListener(name: string, cb: () => void) { windowEvents.get(name)?.delete(cb); },
  } as unknown as Window;
  let observerCallback = () => {};
  let observed = false;
  const observerFactory = (cb: () => void) => ({
    observe(target: Element) { expect(target).toBe(container); observed = true; observerCallback = cb; },
    disconnect() { observed = false; },
  });
  const surface = browserSceneSurface(canvas, container, browser, observerFactory);
  return {
    surface, canvasEvents, windowEvents,
    get observed() { return observed; },
    resize(w: number, h: number) { width = w; height = h; observerCallback(); },
    browserResize() { for (const cb of windowEvents.get('resize') ?? []) cb(); },
    emit(name: string, event: Event) { for (const cb of canvasEvents.get(name) ?? []) cb(event); },
  };
}

describe('browser scene surface adapter', () => {
  it('measures CSS dimensions and DPR and releases resize observers/listeners', () => {
    const x = fixture();
    expect(x.surface.measure()).toEqual({ width: 500, height: 300, devicePixelRatio: 2.5 });
    let calls = 0;
    const remove = x.surface.onResize(() => { calls += 1; });
    expect(x.observed).toBe(true);
    x.resize(300, 200);
    x.browserResize();
    expect(calls).toBe(2);
    expect(x.surface.measure().width).toBe(300);
    remove();
    expect(x.observed).toBe(false);
    expect(x.windowEvents.get('resize')?.size).toBe(0);
  });

  it('prevents default context loss so restoration can occur, then removes events', () => {
    const x = fixture();
    let losses = 0;
    let restores = 0;
    const removeLoss = x.surface.onContextLost(() => { losses += 1; });
    const removeRestore = x.surface.onContextRestored(() => { restores += 1; });
    let prevented = false;
    x.emit('webglcontextlost', { preventDefault: () => { prevented = true; } } as Event);
    x.emit('webglcontextrestored', {} as Event);
    expect({ losses, restores, prevented }).toEqual({ losses: 1, restores: 1, prevented: true });
    removeLoss();
    removeRestore();
    expect(x.canvasEvents.get('webglcontextlost')?.size).toBe(0);
    expect(x.canvasEvents.get('webglcontextrestored')?.size).toBe(0);
  });
});
