import { describe, expect, it } from 'vitest';
import { parseHgGlb } from './glbContainer';
import { HgGltfBuilder } from './gltfBuilder';
import { readHgAccessor } from './gltfAccessors';

describe('first-party glTF builder', () => {
  it('writes accessors that the first-party reader round-trips', () => {
    const builder = new HgGltfBuilder();
    const positions = builder.addAccessor(
      [-1, 0, 2, 3, 4, -5],
      { type: 'VEC3', componentType: 5126, target: 34962, includeMinMax: true },
    );
    const indices = builder.addAccessor(
      [0, 1, 2, 2, 1, 3],
      { type: 'SCALAR', componentType: 5123, target: 34963 },
    );

    builder.json.meshes = [{
      primitives: [{
        attributes: { POSITION: positions },
        indices,
      }],
    }];

    const parsed = parseHgGlb(builder.toGlb());
    expect(readHgAccessor(parsed, positions).values).toEqual([-1, 0, 2, 3, 4, -5]);
    expect(readHgAccessor(parsed, indices).values).toEqual([0, 1, 2, 2, 1, 3]);

    const accessor = (parsed.json.accessors as Record<string, unknown>[])[positions];
    expect(accessor.min).toEqual([-1, 0, -5]);
    expect(accessor.max).toEqual([3, 4, 2]);
  });

  it('aligns every bufferView to four bytes', () => {
    const builder = new HgGltfBuilder();
    builder.addAccessor([1, 2, 3], { type: 'SCALAR', componentType: 5121 });
    builder.addAccessor([1.25, 2.5], { type: 'SCALAR', componentType: 5126 });

    const parsed = parseHgGlb(builder.toGlb());
    const views = parsed.json.bufferViews as Array<Record<string, unknown>>;
    expect((views[0].byteOffset as number) % 4).toBe(0);
    expect((views[1].byteOffset as number) % 4).toBe(0);
  });

  it('rejects integer values outside their component range', () => {
    const builder = new HgGltfBuilder();
    expect(() => builder.addAccessor(
      [70000],
      { type: 'SCALAR', componentType: 5123 },
    )).toThrow(/range/);
  });

  it('rejects a scalar count incompatible with the accessor shape', () => {
    const builder = new HgGltfBuilder();
    expect(() => builder.addAccessor(
      [1, 2, 3, 4],
      { type: 'VEC3', componentType: 5126 },
    )).toThrow(/multiple/);
  });
});
