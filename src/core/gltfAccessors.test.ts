import { describe, expect, it } from 'vitest';
import { encodeHgGlb, parseHgGlb } from './glbContainer';
import { readHgAccessor } from './gltfAccessors';

function glb(json: Record<string, unknown>, binary: Uint8Array) {
  return parseHgGlb(encodeHgGlb(json, [binary]));
}

describe('first-party glTF accessor reader', () => {
  it('reads tightly packed float VEC3 values', () => {
    const floats = new Float32Array([1, 2, 3, -4, 5.5, 6]);
    const binary = new Uint8Array(floats.buffer.slice(0));
    const document = glb({
      asset: { version: '2.0' },
      buffers: [{ byteLength: binary.length }],
      bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: binary.length }],
      accessors: [{ bufferView: 0, componentType: 5126, count: 2, type: 'VEC3' }],
    }, binary);

    const accessor = readHgAccessor(document, 0);
    expect(accessor.count).toBe(2);
    expect(accessor.components).toBe(3);
    expect(accessor.values).toEqual([1, 2, 3, -4, 5.5, 6]);
  });

  it('honours interleaved byteStride and accessor byteOffset', () => {
    const binary = new Uint8Array(32);
    const view = new DataView(binary.buffer);
    // Two 16-byte records: unused float, then XYZ.
    [10, 1, 2, 3, 20, 4, 5, 6].forEach((value, index) => {
      view.setFloat32(index * 4, value, true);
    });

    const document = glb({
      asset: { version: '2.0' },
      buffers: [{ byteLength: binary.length }],
      bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: binary.length, byteStride: 16 }],
      accessors: [{ bufferView: 0, byteOffset: 4, componentType: 5126, count: 2, type: 'VEC3' }],
    }, binary);

    expect(readHgAccessor(document, 0).values).toEqual([1, 2, 3, 4, 5, 6]);
  });

  it('normalises unsigned-byte colour/weight values', () => {
    const binary = new Uint8Array([0, 127, 255, 64]);
    const document = glb({
      asset: { version: '2.0' },
      buffers: [{ byteLength: 4 }],
      bufferViews: [{ buffer: 0, byteLength: 4 }],
      accessors: [{
        bufferView: 0,
        componentType: 5121,
        count: 1,
        type: 'VEC4',
        normalized: true,
      }],
    }, binary);

    const values = readHgAccessor(document, 0).values;
    expect(values[0]).toBe(0);
    expect(values[1]).toBeCloseTo(127 / 255, 12);
    expect(values[2]).toBe(1);
    expect(values[3]).toBeCloseTo(64 / 255, 12);
  });

  it('rejects sparse accessors rather than silently misreading them', () => {
    const binary = new Uint8Array(4);
    const document = glb({
      asset: { version: '2.0' },
      buffers: [{ byteLength: 4 }],
      bufferViews: [{ buffer: 0, byteLength: 4 }],
      accessors: [{
        bufferView: 0,
        componentType: 5126,
        count: 1,
        type: 'SCALAR',
        sparse: { count: 1 },
      }],
    }, binary);

    expect(() => readHgAccessor(document, 0)).toThrow(/Sparse/);
  });

  it('rejects an accessor that runs outside its declared bufferView', () => {
    const binary = new Uint8Array(8);
    const document = glb({
      asset: { version: '2.0' },
      buffers: [{ byteLength: 8 }],
      bufferViews: [{ buffer: 0, byteLength: 8 }],
      accessors: [{ bufferView: 0, componentType: 5126, count: 3, type: 'SCALAR' }],
    }, binary);

    expect(() => readHgAccessor(document, 0)).toThrow(/exceeds/i);
  });
});
