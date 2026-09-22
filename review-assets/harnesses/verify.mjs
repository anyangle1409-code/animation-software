// What the candidate changed, and — more to the point — what it did not.
import { readGlb, accessorView, readSkin } from './glb.mjs';

const base = readGlb(process.argv[2]);
const candidate = readGlb(process.argv[3]);

const primitiveOf = (glb) => glb.json.meshes[0].primitives[0];
const basePrimitive = primitiveOf(base);
const candidatePrimitive = primitiveOf(candidate);

// 1. Everything that is not a skin weight must be identical.
const untouched = ['POSITION', 'NORMAL', 'TEXCOORD_0', 'TEXCOORD_1', 'COLOR_0', 'JOINTS_0', 'JOINTS_1', 'JOINTS_2', 'WEIGHTS_1', 'WEIGHTS_2'];
for (const attribute of untouched) {
  if (basePrimitive.attributes[attribute] === undefined) continue;
  const one = accessorView(base, basePrimitive.attributes[attribute]).data;
  const two = accessorView(candidate, candidatePrimitive.attributes[attribute]).data;
  let differs = 0;
  for (let slot = 0; slot < one.length; slot += 1) if (one[slot] !== two[slot]) differs += 1;
  console.log(`${attribute.padEnd(12)} identical: ${differs === 0 ? 'yes' : `NO (${differs} values)`}`);
}
const baseIndex = accessorView(base, basePrimitive.indices).data;
const candidateIndex = accessorView(candidate, candidatePrimitive.indices).data;
let indexDiffers = 0;
for (let slot = 0; slot < baseIndex.length; slot += 1) if (baseIndex[slot] !== candidateIndex[slot]) indexDiffers += 1;
console.log(`indices      identical: ${indexDiffers === 0 ? 'yes' : `NO (${indexDiffers})`}`);

const morphs = basePrimitive.targets ?? [];
let morphDiffers = 0;
morphs.forEach((target, slot) => {
  for (const key of Object.keys(target)) {
    const one = accessorView(base, target[key]).data;
    const two = accessorView(candidate, candidatePrimitive.targets[slot][key]).data;
    for (let value = 0; value < one.length; value += 1) if (one[value] !== two[value]) morphDiffers += 1;
  }
});
console.log(`morph targets: ${morphs.length}, differing values: ${morphDiffers}`);

const skeletonSame =
  JSON.stringify(base.json.nodes) === JSON.stringify(candidate.json.nodes) &&
  JSON.stringify(base.json.skins) === JSON.stringify(candidate.json.skins);
console.log(`skeleton + skin definition identical: ${skeletonSame ? 'yes' : 'NO'}`);

const inverseBinds = accessorView(base, base.json.skins[0].inverseBindMatrices).data;
const candidateBinds = accessorView(candidate, candidate.json.skins[0].inverseBindMatrices).data;
let bindDiffers = 0;
for (let slot = 0; slot < inverseBinds.length; slot += 1) if (inverseBinds[slot] !== candidateBinds[slot]) bindDiffers += 1;
console.log(`inverse bind matrices identical: ${bindDiffers === 0 ? 'yes' : `NO (${bindDiffers})`}`);

// 2. The weights themselves.
const baseSkin = readSkin(base, basePrimitive);
const candidateSkin = readSkin(candidate, candidatePrimitive);
const names = base.json.skins[0].joints.map((node) => base.json.nodes[node].name);

let changed = 0;
let worstSum = 0;
let maxInfluences = 0;
let handMaxInfluences = 0;
const perBone = new Map();
const HAND_AREA = /^DEF-(hand|f_index|f_middle|f_ring|f_pinky|thumb|palm)\.|^DEF-forearm\.[LR]\.001$/;

for (let vertex = 0; vertex < baseSkin.count; vertex += 1) {
  let differs = false;
  let sum = 0;
  let influences = 0;
  let inHand = false;
  for (let slot = 0; slot < baseSkin.slots; slot += 1) {
    const at = vertex * baseSkin.slots + slot;
    const weight = candidateSkin.weights[at];
    sum += weight;
    if (weight > 0) {
      influences += 1;
      if (HAND_AREA.test(names[candidateSkin.joints[at]])) inHand = true;
    }
    if (Math.abs(baseSkin.weights[at] - weight) > 1e-6 || baseSkin.joints[at] !== candidateSkin.joints[at]) {
      differs = true;
    }
  }
  worstSum = Math.max(worstSum, Math.abs(sum - 1));
  maxInfluences = Math.max(maxInfluences, influences);
  if (inHand) handMaxInfluences = Math.max(handMaxInfluences, influences);
  if (!differs) continue;
  changed += 1;
  for (let slot = 0; slot < baseSkin.slots; slot += 1) {
    const at = vertex * baseSkin.slots + slot;
    for (const [skin, sign] of [[baseSkin, -1], [candidateSkin, 1]]) {
      const bone = names[skin.joints[at]];
      const weight = skin.weights[at];
      if (weight <= 0) continue;
      perBone.set(bone, (perBone.get(bone) ?? 0) + sign * weight);
    }
  }
}

console.log(`\nvertices with changed influences: ${changed} of ${baseSkin.count}`);
console.log(`worst |weight sum - 1|: ${worstSum.toExponential(3)}`);
console.log(`max influences per vertex: ${maxInfluences} (hand area: ${handMaxInfluences})`);
console.log('net weight moved per bone:');
for (const [bone, delta] of [...perBone].sort((one, two) => Math.abs(two[1]) - Math.abs(one[1]))) {
  if (Math.abs(delta) < 1e-4) continue;
  console.log(`  ${bone.padEnd(24)} ${delta >= 0 ? '+' : ''}${delta.toFixed(3)}`);
}

// 3. Left/right symmetry of the change.
const sideOf = (bone) => (bone.endsWith('.L') ? 'L' : bone.endsWith('.R') ? 'R' : bone.includes('.L.') ? 'L' : bone.includes('.R.') ? 'R' : '-');
const mirrored = new Map();
for (const [bone, delta] of perBone) {
  const side = sideOf(bone);
  if (side === '-') continue;
  const key = bone.replace(/\.L(\.|$)/, '.*$1').replace(/\.R(\.|$)/, '.*$1');
  const entry = mirrored.get(key) ?? {};
  entry[side] = delta;
  mirrored.set(key, entry);
}
let worstAsymmetry = 0;
for (const [key, entry] of mirrored) {
  const gap = Math.abs((entry.L ?? 0) - (entry.R ?? 0));
  if (gap > worstAsymmetry) worstAsymmetry = gap;
  if (gap > 1e-3) console.log(`  asymmetric: ${key} L=${(entry.L ?? 0).toFixed(3)} R=${(entry.R ?? 0).toFixed(3)}`);
}
console.log(`worst left/right difference in moved weight: ${worstAsymmetry.toFixed(4)}`);
