import { describe, expect, it, vi } from 'vitest';
import { buildHgIKHandleSceneModel, HG_IK_HANDLE_COLOURS } from './ikHandleSceneModel';
import {
  createHgIKHandleScene,
  registerHgIKHandlePointers,
  updateHgIKHandleSelection,
} from './firstPartyIKHandleScene';

describe('first-party IK handle scene', () => {
  it('materialises every renderer-neutral handle model as a clickable primitive mesh', () => {
    const resources = createHgIKHandleScene();
    const model = buildHgIKHandleSceneModel();
    expect(resources.handles.size).toBe(model.length);

    for (const visual of model) {
      const mesh = resources.handles.get(visual.key)!;
      expect(mesh.name).toBe(`hgpt-ik-${visual.chain}-${visual.kind}`);
      expect(mesh.visible).toBe(false);
      expect(mesh.isMesh).toBe(true);
      expect(mesh.material.depthTest).toBe(false);
      expect(mesh.material.colour[3]).toBeCloseTo(0.9, 10);
      expect(mesh.geometry.indices.length).toBeGreaterThan(0);
    }
    resources.dispose();
    expect(resources.group.children).toHaveLength(0);
  });

  it('updates selected appearance and preserves pointer registration semantics', () => {
    const resources = createHgIKHandleScene();
    const first = buildHgIKHandleSceneModel()[0];
    updateHgIKHandleSelection(resources, {
      chain: first.chain,
      kind: first.kind,
    });
    const selected = resources.handles.get(first.key)!;
    expect(selected.material.colour.slice(0, 3)).toEqual([
      1,
      0xb4 / 255,
      0x3a / 255,
    ]);

    const registrations: Array<{ object: unknown; handlers: { pointerdown?: (event: { stopPropagation(): void }) => void } }> = [];
    const unregister = vi.fn();
    const select = vi.fn();
    const remove = registerHgIKHandlePointers(
      resources,
      {
        register(object, handlers) {
          registrations.push({ object, handlers });
          return unregister;
        },
      },
      select,
    );
    expect(registrations).toHaveLength(buildHgIKHandleSceneModel().length);
    const stop = vi.fn();
    registrations[0].handlers.pointerdown?.({ stopPropagation: stop });
    expect(stop).toHaveBeenCalledTimes(1);
    expect(select).toHaveBeenCalledWith({
      chain: first.chain,
      kind: first.kind,
    });
    remove();
    expect(unregister).toHaveBeenCalledTimes(registrations.length);
  });

  it('uses the canonical selected colour constant', () => {
    expect(HG_IK_HANDLE_COLOURS.selected).toBe('#ffb43a');
  });
});
