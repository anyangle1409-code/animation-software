import { readGlb, readSkin, accessorView } from './glb.mjs';

const glb = readGlb(process.argv[2]);
const primitive = glb.json.meshes[0].primitives[0];
const skin = readSkin(glb, primitive);
const position = accessorView(glb, primitive.attributes.POSITION);
const names = glb.json.skins[0].joints.map((node) => glb.json.nodes[node].name);

const dominant = (vertex) => {
  let best = -1;
  let bestWeight = 0;
  for (let slot = 0; slot < skin.slots; slot += 1) {
    const weight = skin.weights[vertex * skin.slots + slot];
    if (weight > bestWeight) {
      bestWeight = weight;
      best = skin.joints[vertex * skin.slots + slot];
    }
  }
  return names[best] ?? '?';
};

// What lives in each horizontal slice of the hip region.
for (let y = 0.75; y <= 1.30001; y += 0.05) {
  const lo = y - 0.025;
  const hi = y + 0.025;
  const counts = new Map();
  let minX = 9;
  let maxX = -9;
  let minZ = 9;
  let maxZ = -9;
  const xs = [];
  for (let vertex = 0; vertex < skin.count; vertex += 1) {
    const py = position.data[vertex * 3 + 1];
    if (py < lo || py > hi) continue;
    const name = dominant(vertex);
    counts.set(name, (counts.get(name) ?? 0) + 1);
    const px = position.data[vertex * 3];
    const pz = position.data[vertex * 3 + 2];
    if (/thigh|pelvis|spine|shin/.test(name)) {
      minX = Math.min(minX, px);
      maxX = Math.max(maxX, px);
      minZ = Math.min(minZ, pz);
      maxZ = Math.max(maxZ, pz);
      xs.push(px);
    }
  }
  const top = [...counts].sort((a, b) => b[1] - a[1]).slice(0, 4);
  // A gap in the middle means two separate legs at this height.
  xs.sort((a, b) => a - b);
  let widestGap = 0;
  let gapAt = 0;
  for (let i = 1; i < xs.length; i += 1) {
    if (xs[i] - xs[i - 1] > widestGap) {
      widestGap = xs[i] - xs[i - 1];
      gapAt = (xs[i] + xs[i - 1]) / 2;
    }
  }
  console.log(
    `y=${y.toFixed(2)}  x[${minX.toFixed(3)},${maxX.toFixed(3)}] z[${minZ.toFixed(3)},${maxZ.toFixed(3)}]` +
      `  gap ${(widestGap * 1000).toFixed(0)}mm at x=${gapAt.toFixed(3)}  ` +
      top.map(([n, c]) => `${n}:${c}`).join(' '),
  );
}
