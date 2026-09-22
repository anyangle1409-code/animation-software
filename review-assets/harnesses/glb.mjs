// Minimal GLB reader/writer that edits accessor data in place.
//
// The point of doing it at this level rather than through three.js is that
// everything we do not touch stays byte-for-byte identical: positions,
// normals, UVs, colours, indices, the skin, the inverse binds, the node
// hierarchy and the morph targets.
import { readFileSync, writeFileSync } from 'node:fs';

const COMPONENT = {
  5120: { array: Int8Array, size: 1 },
  5121: { array: Uint8Array, size: 1 },
  5122: { array: Int16Array, size: 2 },
  5123: { array: Uint16Array, size: 2 },
  5125: { array: Uint32Array, size: 4 },
  5126: { array: Float32Array, size: 4 },
};

const COUNT = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };

export function readGlb(path) {
  const buffer = readFileSync(path);
  const view = new DataView(buffer.buffer, buffer.byteOffset, buffer.byteLength);
  if (view.getUint32(0, true) !== 0x46546c67) throw new Error('not a GLB');
  const jsonLength = view.getUint32(12, true);
  const json = JSON.parse(
    new TextDecoder().decode(new Uint8Array(buffer.buffer, buffer.byteOffset + 20, jsonLength)),
  );
  const binHeader = 20 + jsonLength;
  const binLength = view.getUint32(binHeader, true);
  const bin = Buffer.from(
    buffer.buffer.slice(
      buffer.byteOffset + binHeader + 8,
      buffer.byteOffset + binHeader + 8 + binLength,
    ),
  );
  return { json, bin };
}

/** A typed view straight onto the BIN chunk, so writes to it are writes to the file. */
export function accessorView(glb, index) {
  const accessor = glb.json.accessors[index];
  const component = COMPONENT[accessor.componentType];
  const items = COUNT[accessor.type];
  const bufferView = glb.json.bufferViews[accessor.bufferView];
  const offset = (bufferView.byteOffset ?? 0) + (accessor.byteOffset ?? 0);
  const stride = bufferView.byteStride ?? component.size * items;
  if (stride !== component.size * items) throw new Error(`interleaved accessor ${index}`);
  return {
    accessor,
    items,
    count: accessor.count,
    data: new component.array(glb.bin.buffer, glb.bin.byteOffset + offset, accessor.count * items),
    normalized: accessor.normalized === true,
    componentType: accessor.componentType,
  };
}

export function writeGlb(glb, path) {
  const jsonText = JSON.stringify(glb.json);
  const jsonBytes = Buffer.from(jsonText, 'utf8');
  const jsonPad = (4 - (jsonBytes.length % 4)) % 4;
  const binPad = (4 - (glb.bin.length % 4)) % 4;
  const jsonChunk = Buffer.concat([jsonBytes, Buffer.alloc(jsonPad, 0x20)]);
  const binChunk = Buffer.concat([glb.bin, Buffer.alloc(binPad, 0)]);
  const total = 12 + 8 + jsonChunk.length + 8 + binChunk.length;
  const out = Buffer.alloc(total);
  out.writeUInt32LE(0x46546c67, 0);
  out.writeUInt32LE(2, 4);
  out.writeUInt32LE(total, 8);
  out.writeUInt32LE(jsonChunk.length, 12);
  out.writeUInt32LE(0x4e4f534a, 16);
  jsonChunk.copy(out, 20);
  const binHeader = 20 + jsonChunk.length;
  out.writeUInt32LE(binChunk.length, binHeader);
  out.writeUInt32LE(0x004e4942, binHeader + 4);
  binChunk.copy(out, binHeader + 8);
  writeFileSync(path, out);
  return total;
}

/**
 * Per-vertex skin influences, gathered across however many JOINTS_n/WEIGHTS_n
 * sets the file uses. The source convention (how many sets, their component
 * types) is reported so a repair can put the data back the same way.
 */
export function readSkin(glb, primitive) {
  const sets = [];
  for (let n = 0; primitive.attributes[`JOINTS_${n}`] !== undefined; n += 1) {
    sets.push({
      joints: accessorView(glb, primitive.attributes[`JOINTS_${n}`]),
      weights: accessorView(glb, primitive.attributes[`WEIGHTS_${n}`]),
    });
  }
  const count = sets[0].joints.count;
  const slots = sets.length * 4;
  const joints = new Uint16Array(count * slots);
  const weights = new Float32Array(count * slots);
  sets.forEach((set, n) => {
    for (let vertex = 0; vertex < count; vertex += 1) {
      for (let lane = 0; lane < 4; lane += 1) {
        joints[vertex * slots + n * 4 + lane] = set.joints.data[vertex * 4 + lane];
        weights[vertex * slots + n * 4 + lane] = set.weights.data[vertex * 4 + lane];
      }
    }
  });
  return { sets, count, slots, joints, weights };
}

/** Put edited influences back into the same accessors, same layout. */
export function writeSkin(glb, skin) {
  const { sets, count, slots, joints, weights } = skin;
  sets.forEach((set, n) => {
    if (set.weights.componentType !== 5126) throw new Error('non-float weights');
    for (let vertex = 0; vertex < count; vertex += 1) {
      for (let lane = 0; lane < 4; lane += 1) {
        set.joints.data[vertex * 4 + lane] = joints[vertex * slots + n * 4 + lane];
        set.weights.data[vertex * 4 + lane] = weights[vertex * slots + n * 4 + lane];
      }
    }
  });
}
