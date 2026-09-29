import { describe, expect, it, vi } from 'vitest';
import { HgMat4 } from './linearMath';
import { boxPrimitiveData } from './primitiveGeometry';
import { HgPerspectiveCamera } from './sceneGraph';
import { HgLitTrianglePipeline } from './webglLitTrianglePipeline';
import { HgLitPrimitiveRenderer } from './webglLitRenderer';
import { hgClipMatrix } from './webglFlatRenderer';

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
    DEPTH_TEST: 0x0b71,
    CULL_FACE: 0x0b44,
    LEQUAL: 0x0203,
    BACK: 0x0405,
    CCW: 0x0901,
    COLOR_BUFFER_BIT: 0x4000,
    DEPTH_BUFFER_BIT: 0x0100,
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
    enable: vi.fn((value: number) => calls.push(['enable', value])),
    depthFunc: vi.fn(),
    cullFace: vi.fn(),
    frontFace: vi.fn(),
    viewport: vi.fn((x: number, y: number, width: number, height: number) =>
      calls.push(['viewport', x, y, width, height])),
    clearColor: vi.fn((...values: number[]) => calls.push(['clearColor', ...values])),
    clear: vi.fn((mask: number) => calls.push(['clear', mask])),
    useProgram: vi.fn(),
    bindBuffer: vi.fn(),
    bufferData: vi.fn((_target: number, values: Float32Array) =>
      calls.push(['bufferData', values.length])),
    enableVertexAttribArray: vi.fn(),
    vertexAttribPointer: vi.fn(),
    uniformMatrix4fv: vi.fn((_location: unknown, _transpose: boolean, values: Float32Array) =>
      calls.push(['matrix', ...values])),
    uniform4fv: vi.fn((_location: unknown, values: Float32Array) =>
      calls.push(['colour', ...values])),
    uniform3fv: vi.fn((_location: unknown, values: Float32Array) =>
      calls.push(['light', ...values])),
    uniform1f: vi.fn((_location: unknown, value: number) =>
      calls.push(['ambient', value])),
    drawArrays: vi.fn((mode: number, first: number, count: number) =>
      calls.push(['draw', mode, first, count])),
  } as unknown as WebGL2RenderingContext;
  return { gl, calls };
}

describe('first-party lit primitive renderer', () => {
  it('owns viewport, depth/culling, clear and lit indexed primitive submission', () => {
    const x = fakeGl();
    const pipeline = new HgLitTrianglePipeline(x.gl);
    pipeline.setViewport(640, 360, 2);
    pipeline.clear([0.08, 0.09, 0.11, 1]);

    const camera = new HgPerspectiveCamera(38, 640 / 360, 0.05, 100);
    camera.position.set(2.3, 1.35, 2.7);
    camera.lookAt(0, 0.8, 0);
    camera.updateWorldMatrix(true, false);

    const renderer = new HgLitPrimitiveRenderer(pipeline);
    const world = new HgMat4().makeTranslation(0.2, 0.9, -0.1);
    const box = boxPrimitiveData([0.4, 0.2, 0.3]);
    renderer.draw(camera, world, box, [0.7, 0.3, 0.2, 1]);

    expect(x.calls).toContainEqual(['viewport', 0, 0, 1280, 720]);
    expect(x.calls).toContainEqual(['enable', 0x0b71]);
    expect(x.calls).toContainEqual(['enable', 0x0b44]);
    expect(x.calls).toContainEqual(['clear', 0x4000 | 0x0100]);
    expect(x.calls.filter((entry) => entry[0] === 'bufferData')).toHaveLength(2);
    expect(x.calls.find((entry) => entry[0] === 'draw'))
      .toEqual(['draw', 0x0004, 0, box.indices.length]);
    expect(x.calls.find((entry) => entry[0] === 'light')).toBeDefined();

    const matrices = x.calls.filter((entry) => entry[0] === 'matrix');
    expect(matrices).toHaveLength(2);
    expect(matrices[0].slice(1)).toEqual(
      Array.from(new Float32Array(hgClipMatrix(camera, world).elements)),
    );
  });

  it('validates input and disposes GPU resources once', () => {
    const x = fakeGl();
    const pipeline = new HgLitTrianglePipeline(x.gl);
    expect(() => pipeline.setAmbient(1.1)).toThrow(/between 0 and 1/);
    expect(() => pipeline.setLightDirection({ x: 0, y: 0, z: 0 }))
      .toThrow(/cannot be zero/);
    expect(() => pipeline.setViewport(0, 100)).toThrow(/positive/);
    pipeline.dispose();
    pipeline.dispose();
    expect((x.gl.deleteBuffer as unknown as ReturnType<typeof vi.fn>)).toHaveBeenCalledTimes(2);
    expect((x.gl.deleteProgram as unknown as ReturnType<typeof vi.fn>)).toHaveBeenCalledTimes(1);
  });
});
