/**
 * Home Gym PT first-party GLB 2.0 container codec.
 *
 * This handles only the GLB container itself: header, JSON chunk and binary
 * chunks. Higher-level glTF mesh/skin/animation decoding is layered above it.
 * No third-party imports.
 */

const GLB_MAGIC = 0x46546c67;
const GLB_VERSION = 2;
const CHUNK_JSON = 0x4e4f534a;
const CHUNK_BIN = 0x004e4942;

export interface HgGlbDocument {
  json: Record<string, unknown>;
  binaryChunks: Uint8Array[];
}

const paddedLength = (length: number): number => (length + 3) & ~3;

export function parseHgGlb(input: ArrayBuffer | Uint8Array): HgGlbDocument {
  const bytes = input instanceof Uint8Array ? input : new Uint8Array(input);
  if (bytes.byteLength < 20) throw new Error('GLB is too short');

  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (view.getUint32(0, true) !== GLB_MAGIC) throw new Error('Invalid GLB magic');
  if (view.getUint32(4, true) !== GLB_VERSION) throw new Error('Only GLB version 2 is supported');

  const declaredLength = view.getUint32(8, true);
  if (declaredLength !== bytes.byteLength) {
    throw new Error(`GLB length mismatch: header ${declaredLength}, bytes ${bytes.byteLength}`);
  }

  let offset = 12;
  let json: Record<string, unknown> | null = null;
  const binaryChunks: Uint8Array[] = [];

  while (offset < bytes.byteLength) {
    if (offset + 8 > bytes.byteLength) throw new Error('Truncated GLB chunk header');
    const chunkLength = view.getUint32(offset, true);
    const chunkType = view.getUint32(offset + 4, true);
    offset += 8;

    if (chunkLength % 4 !== 0) throw new Error('GLB chunk length is not 4-byte aligned');
    if (offset + chunkLength > bytes.byteLength) throw new Error('GLB chunk exceeds file length');

    const chunk = bytes.subarray(offset, offset + chunkLength);
    offset += chunkLength;

    if (chunkType === CHUNK_JSON) {
      if (json) throw new Error('GLB contains more than one JSON chunk');
      const decoded = new TextDecoder().decode(chunk).replace(/[\u0000\u0020]+$/g, '');
      const parsed = JSON.parse(decoded);
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        throw new Error('GLB JSON root must be an object');
      }
      json = parsed as Record<string, unknown>;
    } else if (chunkType === CHUNK_BIN) {
      // Copy the slice so the parsed document is independent of the source buffer.
      binaryChunks.push(new Uint8Array(chunk));
    }
  }

  if (!json) throw new Error('GLB has no JSON chunk');
  return { json, binaryChunks };
}

export function encodeHgGlb(
  json: Record<string, unknown>,
  binaryChunks: readonly Uint8Array[] = [],
): Uint8Array {
  const encoder = new TextEncoder();
  const rawJson = encoder.encode(JSON.stringify(json));
  const jsonLength = paddedLength(rawJson.byteLength);

  const chunks: Array<{ type: number; bytes: Uint8Array; pad: number }> = [
    { type: CHUNK_JSON, bytes: rawJson, pad: 0x20 },
    ...binaryChunks.map((bytes) => ({ type: CHUNK_BIN, bytes, pad: 0x00 })),
  ];

  let total = 12;
  for (const chunk of chunks) total += 8 + paddedLength(chunk.bytes.byteLength);

  const out = new Uint8Array(total);
  const view = new DataView(out.buffer);
  view.setUint32(0, GLB_MAGIC, true);
  view.setUint32(4, GLB_VERSION, true);
  view.setUint32(8, total, true);

  let offset = 12;
  for (const chunk of chunks) {
    const length = paddedLength(chunk.bytes.byteLength);
    view.setUint32(offset, length, true);
    view.setUint32(offset + 4, chunk.type, true);
    offset += 8;

    out.set(chunk.bytes, offset);
    if (length > chunk.bytes.byteLength) {
      out.fill(chunk.pad, offset + chunk.bytes.byteLength, offset + length);
    }
    offset += length;
  }

  // The first chunk must be JSON under GLB 2.0. Keeping this explicit makes a
  // future refactor fail locally instead of producing a subtly invalid file.
  if (jsonLength !== view.getUint32(12, true)) {
    throw new Error('Internal GLB JSON padding mismatch');
  }

  return out;
}

export const HG_GLB_CONSTANTS = {
  magic: GLB_MAGIC,
  version: GLB_VERSION,
  jsonChunk: CHUNK_JSON,
  binaryChunk: CHUNK_BIN,
} as const;
