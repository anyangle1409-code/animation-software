import { encodeHgGlb } from './glbContainer';
import type { HgAccessorType, HgComponentType } from './gltfAccessors';

const COMPONENTS: Record<HgAccessorType, number> = {
  SCALAR: 1,
  VEC2: 2,
  VEC3: 3,
  VEC4: 4,
  MAT2: 4,
  MAT3: 9,
  MAT4: 16,
};

const COMPONENT_BYTES: Record<HgComponentType, number> = {
  5120: 1,
  5121: 1,
  5122: 2,
  5123: 2,
  5125: 4,
  5126: 4,
};

export interface HgWriteAccessorOptions {
  type: HgAccessorType;
  componentType: HgComponentType;
  normalized?: boolean;
  /** glTF ARRAY_BUFFER (34962) or ELEMENT_ARRAY_BUFFER (34963). */
  target?: 34962 | 34963;
  includeMinMax?: boolean;
}

export interface HgGltfJson {
  asset: { version: string; generator?: string };
  buffers: Array<{ byteLength: number }>;
  bufferViews: Array<Record<string, unknown>>;
  accessors: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

class HgBinaryBuilder {
  private readonly chunks: Array<{ offset: number; bytes: Uint8Array }> = [];
  private length = 0;

  append(bytes: Uint8Array, alignment = 4): { byteOffset: number; byteLength: number } {
    const mask = alignment - 1;
    if (alignment <= 0 || (alignment & mask) !== 0) {
      throw new Error('Binary alignment must be a positive power of two');
    }

    const offset = (this.length + mask) & ~mask;
    this.chunks.push({ offset, bytes: new Uint8Array(bytes) });
    this.length = offset + bytes.byteLength;
    return { byteOffset: offset, byteLength: bytes.byteLength };
  }

  finish(): Uint8Array {
    const out = new Uint8Array(this.length);
    for (const chunk of this.chunks) out.set(chunk.bytes, chunk.offset);
    return out;
  }
}

function rangeFor(type: HgComponentType): [number, number] | null {
  switch (type) {
    case 5120: return [-128, 127];
    case 5121: return [0, 255];
    case 5122: return [-32768, 32767];
    case 5123: return [0, 65535];
    case 5125: return [0, 4294967295];
    case 5126: return null;
  }
}

function encodeComponents(values: readonly number[], type: HgComponentType): Uint8Array {
  const bytes = COMPONENT_BYTES[type];
  const out = new Uint8Array(values.length * bytes);
  const view = new DataView(out.buffer);
  const range = rangeFor(type);

  values.forEach((value, index) => {
    if (!Number.isFinite(value)) throw new Error(`Accessor value ${index} is not finite`);
    if (range && (!Number.isInteger(value) || value < range[0] || value > range[1])) {
      throw new Error(
        `Accessor value ${value} is outside componentType ${type} range ${range[0]}..${range[1]}`,
      );
    }

    const offset = index * bytes;
    switch (type) {
      case 5120: view.setInt8(offset, value); break;
      case 5121: view.setUint8(offset, value); break;
      case 5122: view.setInt16(offset, value, true); break;
      case 5123: view.setUint16(offset, value, true); break;
      case 5125: view.setUint32(offset, value, true); break;
      case 5126: view.setFloat32(offset, value, true); break;
    }
  });

  return out;
}

function minMax(values: readonly number[], components: number) {
  const min = Array.from({ length: components }, () => Infinity);
  const max = Array.from({ length: components }, () => -Infinity);

  for (let index = 0; index < values.length; index += components) {
    for (let lane = 0; lane < components; lane += 1) {
      min[lane] = Math.min(min[lane], values[index + lane]);
      max[lane] = Math.max(max[lane], values[index + lane]);
    }
  }
  return { min, max };
}

/**
 * Minimal project-owned glTF/GLB document builder.
 *
 * It intentionally writes tightly packed accessors only. Add more layout
 * options only when the Home Gym PT production format actually needs them.
 */
export class HgGltfBuilder {
  readonly json: HgGltfJson = {
    asset: { version: '2.0', generator: 'Home Gym PT first-party codec' },
    buffers: [],
    bufferViews: [],
    accessors: [],
  };

  private readonly binary = new HgBinaryBuilder();

  addAccessor(
    values: readonly number[],
    options: HgWriteAccessorOptions,
  ): number {
    const components = COMPONENTS[options.type];
    if (values.length % components !== 0) {
      throw new Error(
        `${options.type} accessor has ${values.length} scalar values, not a multiple of ${components}`,
      );
    }

    const count = values.length / components;
    const encoded = encodeComponents(values, options.componentType);
    const written = this.binary.append(encoded, Math.max(4, COMPONENT_BYTES[options.componentType]));

    const bufferViewIndex = this.json.bufferViews.length;
    this.json.bufferViews.push({
      buffer: 0,
      byteOffset: written.byteOffset,
      byteLength: written.byteLength,
      ...(options.target ? { target: options.target } : {}),
    });

    const accessor: Record<string, unknown> = {
      bufferView: bufferViewIndex,
      byteOffset: 0,
      componentType: options.componentType,
      count,
      type: options.type,
      ...(options.normalized ? { normalized: true } : {}),
    };

    if (options.includeMinMax && count > 0 && !options.normalized) {
      const bounds = minMax(values, components);
      accessor.min = bounds.min;
      accessor.max = bounds.max;
    }

    const index = this.json.accessors.length;
    this.json.accessors.push(accessor);
    return index;
  }

  binaryBytes(): Uint8Array {
    return this.binary.finish();
  }

  toGlb(): Uint8Array {
    const binary = this.binary.finish();
    this.json.buffers = [{ byteLength: binary.byteLength }];
    return encodeHgGlb(this.json, binary.byteLength ? [binary] : []);
  }
}
