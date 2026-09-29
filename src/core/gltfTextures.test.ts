import { describe, expect, it } from 'vitest';
import { encodeHgGlb, parseHgGlb } from './glbContainer';
import { readHgGltfTextures } from './gltfTextures';

function documentWithTexture() {
  const image = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  const json = {
    asset: { version: '2.0' },
    buffers: [{ byteLength: image.byteLength }],
    bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: image.byteLength }],
    images: [{ name: 'skin', bufferView: 0, mimeType: 'image/png' }],
    samplers: [{
      name: 'skin_sampler',
      magFilter: 9729,
      minFilter: 9987,
      wrapS: 10497,
      wrapT: 33071,
    }],
    textures: [{ name: 'skin_texture', source: 0, sampler: 0 }],
  };
  return parseHgGlb(encodeHgGlb(json, [image]));
}

describe('first-party glTF texture decoder', () => {
  it('extracts embedded image bytes and sampler metadata', () => {
    const decoded = readHgGltfTextures(documentWithTexture());
    expect(decoded.images).toHaveLength(1);
    expect(decoded.images[0].name).toBe('skin');
    expect(decoded.images[0].mimeType).toBe('image/png');
    expect([...decoded.images[0].bytes]).toEqual([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

    expect(decoded.samplers[0]).toEqual({
      index: 0,
      name: 'skin_sampler',
      magFilter: 9729,
      minFilter: 9987,
      wrapS: 10497,
      wrapT: 33071,
    });
    expect(decoded.textures[0]).toEqual({
      index: 0,
      name: 'skin_texture',
      source: 0,
      sampler: 0,
    });
  });

  it('uses glTF repeat wrapping defaults when a sampler omits wrapping', () => {
    const bytes = new Uint8Array([1, 2, 3, 4]);
    const document = parseHgGlb(encodeHgGlb({
      asset: { version: '2.0' },
      buffers: [{ byteLength: 4 }],
      bufferViews: [{ buffer: 0, byteLength: 4 }],
      images: [{ bufferView: 0, mimeType: 'image/jpeg' }],
      samplers: [{}],
      textures: [{ source: 0, sampler: 0 }],
    }, [bytes]));
    const sampler = readHgGltfTextures(document).samplers[0];
    expect(sampler.wrapS).toBe(10497);
    expect(sampler.wrapT).toBe(10497);
    expect(sampler.magFilter).toBeNull();
    expect(sampler.minFilter).toBeNull();
  });

  it('rejects external image URIs in the standalone GLB path', () => {
    const document = {
      json: {
        asset: { version: '2.0' },
        images: [{ uri: 'skin.png', mimeType: 'image/png' }],
      },
      binaryChunks: [],
    };
    expect(() => readHgGltfTextures(document)).toThrow(/URI images/);
  });

  it('rejects texture references to a missing image', () => {
    const document = {
      json: {
        asset: { version: '2.0' },
        textures: [{ source: 2 }],
      },
      binaryChunks: [],
    };
    expect(() => readHgGltfTextures(document)).toThrow(/missing image/);
  });

  it('rejects unsupported sampler enums', () => {
    const bytes = new Uint8Array([1, 2, 3, 4]);
    const document = parseHgGlb(encodeHgGlb({
      asset: { version: '2.0' },
      buffers: [{ byteLength: 4 }],
      bufferViews: [{ buffer: 0, byteLength: 4 }],
      images: [{ bufferView: 0, mimeType: 'image/png' }],
      samplers: [{ wrapS: 12345 }],
      textures: [{ source: 0, sampler: 0 }],
    }, [bytes]));
    expect(() => readHgGltfTextures(document)).toThrow(/wrapS/);
  });
});
