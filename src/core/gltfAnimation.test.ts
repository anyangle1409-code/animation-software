import { describe, expect, it } from 'vitest';
import { parseHgGlb } from './glbContainer';
import { HgGltfBuilder } from './gltfBuilder';
import { addHgGltfAnimation, readHgGltfAnimations } from './gltfAnimation';

describe('first-party glTF animation codec', () => {
  it('round-trips translation, rotation, scale and morph-weight tracks', () => {
    const builder = new HgGltfBuilder();
    builder.json.nodes = [{ name: 'root' }];

    addHgGltfAnimation(builder, {
      name: 'curl',
      tracks: [
        {
          node: 0,
          path: 'translation',
          times: [0, 1],
          values: [0, 0, 0, 0, 0.2, 0],
        },
        {
          node: 0,
          path: 'rotation',
          times: [0, 1],
          values: [0, 0, 0, 1, 0.2, 0, 0, 0.9797958971],
        },
        {
          node: 0,
          path: 'scale',
          times: [0, 1],
          values: [1, 1, 1, 1, 1.1, 1],
        },
        {
          node: 0,
          path: 'weights',
          times: [0, 1],
          values: [0, 0.2, 0.8, 1],
        },
      ],
    });

    const decoded = readHgGltfAnimations(parseHgGlb(builder.toGlb()));
    expect(decoded).toHaveLength(1);
    expect(decoded[0].name).toBe('curl');
    expect(decoded[0].channels.map((channel) => [channel.path, channel.valueSize])).toEqual([
      ['translation', 3],
      ['rotation', 4],
      ['scale', 3],
      ['weights', 2],
    ]);
    expect(decoded[0].channels[0].times).toEqual([0, 1]);
    expect(decoded[0].channels[0].values).toEqual(Array.from(new Float32Array([0, 0, 0, 0, 0.2, 0])));
    expect(decoded[0].channels[3].values).toEqual(Array.from(new Float32Array([0, 0.2, 0.8, 1])));
  });

  it('rejects non-increasing keyframe times before writing', () => {
    const builder = new HgGltfBuilder();
    builder.json.nodes = [{}];
    expect(() => addHgGltfAnimation(builder, {
      tracks: [{
        node: 0,
        path: 'translation',
        times: [0, 0],
        values: [0, 0, 0, 1, 0, 0],
      }],
    })).toThrow(/strictly increasing/);
  });

  it('rejects unsupported interpolation on read', () => {
    const builder = new HgGltfBuilder();
    builder.json.nodes = [{}];
    const input = builder.addAccessor([0, 1], { type: 'SCALAR', componentType: 5126 });
    const output = builder.addAccessor(
      [0, 0, 0, 1, 0, 0],
      { type: 'VEC3', componentType: 5126 },
    );
    builder.json.animations = [{
      samplers: [{ input, output, interpolation: 'CUBICSPLINE' }],
      channels: [{ sampler: 0, target: { node: 0, path: 'translation' } }],
    }];

    expect(() => readHgGltfAnimations(parseHgGlb(builder.toGlb()))).toThrow(/LINEAR/);
  });

  it('rejects a rotation sampler with the wrong output shape', () => {
    const builder = new HgGltfBuilder();
    builder.json.nodes = [{}];
    const input = builder.addAccessor([0, 1], { type: 'SCALAR', componentType: 5126 });
    const output = builder.addAccessor(
      [0, 0, 0, 0, 0, 0],
      { type: 'VEC3', componentType: 5126 },
    );
    builder.json.animations = [{
      samplers: [{ input, output }],
      channels: [{ sampler: 0, target: { node: 0, path: 'rotation' } }],
    }];

    expect(() => readHgGltfAnimations(parseHgGlb(builder.toGlb()))).toThrow(/shape/);
  });

  it('rejects animation channels that target a missing node', () => {
    const builder = new HgGltfBuilder();
    builder.json.nodes = [{}];
    expect(() => addHgGltfAnimation(builder, {
      tracks: [{
        node: 2,
        path: 'scale',
        times: [0, 1],
        values: [1, 1, 1, 1, 1, 1],
      }],
    })).toThrow(/missing node/);
  });
});
