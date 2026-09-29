import { describe, expect, it } from 'vitest';
import { parseHgGlb } from './glbContainer';
import { addHgGltfAnimation, readHgGltfAnimations } from './gltfAnimation';
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

  it('preserves an existing GLB while appending first-party animation data', () => {
    const original = new HgGltfBuilder();
    const position = original.addAccessor(
      [0, 0, 0, 1, 0, 0, 0, 1, 0],
      { type: 'VEC3', componentType: 5126, target: 34962 },
    );
    original.json.meshes = [{ primitives: [{ attributes: { POSITION: position } }] }];
    original.json.nodes = [{ name: 'pelvis', mesh: 0 }];
    original.json.scenes = [{ nodes: [0] }];
    original.json.scene = 0;

    const source = parseHgGlb(original.toGlb());
    const preservedPosition = readHgAccessor(source, position).values;
    const builder = HgGltfBuilder.fromDocument(source);
    addHgGltfAnimation(builder, {
      name: 'test_clip',
      tracks: [{
        node: 0,
        path: 'rotation',
        times: [0, 1],
        values: [0, 0, 0, 1, 0, 0.1, 0, 0.9949874371],
      }],
    });

    const output = parseHgGlb(builder.toGlb());
    expect(readHgAccessor(output, position).values).toEqual(preservedPosition);
    expect((output.json.meshes as unknown[])).toEqual(source.json.meshes);
    expect((output.json.nodes as unknown[])).toEqual(source.json.nodes);
    expect(readHgGltfAnimations(output)).toMatchObject([{
      name: 'test_clip',
      channels: [{ node: 0, path: 'rotation' }],
    }]);
    expect((output.json.asset as { generator?: string }).generator)
      .toBe('Home Gym PT first-party codec');
  });

  it('rejects preserved GLBs that require more than one binary buffer', () => {
    const document = parseHgGlb(new HgGltfBuilder().toGlb());
    document.binaryChunks.push(new Uint8Array([1, 2, 3, 4]));
    expect(() => HgGltfBuilder.fromDocument(document)).toThrow(/one BIN chunk/);
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
