import { describe, expect, it, vi } from 'vitest';
import {
  HgWebGLRenderer,
  type HgWebGLCanvasPort,
  type HgWebGLContextPort,
} from './webglRenderer';

function fixture() {
  const calls: Array<[string, ...number[]]> = [];
  const loseContext = vi.fn();
  const gl: HgWebGLContextPort = {
    COLOR_BUFFER_BIT: 0x4000,
    DEPTH_BUFFER_BIT: 0x0100,
    DEPTH_TEST: 0x0b71,
    viewport: (...values) => calls.push(['viewport', ...values]),
    clearColor: (...values) => calls.push(['clearColor', ...values]),
    enable: (value) => calls.push(['enable', value]),
    clear: (value) => calls.push(['clear', value]),
    getExtension: (name) => name === 'WEBGL_lose_context' ? { loseContext } : null,
  };
  const canvas: HgWebGLCanvasPort = {
    width: 1,
    height: 1,
    style: { width: '', height: '' },
    getContext: () => gl as unknown as WebGL2RenderingContext,
  };
  return { gl, canvas, calls, loseContext };
}

describe('first-party WebGL renderer foundation', () => {
  it('owns DPR-aware drawing-buffer sizing without a rendering library', () => {
    const x = fixture();
    const renderer = new HgWebGLRenderer(x.canvas, x.gl);
    renderer.setPixelRatio(2);
    renderer.setSize(320, 180, false);
    expect([x.canvas.width, x.canvas.height]).toEqual([640, 360]);
    expect(x.canvas.style).toEqual({ width: '', height: '' });

    renderer.setSize(200, 100, true);
    expect([x.canvas.width, x.canvas.height]).toEqual([400, 200]);
    expect(x.canvas.style).toEqual({ width: '200px', height: '100px' });
  });

  it('clears colour/depth deterministically and counts submitted frames', () => {
    const x = fixture();
    const renderer = new HgWebGLRenderer(x.canvas, x.gl);
    renderer.setSize(100, 50, false);
    renderer.setClearColor(0.1, 0.2, 0.3, 1);
    renderer.beginFrame();
    renderer.beginFrame();

    expect(renderer.info.render.frame).toBe(2);
    expect(x.calls).toContainEqual(['clearColor', 0.1, 0.2, 0.3, 1]);
    expect(x.calls).toContainEqual([
      'clear',
      x.gl.COLOR_BUFFER_BIT | x.gl.DEPTH_BUFFER_BIT,
    ]);
    expect(x.calls).toContainEqual(['viewport', 0, 0, 100, 50]);
  });

  it('disposes the native context once and rejects later mutation', () => {
    const x = fixture();
    const renderer = new HgWebGLRenderer(x.canvas, x.gl);
    renderer.dispose();
    renderer.dispose();
    expect(x.loseContext).toHaveBeenCalledTimes(1);
    expect(() => renderer.beginFrame()).toThrow(/disposed/);
  });
});
