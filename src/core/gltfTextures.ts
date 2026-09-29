import type { HgGlbDocument } from './glbContainer';

type JsonObject = Record<string, unknown>;

export type HgImageMimeType = 'image/png' | 'image/jpeg';

export interface HgGltfImage {
  readonly index: number;
  readonly name: string;
  readonly mimeType: HgImageMimeType;
  readonly bytes: Uint8Array;
}

export interface HgGltfSampler {
  readonly index: number;
  readonly name: string;
  readonly magFilter: 9728 | 9729 | null;
  readonly minFilter: 9728 | 9729 | 9984 | 9985 | 9986 | 9987 | null;
  readonly wrapS: 33071 | 33648 | 10497;
  readonly wrapT: 33071 | 33648 | 10497;
}

export interface HgGltfTexture {
  readonly index: number;
  readonly name: string;
  readonly source: number;
  readonly sampler: number | null;
}

export interface HgGltfTextureDocument {
  readonly images: HgGltfImage[];
  readonly samplers: HgGltfSampler[];
  readonly textures: HgGltfTexture[];
}

function object(value: unknown, label: string): JsonObject {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be an object`);
  }
  return value as JsonObject;
}

function objectArray(value: unknown, label: string): JsonObject[] {
  if (value === undefined) return [];
  if (!Array.isArray(value)) throw new Error(`${label} must be an array`);
  return value.map((entry, index) => object(entry, `${label}[${index}]`));
}

function integer(value: unknown, label: string): number {
  if (!Number.isInteger(value) || (value as number) < 0) {
    throw new Error(`${label} must be a non-negative integer`);
  }
  return value as number;
}

function nameOf(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function enumValue<T extends number>(
  value: unknown,
  allowed: readonly T[],
  fallback: T | null,
  label: string,
): T | null {
  if (value === undefined) return fallback;
  if (typeof value !== 'number' || !allowed.includes(value as T)) {
    throw new Error(`${label} has unsupported value ${String(value)}`);
  }
  return value as T;
}

function imageMimeType(value: unknown, label: string): HgImageMimeType {
  if (value === 'image/png' || value === 'image/jpeg') return value;
  throw new Error(`${label} must be image/png or image/jpeg`);
}

function bufferViewBytes(
  document: HgGlbDocument,
  viewIndex: number,
  label: string,
): Uint8Array {
  const views = objectArray(document.json.bufferViews, 'bufferViews');
  const view = views[viewIndex];
  if (!view) throw new Error(`${label} references missing bufferView ${viewIndex}`);

  const buffer = view.buffer === undefined ? 0 : integer(view.buffer, `${label}.buffer`);
  const bytes = document.binaryChunks[buffer];
  if (!bytes) throw new Error(`${label} references unavailable GLB buffer ${buffer}`);

  const offset = view.byteOffset === undefined ? 0 : integer(view.byteOffset, `${label}.byteOffset`);
  const length = integer(view.byteLength, `${label}.byteLength`);
  if (offset + length > bytes.byteLength) {
    throw new Error(`${label} exceeds its GLB buffer`);
  }
  return new Uint8Array(bytes.subarray(offset, offset + length));
}

function readImage(document: HgGlbDocument, value: JsonObject, index: number): HgGltfImage {
  const label = `images[${index}]`;
  if (value.extensions !== undefined) throw new Error(`${label} extensions are not supported`);
  if (value.uri !== undefined) {
    throw new Error(`${label} URI images are not supported in the standalone GLB path`);
  }
  const bufferView = integer(value.bufferView, `${label}.bufferView`);
  return {
    index,
    name: nameOf(value.name),
    mimeType: imageMimeType(value.mimeType, `${label}.mimeType`),
    bytes: bufferViewBytes(document, bufferView, `${label}.bufferView`),
  };
}

function readSampler(value: JsonObject, index: number): HgGltfSampler {
  const label = `samplers[${index}]`;
  if (value.extensions !== undefined) throw new Error(`${label} extensions are not supported`);
  return {
    index,
    name: nameOf(value.name),
    magFilter: enumValue(value.magFilter, [9728, 9729] as const, null, `${label}.magFilter`),
    minFilter: enumValue(
      value.minFilter,
      [9728, 9729, 9984, 9985, 9986, 9987] as const,
      null,
      `${label}.minFilter`,
    ),
    wrapS: enumValue(value.wrapS, [33071, 33648, 10497] as const, 10497, `${label}.wrapS`)!,
    wrapT: enumValue(value.wrapT, [33071, 33648, 10497] as const, 10497, `${label}.wrapT`)!,
  };
}

function readTexture(value: JsonObject, index: number): HgGltfTexture {
  const label = `textures[${index}]`;
  if (value.extensions !== undefined) throw new Error(`${label} extensions are not supported`);
  return {
    index,
    name: nameOf(value.name),
    source: integer(value.source, `${label}.source`),
    sampler: value.sampler === undefined ? null : integer(value.sampler, `${label}.sampler`),
  };
}

/**
 * Decode embedded GLB image bytes and core glTF texture/sampler metadata.
 *
 * Image decompression is intentionally left to the browser's native image
 * decoder at the renderer boundary. This module only owns deterministic GLB
 * extraction and glTF validation, so no third-party image library is required.
 */
export function readHgGltfTextures(document: HgGlbDocument): HgGltfTextureDocument {
  const images = objectArray(document.json.images, 'images').map(
    (value, index) => readImage(document, value, index),
  );
  const samplers = objectArray(document.json.samplers, 'samplers').map(readSampler);
  const textures = objectArray(document.json.textures, 'textures').map(readTexture);

  for (const texture of textures) {
    if (texture.source >= images.length) {
      throw new Error(`textures[${texture.index}] references missing image ${texture.source}`);
    }
    if (texture.sampler !== null && texture.sampler >= samplers.length) {
      throw new Error(`textures[${texture.index}] references missing sampler ${texture.sampler}`);
    }
  }

  return { images, samplers, textures };
}
