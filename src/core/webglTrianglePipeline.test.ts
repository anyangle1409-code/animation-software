import { describe, expect, it, vi } from 'vitest';
import { HgMat4 } from './linearMath';
import { HgTrianglePipeline } from './webglTrianglePipeline';

function fakeGl() {
  const calls: Array<[string, ...unknown[]]> = [];
  const gl = {
    VERTEX_SHADER: 0x8b31,
    FRAGMENT_SHADER: 0x8b30,
    COMPILE_STATUS: 0x8b81,
    LINK_STATUS: 0x8b82,
    ARRAY_BUFFER: 0x8892,
    STREAM_DRAW: 0x88e0,
    FLOAT: 0x1406,
    TRIANGLES: 0x0004,
    createShader: vi.fn((type: number) => ({ type })),
    shaderSource: vi.fn(),
    compileShader: vi.fn(),
    getShaderParameter: vi.fn(() => true),
    getShaderInfoLog: vi.fn(() => ''),
    deleteShader: vi.fn(),
    createProgram: vi.fn(() => ({ program: true })),
    attachShader: vi.fn(),
    linkProgram: vi.fn(),
    getProgramParameter: vi.fn(() => true),
    getProgramInfoLog: vi.fn(() => ''),
    deleteProgram: vi.fn(),
    createBuffer: vi.fn(() => ({ buffer: true })),
    deleteBuffer: vi.fn(),
    getUniformLocation: vi.fn((_program: unknown, name: string) => ({ name })),
    useProgram: vi.fn(),
    bindBuffer: vi.fn(),
    bufferData: vi.fn((_target: number, values: Float32Array) => {
      calls.push(['bufferData', ...values]);
    }),
    enableVertexAttribArray: vi.fn(),
    vertexAttribPointer: vi.fn(),
    uniformMatrix4fv: vi.fn((_location: unknown, _transpose: boolean, values: Float32Array) => {
      calls.push(['matrix', ...values]);
    }),
    uniform4fv: vi.fn((_location: unknown, values: Float32Array) => {
      calls.push(['colour', ...values]);
    }),
    drawArrays: vi.fn((mode: number, first: number, count: number) => {
      calls.push(['draw', mode, first, count]);
    }),
  } as unknown as WebGL2RenderingContext;
  return { gl, calls };
}

describe('first-party WebGL triangle pipeline', () => {
  it('compiles project-owned shaders and draws transformed triangles', () => {
    const x = fakeGl();
    const pipeline = new HgTrianglePipeline(x.gl);
    const matrix = new HgMat4().makeTranslation(0.2, -0.1, 0.4);
    pipeline.draw({
      positions: new Float32Array([
        -0.5, -0.5, 0,
         0.5, -0.5, 0,
         0.0,  0.5, 0,
      ]),
      matrix,
      colour: [0.2, 0.4, 0.8, 1],
    });

    expect(x.calls.find((entry) => entry[0] === 'draw'))
      .toEqual(['draw', 0x0004, 0, 3]);
    expect(x.calls.find((entry) => entry[0] === 'matrix')?.slice(1))
      .toEqual(Array.from(new Float32Array(matrix.elements)));
    expect(x.calls.find((entry) => entry[0] === 'colour')?.slice(1))
      .toEqual(Array.from(new Float32Array([0.2, 0.4, 0.8, 1])));
  });

  it('rejects incomplete triangles and disposes GPU resources once', () => {
    const x = fakeGl();
    const pipeline = new HgTrianglePipeline(x.gl);
    expect(() => pipeline.draw({
      positions: new Float32Array([0, 0, 0]),
      matrix: new HgMat4(),
      colour: [1, 1, 1, 1],
    })).toThrow(/complete XYZ triangles/);

    pipeline.dispose();
    pipeline.dispose();
    expect((x.gl.deleteBuffer as unknown as ReturnType<typeof vi.fn>)).toHaveBeenCalledTimes(1);
    expect((x.gl.deleteProgram as unknown as ReturnType<typeof vi.fn>)).toHaveBeenCalledTimes(1);
  });
});
