import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Quaternion, Vector3 } from 'three';

const project = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const sourceRoot = process.env.MAKEHUMAN_SOURCE_DIR;
if (!sourceRoot) throw new Error('Set MAKEHUMAN_SOURCE_DIR to the directory containing the five CC0 source files');
const objText = fs.readFileSync(`${sourceRoot}/base.obj`, 'utf8');
const maleText = fs.readFileSync(`${sourceRoot}/caucasian-male-young.target`, 'utf8');
const muscleText = fs.readFileSync(`${sourceRoot}/male-muscular.target`, 'utf8');
const weightData = JSON.parse(fs.readFileSync(`${sourceRoot}/default_weights.mhw`, 'utf8'));
const sourceSkeleton = JSON.parse(fs.readFileSync(`${sourceRoot}/default.mhskel`, 'utf8'));
const canonicalBones = JSON.parse(execFileSync('./node_modules/.bin/vite-node', ['scripts/dump-canonical-skeleton.ts'], {
  cwd: project,
  encoding: 'utf8',
}));

const vertices = [];
const faces = [];
const vertexGroup = new Map();
let group = '';
for (const line of objText.split(/\r?\n/)) {
  if (line.startsWith('v ')) {
    const [, x, y, z] = line.trim().split(/\s+/);
    vertices.push([Number(x), Number(y), Number(z)]);
  } else if (line.startsWith('g ')) {
    group = line.slice(2).trim();
  } else if (line.startsWith('f ') && ['body', 'helper-l-eye', 'helper-r-eye'].includes(group)) {
    const face = line.trim().split(/\s+/).slice(1).map((part) => Number(part.split('/')[0]) - 1);
    faces.push(face);
    for (const index of face) vertexGroup.set(index, group);
  }
}

// The macro target establishes an adult male body; the second target adds the
// athletic definition visible in the coaching reference.
for (const line of `${maleText}\n${muscleText}`.split(/\r?\n/)) {
  if (!line || line.startsWith('#')) continue;
  const [index, dx, dy, dz] = line.trim().split(/\s+/).map(Number);
  const vertex = vertices[index];
  if (!vertex) continue;
  vertex[0] += dx;
  vertex[1] += dy;
  vertex[2] += dz;
}

const used = [...vertexGroup.keys()];
const body = used.filter((index) => vertexGroup.get(index) === 'body');
const minY = Math.min(...body.map((index) => vertices[index][1]));
const maxY = Math.max(...body.map((index) => vertices[index][1]));
const scale = 1.75 / (maxY - minY);
const minX = Math.min(...body.map((index) => vertices[index][0]));
const maxX = Math.max(...body.map((index) => vertices[index][0]));
const centreX = (minX + maxX) / 2;
const torsoDepth = body
  .map((index) => vertices[index])
  .filter(([, y]) => (y - minY) * scale > 0.9 && (y - minY) * scale < 1.15)
  .map(([, , z]) => z)
  .sort((a, b) => a - b);
const centreZ = (torsoDepth[0] + torsoDepth[torsoDepth.length - 1]) / 2;

// MakeHuman calls anatomical left +X; the app rig calls anatomical left -X.
const toStudio = ([x, y, z]) => new Vector3(
  -(x - centreX) * scale,
  (y - minY) * scale,
  (z - centreZ) * scale,
);

const averageJoint = (label) => {
  const indices = sourceSkeleton.joints[label];
  if (!indices?.length) throw new Error(`Missing MakeHuman joint ${label}`);
  const point = new Vector3();
  for (const index of indices) point.add(toStudio(vertices[index]));
  return point.multiplyScalar(1 / indices.length);
};

const sourceBone = (name) => {
  const definition = sourceSkeleton.bones[name];
  if (!definition) throw new Error(`Missing MakeHuman bone ${name}`);
  return { head: averageJoint(definition.head), tail: averageJoint(definition.tail) };
};

