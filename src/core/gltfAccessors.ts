import type { HgGlbDocument } from './glbContainer';

export type HgAccessorType =
  | 'SCALAR'
  | 'VEC2'
  | 'VEC3'
  | 'VEC4'
  | 'MAT2'
  | 'MAT3'
  | 'MAT4';

export type HgComponentType = 5120 | 5121 | 5122 | 5123 | 5125 | 5126;

export interface HgAccessorData {
  index: number;
  count: number;
  components: number;
  componentType: HgComponentType;
  normalized: boolean;
  values: number[];
}

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

function objectAt(value: unknown, index: number, label: string): Record<string, unknown> {
  if (!Array.isArray(value) || index < 0 || index >= value.length) {
    throw new Error(`${label}[${index}] is missing`);
  }
  const item = value[index];
  if (!item || typeof item !== 'object' || Array.isArray(item)) {
    throw new Error(`${label}[${index}] is not an object`);
  }
  return item as Record<string, unknown>;
}

function integer(value: unknown, label: string): number {
  if (!Number.isInteger(value) || (value as number) < 0) {
    throw new Error(`${label} must be a non-negative integer`);
  }
  return value as number;
}

function componentType(value: unknown): HgComponentType {
  if (
    value === 5120 ||
    value === 5121 ||
    value === 5122 ||
    value === 5123 ||
    value === 5125 ||
    value === 5126
  ) {
    return value;
  }
  throw new Error(`Unsupported glTF componentType ${String(value)}`);
}

function accessorType(value: unknown): HgAccessorType {
  if (
    value === 'SCALAR' ||
    value === 'VEC2' ||
    value === 'VEC3' ||
    value === 'VEC4' ||
    value === 'MAT2' ||
    value === 'MAT3' ||
    value === 'MAT4'
  ) {
    return value;
  }
  throw new Error(`Unsupported glTF accessor type ${String(value)}`);
}

function readComponent(view: DataView, offset: number, type: HgComponentType): number {
  switch (type) {
    case 5120: return view.getInt8(offset);
    case 5121: return view.getUint8(offset);
    case 5122: return view.getInt16(offset, true);
    case 5123: return view.getUint16(offset, true);
    case 5125: return view.getUint32(offset, true);
    case 5126: return view.getFloat32(offset, true);
  }
}

function normalise(value: number, type: HgComponentType): number {
  switch (type) {
    case 5120: return Math.max(value / 127, -1);
    case 5121: return value / 255;
    case 5122: return Math.max(value / 32767, -1);
    case 5123: return value / 65535;
    case 5125: return value / 4294967295;
    case 5126: return value;
  }
}

/**
 * Read one accessor from the first-party GLB document.
 *
 * Supported intentionally:
 * - one in-file BIN buffer per glTF buffer index;
 * - byte offsets and byteStride;
 * - scalar/vector/matrix accessors;
 * - integer normalisation.
 *
 * Sparse accessors and external/data-URI buffers are rejected until Home Gym PT
 * has an actual production requirement for them.
 */
export function readHgAccessor(document: HgGlbDocument, index: number): HgAccessorData {
  const accessor = objectAt(document.json.accessors, index, 'accessors');
  if ('sparse' in accessor) throw new Error('Sparse glTF accessors are not supported');

  const viewIndex = integer(accessor.bufferView, `accessors[${index}].bufferView`);
  const bufferView = objectAt(document.json.bufferViews, viewIndex, 'bufferViews');
  const bufferIndex = bufferView.buffer === undefined ? 0 : integer(bufferView.buffer, 'bufferView.buffer');
  const binary = document.binaryChunks[bufferIndex];
  if (!binary) {
    throw new Error(`GLB binary buffer ${bufferIndex} is unavailable`);
  }

  const type = accessorType(accessor.type);
  const components = COMPONENTS[type];
  const component = componentType(accessor.componentType);
  const bytesPerComponent = COMPONENT_BYTES[component];
  const elementBytes = components * bytesPerComponent;
  const stride =
    bufferView.byteStride === undefined
      ? elementBytes
      : integer(bufferView.byteStride, 'bufferView.byteStride');

  if (stride < elementBytes) {
    throw new Error(`bufferView.byteStride ${stride} is smaller than accessor element size ${elementBytes}`);
  }

  const count = integer(accessor.count, `accessors[${index}].count`);
  const viewOffset = bufferView.byteOffset === undefined ? 0 : integer(bufferView.byteOffset, 'bufferView.byteOffset');
  const accessorOffset = accessor.byteOffset === undefined ? 0 : integer(accessor.byteOffset, 'accessor.byteOffset');
  const byteLength = integer(bufferView.byteLength, 'bufferView.byteLength');
  const start = viewOffset + accessorOffset;

  const viewEnd = viewOffset + byteLength;
  const requiredEnd =
    count === 0 ? start : start + (count - 1) * stride + elementBytes;

  if (viewEnd > binary.byteLength) {
    throw new Error('bufferView exceeds binary buffer');
  }
  if (start < viewOffset || requiredEnd > viewEnd) {
    throw new Error('Accessor exceeds its bufferView');
  }

  const normalized = accessor.normalized === true;
  const data = new DataView(binary.buffer, binary.byteOffset, binary.byteLength);
  const values: number[] = [];

  for (let element = 0; element < count; element += 1) {
    const elementOffset = start + element * stride;
    for (let lane = 0; lane < components; lane += 1) {
      const raw = readComponent(data, elementOffset + lane * bytesPerComponent, component);
      values.push(normalized ? normalise(raw, component) : raw);
    }
  }

  return {
    index,
    count,
    components,
    componentType: component,
    normalized,
    values,
  };
}
