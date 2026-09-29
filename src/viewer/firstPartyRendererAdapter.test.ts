import { describe, expect, it, vi } from 'vitest';
import { HgPerspectiveCamera, HgScene } from '../core/sceneGraph';
import { HgFirstPartyRendererAdapterCore } from './firstPartyRendererAdapter';

describe('first-party viewer renderer adapter', () => {
  it('begins one project frame, submits the HgScene and reports frame/draw counts', () => {
    const surface = {
      info: { render: { frame: 0 } },
      setPixelRatio: vi.fn(),
      setSize: vi.fn(),
      setClearColor: vi.fn(),
      beginFrame: vi.fn(),
      dispose: vi.fn(),
    };
    surface.beginFrame.mockImplementation(() => {
      surface.info.render.frame += 1;
    });
    const render = vi.fn(() => 7);
    const disposePipelines = vi.fn();
    const adapter = new HgFirstPartyRendererAdapterCore(
      surface,
      { render },
      disposePipelines,
    );
    const scene = new HgScene();
    scene.background = '#123456';
    const camera = new HgPerspectiveCamera();

    adapter.port.setPixelRatio(2);
    adapter.port.setSize(640, 360, false);
    adapter.port.render(scene, camera);

    expect(surface.setPixelRatio).toHaveBeenCalledWith(2);
    expect(surface.setSize).toHaveBeenCalledWith(640, 360, false);
    expect(surface.setClearColor).toHaveBeenCalledTimes(1);
    expect(surface.beginFrame).toHaveBeenCalledTimes(1);
    expect(render).toHaveBeenCalledWith(scene, camera);
    expect(adapter.frame()).toBe(1);
    expect(adapter.drawCount()).toBe(7);

    adapter.port.dispose();
    adapter.port.dispose();
    expect(disposePipelines).toHaveBeenCalledTimes(1);
    expect(surface.dispose).toHaveBeenCalledTimes(1);
    expect(() => adapter.port.render(scene, camera)).toThrow(/disposed/);
  });
});
