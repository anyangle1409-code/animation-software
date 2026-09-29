import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { characterTriangleBuffers } from './webglCharacterTrianglePipeline';

describe('first-party character triangle buffers', () => {
  it('expands indexed posed geometry while preserving vertex colours', () => {
    const buffers = characterTriangleBuffers({
      positions: [
        0, 0, 0,
        1, 0, 0,
        0, 1, 0,
        1, 1, 0,
      ],
      normals: [
        0, 0, 1,
        0, 0, 1,
        0, 0, 1,
        0, 0, 1,
      ],
      uvs: [0, 0, 1, 0, 0, 1, 1, 1],
      colours: [
        1, 0, 0,
        0, 1, 0,
        0, 0, 1,
        1, 1, 0,
      ],
      indices: [0, 1, 2, 2, 1, 3],
    });

    expect(Array.from(buffers.positions)).toEqual([
      0, 0, 0,
      1, 0, 0,
      0, 1, 0,
      0, 1, 0,
      1, 0, 0,
      1, 1, 0,
    ]);
    expect(Array.from(buffers.normals)).toEqual([
      0, 0, 1,
      0, 0, 1,
      0, 0, 1,
      0, 0, 1,
      0, 0, 1,
      0, 0, 1,
    ]);
    expect(Array.from(buffers.uvs)).toEqual([
      0, 0,
      1, 0,
      0, 1,
      0, 1,
      1, 0,
      1, 1,
    ]);
    expect(Array.from(buffers.colours)).toEqual([
      1, 0, 0,
      0, 1, 0,
      0, 0, 1,
      0, 0, 1,
      0, 1, 0,
      1, 1, 0,
    ]);
  });

  it('uses white vertex colour when the mesh has no colour attribute', () => {
    const buffers = characterTriangleBuffers({
      positions: [0, 0, 0, 1, 0, 0, 0, 1, 0],
      normals: [0, 0, 1, 0, 0, 1, 0, 0, 1],
      indices: [0, 1, 2],
    });
    expect(Array.from(buffers.uvs)).toEqual([0, 0, 0, 0, 0, 0]);
    expect(Array.from(buffers.colours)).toEqual([
      1, 1, 1,
      1, 1, 1,
      1, 1, 1,
    ]);
  });

  it('rejects malformed character draw buffers', () => {
    expect(() => characterTriangleBuffers({
      positions: [0, 0, 0],
      normals: [0, 0],
      indices: [0, 0, 0],
    })).toThrow(/normals/i);

    expect(() => characterTriangleBuffers({
      positions: [0, 0, 0],
      normals: [0, 0, 1],
      indices: [0, 1, 0],
    })).toThrow(/outside/i);
  });
  it('owns UV upload and base-texture sampling in the first-party shader', () => {
    const source = readFileSync(
      new URL('./webglCharacterTrianglePipeline.ts', import.meta.url),
      'utf8',
    );
    expect(source).toContain('layout(location = 3) in vec2 a_uv');
    expect(source).toContain('texture(u_baseTexture, v_uv)');
    expect(source).toContain('gl.texImage2D(');
    expect(source).toContain('gl.vertexAttribPointer(3, 2');
    expect(source).toContain('UNPACK_FLIP_Y_WEBGL');
    expect(source).toContain('SRGB8_ALPHA8');
  });

});
