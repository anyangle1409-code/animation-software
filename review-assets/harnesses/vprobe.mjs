import { readGlb, accessorView, readSkin } from './glb.mjs';

const glb = readGlb(process.argv[2]);
const primitive = glb.json.meshes[0].primitives[0];
const skin = readSkin(glb, primitive);
const names = glb.json.skins[0].joints.map((n) => glb.json.nodes[n].name);
const position = accessorView(glb, primitive.attributes.POSITION);
const index = accessorView(glb, primitive.indices);

const neighbours = Array.from({ length: skin.count }, () => new Set());
for (let t = 0; t < index.count; t += 3) {
  const [a, b, c] = [index.data[t], index.data[t + 1], index.data[t + 2]];
  neighbours[a].add(b); neighbours[a].add(c);
  neighbours[b].add(a); neighbours[b].add(c);
  neighbours[c].add(a); neighbours[c].add(b);
}

const describe = (v) => {
  const parts = [];
  for (let s = 0; s < skin.slots; s += 1) {
    const w = skin.weights[v * skin.slots + s];
    if (w > 1e-5) parts.push(`${names[skin.joints[v * skin.slots + s]]}=${w.toFixed(3)}`);
  }
  const p = [position.data[v * 3], position.data[v * 3 + 1], position.data[v * 3 + 2]];
  return `v${String(v).padStart(5)} [${p.map((x) => x.toFixed(3)).join(',')}] ${parts.join(' ')}`;
};

for (const group of process.argv.slice(3)) {
  console.log(`--- ${group}`);
  for (const v of group.split(',').map(Number)) {
    console.log('  ', describe(v));
    for (const n of [...neighbours[v]].sort((a, b) => a - b)) console.log('      n', describe(n));
  }
}
