// What the runtime actually skins with.
//
// three's GLTFLoader reads only JOINTS_0/WEIGHTS_0 — four influences — and then
// calls normalizeSkinWeights(), so the effective skin is "top four lanes,
// rescaled to 1". Anything in JOINTS_1/2 is dead weight in the Studio. This
// measures how much of the hand's authored weight lives outside those lanes.
import { readGlb, accessorView, readSkin } from './glb.mjs';

const glb = readGlb(process.argv[2]);
const primitive = glb.json.meshes[0].primitives[0];
const skin = readSkin(glb, primitive);
const names = glb.json.skins[0].joints.map((n) => glb.json.nodes[n].name);
const index = accessorView(glb, primitive.indices);

const isHandArea = (name) =>
  /DEF-(hand|f_index|f_middle|f_ring|f_pinky|thumb|palm)\./.test(name) ||
  /DEF-forearm\.[LR]\.001/.test(name);

const handBones = new Set(names.filter(isHandArea).map((n) => names.indexOf(n)));

let sorted = 0;
let unsorted = 0;
const sums = [];
let handVertices = 0;
let over4 = 0;
let worst = { sum: 1, vertex: -1 };

for (let v = 0; v < skin.count; v += 1) {
  let inArea = 0;
  for (let s = 0; s < skin.slots; s += 1) {
    if (handBones.has(skin.joints[v * skin.slots + s])) inArea += skin.weights[v * skin.slots + s];
  }
  if (inArea < 0.5) continue;
  handVertices += 1;

  let first4 = 0;
  let used = 0;
  let descending = true;
  let previous = Infinity;
  for (let s = 0; s < skin.slots; s += 1) {
    const w = skin.weights[v * skin.slots + s];
    if (s < 4) first4 += w;
    if (w > 0) used += 1;
    if (w > previous + 1e-7) descending = false;
    previous = w;
  }
  if (descending) sorted += 1; else unsorted += 1;
  if (used > 4) over4 += 1;
  sums.push(first4);
  if (first4 < worst.sum) worst = { sum: first4, vertex: v, used };
}

sums.sort((a, b) => a - b);
const q = (f) => sums[Math.floor(f * (sums.length - 1))].toFixed(4);
console.log(`hand-area vertices: ${handVertices}`);
console.log(`lanes descending: ${sorted} sorted, ${unsorted} unsorted`);
console.log(`vertices with >4 influences: ${over4}`);
console.log(`first-4 weight sum  min=${q(0)} q01=${q(0.01)} q10=${q(0.1)} q50=${q(0.5)} max=${q(1)}`);
console.log(`worst vertex ${worst.vertex}: first4=${worst.sum.toFixed(4)} used=${worst.used}`);

// How much the truncation moves the authored blend at the rings we care about.
const boneIndex = new Map(names.map((n, i) => [n, i]));
const pairBlend = (v, a, b, lanes) => {
  const ai = boneIndex.get(a);
  const bi = boneIndex.get(b);
  let wa = 0;
  let wb = 0;
  let total = 0;
  for (let s = 0; s < lanes; s += 1) {
    const w = skin.weights[v * skin.slots + s];
    total += w;
    if (skin.joints[v * skin.slots + s] === ai) wa += w;
    if (skin.joints[v * skin.slots + s] === bi) wb += w;
  }
  return { wa: wa / (total || 1), wb: wb / (total || 1) };
};

for (const [a, b] of [
  ['DEF-hand.L', 'DEF-f_index.01.L'],
  ['DEF-hand.L', 'DEF-f_middle.01.L'],
  ['DEF-hand.L', 'DEF-f_ring.01.L'],
  ['DEF-hand.L', 'DEF-f_pinky.01.L'],
  ['DEF-forearm.L.001', 'DEF-hand.L'],
]) {
  let moved = 0;
  let maxShift = 0;
  for (let v = 0; v < skin.count; v += 1) {
    const full = pairBlend(v, a, b, skin.slots);
    const runtime = pairBlend(v, a, b, 4);
    if (full.wa + full.wb < 1e-6) continue;
    const fullBlend = full.wb / (full.wa + full.wb);
    const runtimePool = runtime.wa + runtime.wb;
    if (runtimePool < 1e-6) continue;
    const runtimeBlend = runtime.wb / runtimePool;
    const shift = Math.abs(fullBlend - runtimeBlend);
    if (shift > 0.02) moved += 1;
    maxShift = Math.max(maxShift, shift);
  }
  console.log(`${a} -> ${b}: vertices whose blend shifts >0.02 under runtime truncation: ${moved}, max shift ${maxShift.toFixed(3)}`);
}