const canonical = new Map(canonicalBones.map((bone) => [bone.name, {
  head: new Vector3(bone.head.x, bone.head.y, bone.head.z),
  tail: new Vector3(bone.tail.x, bone.tail.y, bone.tail.z),
}]));
const canonicalOrder = canonicalBones.map((bone) => bone.name);
const canonicalIndex = new Map(canonicalOrder.map((name, index) => [name, index]));

/** Sample a point and owning bone along a canonical multi-bone chain. */
const targetChain = (names) => {
  const segments = names.map((name) => ({ name, ...canonical.get(name) }));
  const lengths = segments.map(({ head, tail }) => head.distanceTo(tail));
  const total = lengths.reduce((sum, length) => sum + length, 0);
  const sample = (fraction) => {
    let distance = Math.max(0, Math.min(1, fraction)) * total;
    for (let i = 0; i < segments.length; i += 1) {
      if (distance <= lengths[i] || i === segments.length - 1) {
        return segments[i].head.clone().lerp(segments[i].tail, lengths[i] ? distance / lengths[i] : 0);
      }
      distance -= lengths[i];
    }
  };
  const owner = (fraction) => {
    let distance = Math.max(0, Math.min(0.999999, fraction)) * total;
    for (let i = 0; i < segments.length; i += 1) {
      if (distance < lengths[i] || i === segments.length - 1) return segments[i].name;
      distance -= lengths[i];
    }
  };
  return { sample, owner };
};

/** Rotate into the target segment while scaling only distance along the bone. */
const conversions = new Map();
const defineConversionFromPoints = (sourceName, source, targetName, targetHead, targetTail) => {
  const sourceVector = source.tail.clone().sub(source.head);
  const targetVector = targetTail.clone().sub(targetHead);
  const sourceLength = sourceVector.length();
  const targetLength = targetVector.length();
  const sourceDirection = sourceVector.clone().normalize();
  const rotation = new Quaternion().setFromUnitVectors(sourceDirection, targetVector.clone().normalize());
  conversions.set(sourceName, {
    targetName,
    transform(point) {
      const delta = point.clone().sub(source.head);
      const along = sourceDirection.clone().multiplyScalar(delta.dot(sourceDirection));
      const across = delta.sub(along);
      return across.add(along.multiplyScalar(targetLength / sourceLength)).applyQuaternion(rotation).add(targetHead);
    },
  });
};
const defineConversion = (sourceName, targetName, targetHead, targetTail) =>
  defineConversionFromPoints(sourceName, sourceBone(sourceName), targetName, targetHead, targetTail);

const mapChain = (sourceNames, targetNames) => {
  const sourceSegments = sourceNames.map((name) => ({ name, ...sourceBone(name) }));
  const sourceLengths = sourceSegments.map(({ head, tail }) => head.distanceTo(tail));
  const sourceTotal = sourceLengths.reduce((sum, length) => sum + length, 0);
  const target = targetChain(targetNames);
  let walked = 0;
  sourceSegments.forEach((segment, index) => {
    const start = walked / sourceTotal;
    walked += sourceLengths[index];
    const end = walked / sourceTotal;
    defineConversion(segment.name, target.owner((start + end) / 2), target.sample(start), target.sample(end));
  });
};

// Source spine numbering runs from 05 at the waist to 01 at the neck.
mapChain(['root'], ['pelvis']);
mapChain(['spine05', 'spine04', 'spine03', 'spine02', 'spine01'], ['spine_01', 'spine_02', 'spine_03']);
mapChain(['neck01', 'neck02', 'neck03'], ['neck']);
mapChain(['head'], ['head']);

