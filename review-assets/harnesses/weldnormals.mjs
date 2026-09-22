// Narrow, normals-only repair of the v8 shading seams.
//
// Both v7 and v8 store per-vertex normals computed WITHOUT welding co-located
// duplicates — that is the asset's own convention. On a smooth surface the two
// sides of a UV seam then agree and the seam is invisible, which is how v7
// reads. The Stage 1/2 arm work moved each side's neighbours differently, so in
// v8 the two sides disagree by up to 138 degrees and the seam shades as a hard
// blocky facet.
//
// This welds the normal at exactly those seams: every member of a disagreeing
// co-located group gets the normalised mean of that group's stored normals.
// It writes NOTHING else — no positions, no topology, no weights, no joint
// matrices, no inverse binds, no extras. Groups that were already seams in the
// reference body are left alone, so intentional hard edges survive.
import { readGlb, accessorView, writeGlb } from './glb.mjs';

const SRC = process.argv[2];
const REF = process.argv[3];
const OUT = process.argv[4];
const LIMIT = Number(process.env.SEAM_DEGREES ?? 5);

const read = (path) => {
  const glb = readGlb(path);
  const prim = glb.json.meshes[0].primitives[0];
  return { glb, prim,
    pos: accessorView(glb, prim.attributes.POSITION),
    nor: accessorView(glb, prim.attributes.NORMAL) };
};

const groupsOf = (m) => {
  const groups = new Map();
  for (let v = 0; v < m.pos.count; v += 1) {
    const key = `${m.pos.data[v * 3]},${m.pos.data[v * 3 + 1]},${m.pos.data[v * 3 + 2]}`;
    const list = groups.get(key);
    if (list) list.push(v); else groups.set(key, [v]);
  }
  return groups;
};

const spread = (m, list) => {
  let worst = 0;
  for (let a = 0; a < list.length; a += 1) {
    for (let b = a + 1; b < list.length; b += 1) {
      const ia = list[a], ib = list[b];
      const d = m.nor.data[ia * 3] * m.nor.data[ib * 3]
        + m.nor.data[ia * 3 + 1] * m.nor.data[ib * 3 + 1]
        + m.nor.data[ia * 3 + 2] * m.nor.data[ib * 3 + 2];
      worst = Math.max(worst, Math.acos(Math.max(-1, Math.min(1, d))) * 180 / Math.PI);
    }
  }
  return worst;
};

const src = read(SRC);
const ref = read(REF);

// Intentional hard edges: the reference body's own disagreeing groups, keyed by
// vertex indices so they survive the positional change between the two bodies.
const keep = new Set();
for (const [, list] of groupsOf(ref)) {
  if (list.length > 1 && spread(ref, list) > LIMIT) keep.add(list.slice().sort((a, b) => a - b).join(','));
}

let welded = 0;
let vertices = 0;
let worstBefore = 0;
let worstShift = 0;
let preserved = 0;
for (const [, list] of groupsOf(src)) {
  if (list.length < 2) continue;
  const before = spread(src, list);
  if (before <= LIMIT) continue;
  if (keep.has(list.slice().sort((a, b) => a - b).join(','))) { preserved += 1; continue; }
  worstBefore = Math.max(worstBefore, before);
  let x = 0, y = 0, z = 0;
  for (const v of list) { x += src.nor.data[v * 3]; y += src.nor.data[v * 3 + 1]; z += src.nor.data[v * 3 + 2]; }
  const l = Math.hypot(x, y, z);
  // A group whose normals cancel has no meaningful mean; leave it rather than
  // write a degenerate normal.
  if (l < 1e-6) continue;
  x /= l; y /= l; z /= l;
  for (const v of list) {
    const d = src.nor.data[v * 3] * x + src.nor.data[v * 3 + 1] * y + src.nor.data[v * 3 + 2] * z;
    worstShift = Math.max(worstShift, Math.acos(Math.max(-1, Math.min(1, d))) * 180 / Math.PI);
    src.nor.data[v * 3] = x; src.nor.data[v * 3 + 1] = y; src.nor.data[v * 3 + 2] = z;
    vertices += 1;
  }
  welded += 1;
}

console.log(`welded ${welded} seam groups (${vertices} vertices)`);
console.log(`  worst disagreement before: ${worstBefore.toFixed(1)}deg`);
console.log(`  largest normal shift applied: ${worstShift.toFixed(1)}deg`);
console.log(`  reference hard edges preserved: ${preserved}`);
writeGlb(src.glb, OUT);
console.log(`wrote ${OUT}`);
