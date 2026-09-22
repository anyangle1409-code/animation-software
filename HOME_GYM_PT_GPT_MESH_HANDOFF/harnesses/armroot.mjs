// True-fix candidate: move the imported glenohumeral joint posteriorly so the
// deltoid cap sits over the humerus and the arm hangs from underneath it.
//
// The rig is flat — DEF-upper_arm.L/R are direct children of the armature root
// with the rest of each arm nested beneath them — so editing those two nodes'
// matrices moves each whole arm chain, while DEF-shoulder.L/R (clavicle and
// trapezius) stay where they are and the skin weights blend between them. That
// is what a rigger's shoulder retraction does.
//
// Inverse bind matrices are deliberately left alone. Skinning is
// jointWorld * IBM, so moving the joint while the IBM stays fixed translates
// the arm's skinned vertices by the same amount, and `readCharacter` derives
// its rest pose from the node hierarchy, so the rest pose moves consistently.
// Nothing else in the file is touched: positions, normals, UVs, colours,
// indices, weights, joints and scene.extras stay byte-identical.
import { readGlb, writeGlb } from './glb.mjs';

const SRC = process.argv[2];
const OUT = process.argv[3];
const SHIFT = Number(process.env.SHIFT ?? 0.03); // metres
// Direction of the correction in REST world space. The retarget expresses the
// arm root as an offset in the clavicle's rest frame and then applies it in the
// clavicle's posed frame, and those differ by a large rotation, so a rest-space
// -z shift does not come out as a posed-space -z shift. DIR lets the required
// rest-space direction be solved for rather than assumed.
const DIR = (process.env.DIR ?? '0,0,-1').split(',').map(Number);
const dlen = Math.hypot(...DIR) || 1;

const glb = readGlb(SRC);
const nodes = glb.json.nodes;
const parentOf = new Map();
nodes.forEach((n, i) => (n.children ?? []).forEach((c) => parentOf.set(c, i)));

const localOf = (i) => {
  const n = nodes[i];
  if (n.matrix) return n.matrix.slice();
  // Every joint in these assets uses `matrix`; TRS would silently read as
  // identity here, so refuse rather than guess.
  if (n.translation || n.rotation || n.scale) throw new Error(`node ${n.name} uses TRS`);
  return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
};
const mul = (a, b) => {
  const o = new Array(16).fill(0);
  for (let c = 0; c < 4; c += 1) for (let r = 0; r < 4; r += 1) {
    let s = 0;
    for (let k = 0; k < 4; k += 1) s += a[k * 4 + r] * b[c * 4 + k];
    o[c * 4 + r] = s;
  }
  return o;
};
const worldOf = (i) => {
  const chain = [];
  let p = i;
  while (p !== undefined) { chain.unshift(p); p = parentOf.get(p); }
  return chain.reduce((acc, n) => mul(acc, localOf(n)), [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]);
};
/** Inverse of a matrix's upper-left 3x3, general (the rig root may scale). */
const invBasis = (m) => {
  const a = [m[0], m[1], m[2], m[4], m[5], m[6], m[8], m[9], m[10]];
  const [a0, a1, a2, a3, a4, a5, a6, a7, a8] = a;
  const det = a0 * (a4 * a8 - a5 * a7) - a3 * (a1 * a8 - a2 * a7) + a6 * (a1 * a5 - a2 * a4);
  if (Math.abs(det) < 1e-12) throw new Error('degenerate parent basis');
  return [
    (a4 * a8 - a5 * a7) / det, -(a1 * a8 - a2 * a7) / det, (a1 * a5 - a2 * a4) / det,
    -(a3 * a8 - a5 * a6) / det, (a0 * a8 - a2 * a6) / det, -(a0 * a5 - a2 * a3) / det,
    (a3 * a7 - a4 * a6) / det, -(a0 * a7 - a1 * a6) / det, (a0 * a4 - a1 * a3) / det,
  ];
};

const byName = new Map(nodes.map((n, i) => [n.name, i]));
const report = [];
for (const side of ['L', 'R']) {
  const name = `DEF-upper_arm.${side}`;
  const index = byName.get(name);
  if (index === undefined) throw new Error(`${name} not found`);
  const before = worldOf(index);
  const parent = parentOf.get(index);
  const parentWorld = parent === undefined
    ? [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
    : worldOf(parent);
  // A pure world-space translation becomes a local translation through the
  // parent's inverse basis; the node's own rotation is untouched, so the arm
  // keeps its orientation and only its root moves.
  const inv = invBasis(parentWorld);
  const d = DIR.map((c) => (c / dlen) * SHIFT);
  const local = [
    inv[0] * d[0] + inv[3] * d[1] + inv[6] * d[2],
    inv[1] * d[0] + inv[4] * d[1] + inv[7] * d[2],
    inv[2] * d[0] + inv[5] * d[1] + inv[8] * d[2],
  ];
  const m = nodes[index].matrix.slice();
  m[12] += local[0]; m[13] += local[1]; m[14] += local[2];
  nodes[index].matrix = m;
  const after = worldOf(index);
  report.push(`${name}: world z ${(before[14] * 1000).toFixed(2)} -> ${(after[14] * 1000).toFixed(2)} mm`
    + `  (moved ${(Math.hypot(after[12] - before[12], after[13] - before[13], after[14] - before[14]) * 1000).toFixed(2)} mm,`
    + ` local delta ${local.map((v) => (v * 1000).toFixed(2)).join('/')})`);
}

for (const line of report) console.log('  ' + line);
console.log(`  posterior shift ${(SHIFT * 1000).toFixed(1)} mm; POSITION/NORMAL/weights/IBM/extras untouched`);
writeGlb(glb, OUT);
console.log(`  wrote ${OUT.split('/').pop()}`);