for (const sourceSide of ['L', 'R']) {
  const side = sourceSide === 'L' ? 'l' : 'r';
  mapChain([`clavicle.${sourceSide}`], [`clavicle_${side}`]);
  mapChain([`shoulder01.${sourceSide}`, `upperarm01.${sourceSide}`, `upperarm02.${sourceSide}`], [`upperarm_${side}`]);
  mapChain([`lowerarm01.${sourceSide}`, `lowerarm02.${sourceSide}`], [`forearm_${side}`]);
  // MakeHuman's wrist bone is only a short internal wrist segment. The app's
  // hand bone spans the whole palm, so use the wrist-to-knuckle distance as the
  // source segment or the palm is stretched to several times its real length.
  const wristName = `wrist.${sourceSide}`;
  const palmHeads = [2, 3, 4].map((finger) => sourceBone(`finger${finger}-1.${sourceSide}`).head);
  const palmTail = palmHeads.reduce((sum, point) => sum.add(point), new Vector3()).multiplyScalar(1 / palmHeads.length);
  const hand = canonical.get(`hand_${side}`);
  defineConversionFromPoints(
    wristName,
    { head: sourceBone(wristName).head, tail: palmTail },
    `hand_${side}`,
    hand.head,
    hand.tail,
  );
  mapChain([`upperleg01.${sourceSide}`, `upperleg02.${sourceSide}`], [`thigh_${side}`]);
  mapChain([`lowerleg01.${sourceSide}`, `lowerleg02.${sourceSide}`], [`shin_${side}`]);
  mapChain([`foot.${sourceSide}`], [`foot_${side}`]);
  const fingerNames = ['thumb', 'index', 'middle', 'ring', 'pinky'];
  for (let finger = 1; finger <= 5; finger += 1) {
    for (let segment = 1; segment <= 3; segment += 1) {
      mapChain([`finger${finger}-${segment}.${sourceSide}`], [`${fingerNames[finger - 1]}_0${segment}_${side}`]);
    }
  }
}

// Rigid aliases retain detailed surface without animating source micro-controls.
const aliasConversion = (sourceName, anchorSource, targetName) => {
  const anchor = conversions.get(anchorSource);
  if (!anchor) throw new Error(`Missing conversion anchor ${anchorSource}`);
  conversions.set(sourceName, { targetName, transform: anchor.transform });
};

for (const sourceName of Object.keys(weightData.weights)) {
  if (conversions.has(sourceName)) continue;
  const sideMatch = /\.([LR])$/.exec(sourceName);
  const side = sideMatch?.[1] === 'L' ? 'l' : sideMatch?.[1] === 'R' ? 'r' : null;
  const stem = sourceName.replace(/\.[LR]$/, '');
  if (side && stem.startsWith('metacarpal')) aliasConversion(sourceName, `wrist.${sideMatch[1]}`, `hand_${side}`);
  else if (side && stem.startsWith('toe')) aliasConversion(sourceName, `foot.${sideMatch[1]}`, `foot_${side}`);
  else if (stem === 'pelvis') aliasConversion(sourceName, 'root', 'pelvis');
  else if (stem === 'breast') aliasConversion(sourceName, 'spine02', 'spine_03');
  else if (/^(jaw|eye|special|oculi|orbicularis|oris|risorius|levator|temporalis|tongue)/.test(stem)) {
    aliasConversion(sourceName, 'head', 'head');
  }
}

const sourceInfluences = Array.from({ length: vertices.length }, () => []);
for (const [sourceName, entries] of Object.entries(weightData.weights)) {
  const conversion = conversions.get(sourceName);
  if (!conversion) continue;
  for (const [vertex, weight] of entries) sourceInfluences[vertex].push({ sourceName, weight });
}

const originalIndices = [...used].sort((a, b) => a - b);
const compactIndex = new Map(originalIndices.map((original, compact) => [original, compact]));
const positions = new Float32Array(originalIndices.length * 3);
const colours = new Uint8Array(originalIndices.length * 3);
const skinIndices = new Uint16Array(originalIndices.length * 4);
const skinWeights = new Float32Array(originalIndices.length * 4);

const linearByte = (hex) => [...hex.matchAll(/[0-9a-f]{2}/gi)].map(([pair]) => {
  const channel = parseInt(pair, 16) / 255;
  const linear = channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  return Math.round(linear * 255);
});
const skin = linearByte('b9bec2');
const shorts = linearByte('202226');
const eye = linearByte('eceef0');
const iris = linearByte('343a40');

