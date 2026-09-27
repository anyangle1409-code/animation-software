import { describe, expect, it } from 'vitest';
import { encodeHgGlb, HG_GLB_CONSTANTS, parseHgGlb } from './glbContainer';

describe('first-party GLB container', () => {
  it('round-trips JSON and binary chunks', () => {
    const json = {
      asset: { version: '2.0', generator: 'Home Gym PT' },
      scenes: [{ nodes: [0] }],
      scene: 0,
    };
    const binary = new Uint8Array([1, 2, 3, 4, 5]);
    const encoded = encodeHgGlb(json, [binary]);
    const parsed = parseHgGlb(encoded);

    expect(parsed.json).toEqual(json);
    expect(Array.from(parsed.binaryChunks[0].slice(0, binary.length))).toEqual(Array.from(binary));
    // GLB BIN chunks are padded to four bytes.
    expect(parsed.binaryChunks[0].length % 4).toBe(0);
  });

  it('writes the GLB 2.0 magic/version/declared length', () => {
    const encoded = encodeHgGlb({ asset: { version: '2.0' } });
    const view = new DataView(encoded.buffer, encoded.byteOffset, encoded.byteLength);
    expect(view.getUint32(0, true)).toBe(HG_GLB_CONSTANTS.magic);
    expect(view.getUint32(4, true)).toBe(2);
    expect(view.getUint32(8, true)).toBe(encoded.byteLength);
  });

  it('pads JSON with spaces, never null bytes', () => {
    const encoded = encodeHgGlb({ asset: { version: '2.0' }, x: 'a' });
    const view = new DataView(encoded.buffer, encoded.byteOffset, encoded.byteLength);
    const jsonLength = view.getUint32(12, true);
    const jsonStart = 20;
    const chunk = encoded.subarray(jsonStart, jsonStart + jsonLength);
    const last = chunk[chunk.length - 1];
    expect([0x20, 0x7d]).toContain(last);
    expect(chunk).not.toContain(0);
  });

  it('rejects invalid headers rather than guessing', () => {
    const encoded = encodeHgGlb({ asset: { version: '2.0' } });
    const broken = encoded.slice();
    broken[0] = 0;
    expect(() => parseHgGlb(broken)).toThrow(/magic/i);
  });

  it('rejects a header length that disagrees with the byte stream', () => {
    const encoded = encodeHgGlb({ asset: { version: '2.0' } });
    const broken = encoded.slice();
    new DataView(broken.buffer).setUint32(8, broken.byteLength + 4, true);
    expect(() => parseHgGlb(broken)).toThrow(/length mismatch/i);
  });
});
