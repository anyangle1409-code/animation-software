// Skin material only: a PBR material for the body, and skin tone plus a
// curvature term in the body's vertex colours.
//
// Why here and not in the renderer: the body primitive carries NO material at
// all, so glTF's default applies — base colour white, metallic 1.0, roughness
// 1.0 — which is exactly the dull grey mannequin look. The shorts, which do
// carry a material, read as believable fabric by comparison.
//
// Why the tone goes in COLOR_0 rather than baseColorFactor: CharacterFigure
// sets `material.color` from its `colour` prop on every build, defaulting to
// white, and says so — "multiplies the body's own vertex colours; white leaves
// them as authored". A baseColorFactor would be overwritten on load. Roughness
// and metalness are never touched by the app, so those belong on the material.
//
// Writes only: one material, the body primitive's material index, and COLOR_0.
// No positions, normals, topology, weights, joints, binds, extras or garment.
import { readGlb, accessorView, writeGlb } from './glb.mjs';

const SRC = process.argv[2];
const OUT = process.argv[3];

// sRGB (0.78, 0.60, 0.50) converted to linear, which is what glTF vertex
// colours are. A medium, warm, believable tone for the reference board's
// contemporary athletic male rather than a saturated orange.
const SKIN_LINEAR = [0.5704, 0.3186, 0.2140];
const ROUGHNESS = Number(process.env.SKIN_ROUGHNESS ?? 0.5);
const RANGE = { lo: 0.86, hi: 1.05 };
const TARGET = 0.12; // how far the 95th-percentile crease moves from flat

const srgb = (l) => (l <= 0.0031308 ? l * 12.92 : 1.055 * l ** (1 / 2.4) - 0.055);

const glb = readGlb(SRC);
const prim = glb.json.meshes[0].primitives[0];
const pos = accessorView(glb, prim.attributes.POSITION);
const nor = accessorView(glb, prim.attributes.NORMAL);
const idx = accessorView(glb, prim.indices);
const col = accessorView(glb, prim.attributes.COLOR_0);
if (col.componentType !== 5123 || col.items !== 4 || !col.normalized) {
  throw new Error(`unexpected COLOR_0 layout: comp ${col.componentType} items ${col.items}`);
}

// Neighbours are gathered by POSITION, so a UV seam does not cut the surface in
// half and leave a bright line down the middle of an arm.
const keyOf = (v) => `${pos.data[v * 3]},${pos.data[v * 3 + 1]},${pos.data[v * 3 + 2]}`;
const group = new Map();
for (let v = 0; v < pos.count; v += 1) {
  const k = keyOf(v);
  const list = group.get(k);
  if (list) list.push(v); else group.set(k, [v]);
}
const neighbours = new Map();
const link = (a, b) => {
  const ka = keyOf(a);
  const set = neighbours.get(ka) ?? neighbours.set(ka, new Set()).get(ka);
  set.add(keyOf(b));
};
for (let t = 0; t < idx.count; t += 3) {
  const a = idx.data[t], b = idx.data[t + 1], c = idx.data[t + 2];
  link(a, b); link(b, a); link(b, c); link(c, b); link(c, a); link(a, c);
}

// Discrete mean-curvature sign: where the neighbourhood's centroid sits along
// the vertex normal. Positive is a valley, negative a ridge. Scaled by the
// local edge length so a dense region is not read as flatter than a coarse one.
const raw = new Map();
const magnitudes = [];
for (const [key, list] of group) {
  const v = list[0];
  const near = neighbours.get(key);
  if (!near || near.size === 0) { raw.set(key, 0); continue; }
  let cx = 0, cy = 0, cz = 0, span = 0;
  for (const other of near) {
    const w = group.get(other)[0];
    cx += pos.data[w * 3]; cy += pos.data[w * 3 + 1]; cz += pos.data[w * 3 + 2];
    span += Math.hypot(pos.data[w * 3] - pos.data[v * 3], pos.data[w * 3 + 1] - pos.data[v * 3 + 1], pos.data[w * 3 + 2] - pos.data[v * 3 + 2]);
  }
  const n = near.size;
  cx /= n; cy /= n; cz /= n;
  span /= n;
  if (span <= 0) { raw.set(key, 0); continue; }
  const h = ((cx - pos.data[v * 3]) * nor.data[v * 3]
    + (cy - pos.data[v * 3 + 1]) * nor.data[v * 3 + 1]
    + (cz - pos.data[v * 3 + 2]) * nor.data[v * 3 + 2]) / span;
  raw.set(key, h);
  magnitudes.push(Math.abs(h));
}
magnitudes.sort((a, b) => a - b);
const p95 = magnitudes[Math.floor(magnitudes.length * 0.95)] || 1;
const gain = TARGET / p95;

let darkest = 1, lightest = 1;
for (const [key, list] of group) {
  const shade = Math.min(RANGE.hi, Math.max(RANGE.lo, 1 - raw.get(key) * gain));
  if (shade < darkest) darkest = shade;
  if (shade > lightest) lightest = shade;
  for (const v of list) {
    for (let c = 0; c < 3; c += 1) {
      col.data[v * 4 + c] = Math.round(Math.min(1, Math.max(0, SKIN_LINEAR[c] * shade)) * 65535);
    }
    col.data[v * 4 + 3] = 65535;
  }
}

glb.json.materials = glb.json.materials ?? [];
const existing = glb.json.materials.findIndex((m) => m.name === 'HomeGymPT_Skin');
const material = {
  name: 'HomeGymPT_Skin',
  doubleSided: false,
  pbrMetallicRoughness: {
    // White on purpose: the renderer overwrites this with its own colour prop,
    // and the tone lives in COLOR_0 where the renderer leaves it alone.
    baseColorFactor: [1, 1, 1, 1],
    metallicFactor: 0,
    roughnessFactor: ROUGHNESS,
  },
};
if (existing >= 0) { glb.json.materials[existing] = material; prim.material = existing; }
else { prim.material = glb.json.materials.push(material) - 1; }

console.log(`${SRC.split('/').pop()} -> ${OUT.split('/').pop()}`);
console.log(`  skin tone linear ${SKIN_LINEAR.map((x) => x.toFixed(4)).join(', ')}  = sRGB ${SKIN_LINEAR.map((x) => srgb(x).toFixed(3)).join(', ')}`);
console.log(`  material: metallic 0, roughness ${ROUGHNESS} (was: no material, so glTF default metallic 1 / roughness 1)`);
console.log(`  curvature shading: p95 |h| ${p95.toFixed(4)}, gain ${gain.toFixed(3)}, range ${darkest.toFixed(3)}..${lightest.toFixed(3)}`);
console.log(`  vertices coloured ${pos.count}, meshes touched: 1 of ${glb.json.meshes.length}`);
writeGlb(glb, OUT);