let unmappedVertices = 0;
for (let compact = 0; compact < originalIndices.length; compact += 1) {
  const vertex = originalIndices[compact];
  const sourcePoint = toStudio(vertices[vertex]);
  let influences = sourceInfluences[vertex];
  const part = vertexGroup.get(vertex);
  if (part !== 'body' || sourcePoint.y > 1.50) influences = [{ sourceName: 'head', weight: 1 }];
  if (!influences.length) {
    influences = [{ sourceName: 'root', weight: 1 }];
    unmappedVertices += 1;
  }

  const aggregated = new Map();
  const targetPoint = new Vector3();
  let total = 0;
  for (const influence of influences) {
    const conversion = conversions.get(influence.sourceName);
    if (!conversion) continue;
    // Reject tiny mirrored-side contaminants in the source weights. They are
    // harmless in MakeHuman's dense rig but would couple the two feet or hands
    // when collapsed onto this compact skeleton.
    if (sourcePoint.x > 0.03 && conversion.targetName.endsWith('_l')) continue;
    if (sourcePoint.x < -0.03 && conversion.targetName.endsWith('_r')) continue;
    targetPoint.addScaledVector(conversion.transform(sourcePoint), influence.weight);
    aggregated.set(conversion.targetName, (aggregated.get(conversion.targetName) ?? 0) + influence.weight);
    total += influence.weight;
  }
  if (total === 0) {
    targetPoint.copy(sourcePoint);
    aggregated.set('root', 1);
    total = 1;
  }
  targetPoint.multiplyScalar(1 / total);
  // The max-muscle source has high, squared-off deltoid caps. Round the outer
  // shoulder around the actual humeral joint and give the upper edge a gentle
  // neck-to-deltoid slope. Weighting the correction prevents a seam where the
  // chest, clavicle and upper arm meet.
  const shoulderWeight = [...aggregated.entries()].reduce(
    (sum, [name, weight]) => sum + (
      name === 'spine_03' || name.startsWith('clavicle_') || name.startsWith('upperarm_')
        ? weight
        : 0
    ),
    0,
  ) / total;
  if (shoulderWeight > 0 && targetPoint.y > 1.30 && targetPoint.y < 1.50) {
    const sign = Math.sign(targetPoint.x) || 1;
    const width = Math.abs(targetPoint.x);
    if (width > 0.17) {
      const roundedWidth = 0.17 + (width - 0.17) * 0.74;
      targetPoint.x = sign * (width + (roundedWidth - width) * shoulderWeight);
    }
    const shoulderTop = 1.476 - 0.22 * Math.max(0, Math.abs(targetPoint.x) - 0.05);
    if (targetPoint.y > shoulderTop) {
      targetPoint.y -= (targetPoint.y - shoulderTop) * 0.82 * shoulderWeight;
    }
  }

  // The source forehead reads too tall on the compact coaching rig. Compress
  // the head vertically from its neck base, keep the crown at the rig height,
  // and add a little width at the cranium/temples for an adult-human profile.
  const headWeight = (aggregated.get('head') ?? 0) / total;
  if (headWeight > 0) {
    const oldY = targetPoint.y;
    const compressedY = 1.52 + (oldY - 1.52) * 0.92 + 0.018;
    targetPoint.y += (compressedY - oldY) * headWeight;
    const headWidth = oldY > 1.65 ? 1.08 : oldY > 1.56 ? 1.04 : 0.99;
    targetPoint.x *= 1 + (headWidth - 1) * headWeight;
  }

  // Refine the macro target into the lean V-shaped torso from the exercise
  // reference: a defined chest, a compact waist and natural hips. Blend the
  // sculpt by central-bone weight so the deltoid and hip seams stay continuous.
  const central = new Set(['root', 'pelvis', 'spine_01', 'spine_02', 'spine_03']);
  const centralWeight = [...aggregated.entries()].reduce(
    (sum, [name, weight]) => sum + (central.has(name) ? weight : 0),
    0,
  ) / total;
  const y = targetPoint.y;
  let torsoScale = 1;
  if (y >= 0.88 && y < 0.96) torsoScale = 1.03;
  else if (y < 1.03 && y >= 0.96) torsoScale = 1.03 + ((y - 0.96) / 0.07) * (0.82 - 1.03);
  else if (y < 1.14 && y >= 1.03) torsoScale = 0.82;
  else if (y < 1.28 && y >= 1.14) torsoScale = 0.82 + ((y - 1.14) / 0.14) * (1.12 - 0.82);
  else if (y < 1.36 && y >= 1.28) torsoScale = 1.12;
  else if (y < 1.42 && y >= 1.36) torsoScale = 1.12 + ((y - 1.36) / 0.06) * (1 - 1.12);
  targetPoint.x *= 1 + (torsoScale - 1) * centralWeight;
  // Fit the plantar surface to the app's y=0 floor while leaving the ankle in
  // place. The canonical foot bone is a centre line, not the sole itself.
  if (targetPoint.y < 0.08) {
    targetPoint.y += 0.053 * Math.max(0, Math.min(1, (0.08 - targetPoint.y) / 0.133));
  }
  positions.set(targetPoint.toArray(), compact * 3);

  // The app deliberately caps the coaching character at two influences. This
  // keeps mobile export compact and makes joint blending predictable.
  const top = [...aggregated.entries()].sort((a, b) => b[1] - a[1]).slice(0, 2);
  const topTotal = top.reduce((sum, [, weight]) => sum + weight, 0) || 1;
  for (let slot = 0; slot < 4; slot += 1) {
    skinIndices[compact * 4 + slot] = canonicalIndex.get(top[slot]?.[0] ?? top[0][0]);
    skinWeights[compact * 4 + slot] = (top[slot]?.[1] ?? 0) / topTotal;
  }

  let colour = skin;
  if (part === 'helper-l-eye' || part === 'helper-r-eye') colour = vertices[vertex][2] > 1.34 ? iris : eye;
  else if (
    targetPoint.y >= 0.76 && targetPoint.y <= 1.04 &&
    ['root', 'pelvis', 'spine_01', 'thigh_l', 'thigh_r'].includes(top[0][0])
  ) colour = shorts;
  colours.set(colour, compact * 3);
}

