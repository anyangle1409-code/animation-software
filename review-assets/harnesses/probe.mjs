import { readGlb, accessorView, readSkin } from './glb.mjs';

const glb = readGlb(process.argv[2]);
const primitive = glb.json.meshes[0].primitives[0];
const skin = readSkin(glb, primitive);
const names = glb.json.skins[0].joints.map((n) => glb.json.nodes[n].name);
const position = accessorView(glb, primitive.attributes.POSITION);
const index = accessorView(glb, primitive.indices);

console.log('vertices', skin.count, 'slots', skin.slots, 'sets', skin.sets.length);
console.log('weight component types', skin.sets.map((s) => s.weights.componentType).join(','));
console.log('joint component types', skin.sets.map((s) => s.joints.componentType).join(','));

// Weight-sum sanity and used-slot histogram, so a repair can preserve both.
let minSum = Infinity;
let maxSum = -Infinity;
const used = new Map();
for (let v = 0; v < skin.count; v += 1) {
  let sum = 0;
  let count = 0;
  for (let s = 0; s < skin.slots; s += 1) {
    const w = skin.weights[v * skin.slots + s];
    sum += w;
    if (w > 0) count += 1;
  }
  minSum = Math.min(minSum, sum);
  maxSum = Math.max(maxSum, sum);
  used.set(count, (used.get(count) ?? 0) + 1);
}
console.log('weight sum range', minSum.toFixed(9), maxSum.toFixed(9));
console.log('influences per vertex', [...used].sort((a, b) => a[0] - b[0]).map(([k, n]) => `${k}:${n}`).join(' '));

// Weight on a named bone, per vertex.
const boneIndex = new Map(names.map((n, i) => [n, i]));
const weightOn = (vertex, bone) => {
  const target = boneIndex.get(bone);
  let total = 0;
  for (let s = 0; s < skin.slots; s += 1) {
    if (skin.joints[vertex * skin.slots + s] === target) total += skin.weights[vertex * skin.slots + s];
  }
  return total;
};

const pairs = [];
for (const side of ['L', 'R']) {
  for (const digit of ['index', 'middle', 'ring', 'pinky']) {
    pairs.push([`DEF-hand.${side}`, `DEF-f_${digit}.01.${side}`]);
  }
  pairs.push([`DEF-forearm.${side}.001`, `DEF-hand.${side}`]);
}

for (const [a, b] of pairs) {
  let shared = 0;
  let aOnly = 0;
  let bOnly = 0;
  const blends = [];
  for (let v = 0; v < skin.count; v += 1) {
    const wa = weightOn(v, a);
    const wb = weightOn(v, b);
    if (wa > 1e-6 && wb > 1e-6) {
      shared += 1;
      blends.push(wb / (wa + wb));
    } else if (wa > 1e-6) aOnly += 1;
    else if (wb > 1e-6) bOnly += 1;
  }
  blends.sort((x, y) => x - y);
  const q = (f) => (blends.length ? blends[Math.floor(f * (blends.length - 1))].toFixed(3) : '-');
  console.log(
    `${a.padEnd(22)} ${b.padEnd(22)} shared=${String(shared).padStart(4)} aOnly=${String(aOnly).padStart(4)} bOnly=${String(bOnly).padStart(4)} blend q10=${q(0.1)} q50=${q(0.5)} q90=${q(0.9)}`,
  );
}

// One-ring adjacency, so "one ring out" is a real mesh neighbourhood.
const neighbours = Array.from({ length: skin.count }, () => new Set());
for (let t = 0; t < index.count; t += 3) {
  const a = index.data[t];
  const b = index.data[t + 1];
  const c = index.data[t + 2];
  neighbours[a].add(b); neighbours[a].add(c);
  neighbours[b].add(a); neighbours[b].add(c);
  neighbours[c].add(a); neighbours[c].add(b);
}

// How abrupt is the handover along an edge? Report the worst edges for the
// index-finger MCP and the wrist, in blend units.
for (const [a, b] of [['DEF-hand.L', 'DEF-f_ring.01.L'], ['DEF-forearm.L.001', 'DEF-hand.L']]) {
  const blend = new Float32Array(skin.count).fill(-1);
  for (let v = 0; v < skin.count; v += 1) {
    const wa = weightOn(v, a);
    const wb = weightOn(v, b);
    if (wa + wb > 1e-6) blend[v] = wb / (wa + wb);
  }
  let worst = 0;
  let worstEdge = null;
  let steps = 0;
  for (let v = 0; v < skin.count; v += 1) {
    if (blend[v] < 0) continue;
    for (const n of neighbours[v]) {
      if (blend[n] < 0 || n < v) continue;
      const jump = Math.abs(blend[v] - blend[n]);
      if (jump > 0.5) steps += 1;
      if (jump > worst) { worst = jump; worstEdge = [v, n]; }
    }
  }
  console.log(`${a} -> ${b}: worst edge blend jump ${worst.toFixed(3)} at ${worstEdge}, edges jumping >0.5: ${steps}`);
}

const p = (v) => [position.data[v * 3], position.data[v * 3 + 1], position.data[v * 3 + 2]];
console.log('sample hand vertex position', p(0).map((x) => x.toFixed(3)).join(','));