const indices = [];
for (const face of faces) {
  if (face.length < 3) continue;
  // Mirroring X reverses winding.
  for (let i = 1; i < face.length - 1; i += 1) {
    indices.push(compactIndex.get(face[0]), compactIndex.get(face[i + 1]), compactIndex.get(face[i]));
  }
}

const encode = (array) => Buffer.from(array.buffer).toString('base64');
const destination = `${project}/src/body`;
const generated = '// Generated from MakeHuman CC0 assets. See THIRD_PARTY_ASSETS.md.\n';
fs.writeFileSync(`${destination}/anatomicalMeta.ts`, generated +
  `export const ANATOMICAL_VERTEX_COUNT = ${originalIndices.length};\n` +
  `export const ANATOMICAL_TRIANGLE_COUNT = ${indices.length / 3};\n`);
fs.writeFileSync(`${destination}/anatomicalPositions.ts`, generated +
  `export const ANATOMICAL_POSITIONS = '${encode(positions)}';\n`);
fs.writeFileSync(`${destination}/anatomicalIndices.ts`, generated +
  `export const ANATOMICAL_INDICES = '${encode(new Uint16Array(indices))}';\n`);
fs.writeFileSync(`${destination}/anatomicalSkinIndices.ts`, generated +
  `export const ANATOMICAL_SKIN_INDICES = '${encode(skinIndices)}';\n`);
fs.writeFileSync(`${destination}/anatomicalSkinWeights.ts`, generated +
  `export const ANATOMICAL_SKIN_WEIGHTS = '${encode(skinWeights)}';\n`);
fs.writeFileSync(`${destination}/anatomicalColours.ts`, generated +
  `export const ANATOMICAL_COLOURS = '${encode(colours)}';\n`);
console.log({ vertices: originalIndices.length, triangles: indices.length / 3, unmappedVertices, scale });
