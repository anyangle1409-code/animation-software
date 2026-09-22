// Build athletic shorts as a separate skinned mesh over an existing character.
//
// The shorts are a shell lifted off the character's own surface: the body's
// triangles in the hip band are clipped to a waistband and a hem, pushed out
// along their normals, and smoothed so the garment reads as fabric rather than
// as shrink-wrap over anatomy. Every shorts vertex carries the skin weights of
// the body surface it came from, which is the whole trick — linear blend
// skinning is linear, so a vertex at `body + offset` with the body's own
// weights lands at `skinned body + M·offset` in every pose. The clearance is
// therefore preserved by construction, in a squat as much as in the bind pose,
// without a cloth solver and without a single new bone.
//
// Nothing about the body is read except its surface: no vertex of it moves, no
// weight of it changes, the skeleton is untouched, and the original mesh is
// left exactly as it was.
import { writeFileSync } from 'node:fs';
import { readGlb, writeGlb, accessorView, readSkin } from './glb.mjs';

const WAIST_Y = Number(process.env.WAIST ?? 1.175);
const HEM_Y = Number(process.env.HEM ?? 0.82);
const OFFSET = Number(process.env.OFFSET ?? 0.011);
const FABRIC = Number(process.env.FABRIC ?? 0.004);
const MIN_CLEARANCE = Number(process.env.CLEARANCE ?? 0.006);
const INSEAM_OFFSET = Number(process.env.INSEAM_OFFSET ?? 0.0035);
const INSEAM_CLEARANCE = Number(process.env.INSEAM_CLEARANCE ?? 0.0035);
// The front panel hangs clear of the body rather than resting on it, which is
// both what shorts do and what gives deep hip flexion somewhere to go.
const FRONT_OFFSET = Number(process.env.FRONT_OFFSET ?? 0.019);
const FRONT_CLEARANCE = Number(process.env.FRONT_CLEARANCE ?? 0.013);
// How wide the front panel is, and how hard it is pulled flat.
const POUCH_WIDTH = Number(process.env.POUCH_WIDTH ?? 0.115);
const POUCH_GAIN = Number(process.env.POUCH_GAIN ?? 1.7);
// Where the front panel gives way to the inseam, and how far forward the
// inseam's tight treatment is allowed to reach.
const POUCH_LOW = Number(process.env.POUCH_LOW ?? 0.955);
const INSEAM_FRONT = Number(process.env.INSEAM_FRONT ?? 0.2);
const SMOOTH_PASSES = Number(process.env.SMOOTH ?? 12);
const OUTWARD_PASSES = Number(process.env.OUTWARD ?? 70);
// The viewer forces every material colour to white, so the garment carries its
// colour as vertex colour, which survives that. Linear space, as glTF wants.
const CLOTH = [
  Number(process.env.CLOTH_R ?? 0.075),
  Number(process.env.CLOTH_G ?? 0.079),
  Number(process.env.CLOTH_B ?? 0.09),
];

const WAIST_BONES = [
  'DEF-spine',
  'DEF-spine.001',
  'DEF-pelvis.L',
  'DEF-pelvis.R',
  'DEF-thigh.L',
  'DEF-thigh.R',
  'DEF-thigh.L.001',
  'DEF-thigh.R.001',
];

export function buildShorts(inputPath, outputPath) {
  const glb = readGlb(inputPath);
  const primitive = glb.json.meshes[0].primitives[0];
  const position = accessorView(glb, primitive.attributes.POSITION);
  const normal = accessorView(glb, primitive.attributes.NORMAL);
  const index = accessorView(glb, primitive.indices);
  const skin = readSkin(glb, primitive);
  const names = glb.json.skins[0].joints.map((node) => glb.json.nodes[node].name);
  const allowed = new Set(WAIST_BONES.map((name) => names.indexOf(name)).filter((slot) => slot >= 0));

  // The only thing that has to be kept out of the garment is the arms: the
  // character binds in an A-pose with the hands beside the hips, so they sit
  // squarely inside the band the shorts are cut from.
  //
  // Demanding instead that a vertex be *mostly* hip-weighted looks equivalent
  // and is not. A triangle is only usable when all three of its corners pass,
  // and a triangle straddling the waistband has its third corner up the back
  // where the weights belong to a higher spine bone; that triangle is then
  // dropped whole, and the waistband comes out as a sawtooth of missing
  // triangles instead of the clean line the clip would have cut.
  const armBones = new Set(
    names
      .map((name, slot) => [name, slot])
      .filter(([name]) => /^DEF-(hand|f_index|f_middle|f_ring|f_pinky|thumb|palm|forearm|upper_arm|shoulder)/.test(name))
      .map(([, slot]) => slot),
  );
  const count = position.count;
  const onBody = new Uint8Array(count);
  for (let vertex = 0; vertex < count; vertex += 1) {
    let arm = 0;
    for (let slot = 0; slot < skin.slots; slot += 1) {
      if (armBones.has(skin.joints[vertex * skin.slots + slot])) arm += skin.weights[vertex * skin.slots + slot];
    }
    onBody[vertex] = arm > 0.05 ? 0 : 1;
  }
  void allowed;

  /**
   * A point on the garment's surface: where it sits, and which body vertices it
   * borrows its skin weights from.
   */
  const point = (vertex) => ({
    x: position.data[vertex * 3],
    y: position.data[vertex * 3 + 1],
    z: position.data[vertex * 3 + 2],
    nx: normal.data[vertex * 3],
    ny: normal.data[vertex * 3 + 1],
    nz: normal.data[vertex * 3 + 2],
    from: new Map([[vertex, 1]]),
  });

  const mix = (a, b, t) => {
    const from = new Map();
    for (const [vertex, weight] of a.from) from.set(vertex, (from.get(vertex) ?? 0) + weight * (1 - t));
    for (const [vertex, weight] of b.from) from.set(vertex, (from.get(vertex) ?? 0) + weight * t);
    return {
      x: a.x + (b.x - a.x) * t,
      y: a.y + (b.y - a.y) * t,
      z: a.z + (b.z - a.z) * t,
      nx: a.nx + (b.nx - a.nx) * t,
      ny: a.ny + (b.ny - a.ny) * t,
      nz: a.nz + (b.nz - a.nz) * t,
      from,
    };
  };

  /** Sutherland–Hodgman against one horizontal half-space. */
  const clip = (polygon, keepBelow, level) => {
    const inside = (p) => (keepBelow ? p.y <= level : p.y >= level);
    const out = [];
    for (let slot = 0; slot < polygon.length; slot += 1) {
      const current = polygon[slot];
      const next = polygon[(slot + 1) % polygon.length];
      const currentIn = inside(current);
      const nextIn = inside(next);
      if (currentIn) out.push(current);
      if (currentIn !== nextIn) {
        const t = (level - current.y) / (next.y - current.y);
        if (Number.isFinite(t)) out.push(mix(current, next, t));
      }
    }
    return out;
  };

  // Weld by position, so the clipped patch is a connected surface rather than
  // a soup of triangles.
  const welded = new Map();
  const shell = [];
  const keyOf = (p) => `${Math.round(p.x * 1e5)},${Math.round(p.y * 1e5)},${Math.round(p.z * 1e5)}`;
  const place = (p) => {
    const key = keyOf(p);
    const found = welded.get(key);
    if (found !== undefined) {
      // Merge the weight sources; duplicates come from adjacent triangles.
      const target = shell[found];
      for (const [vertex, weight] of p.from) target.from.set(vertex, (target.from.get(vertex) ?? 0) + weight);
      target.merges += 1;
      return found;
    }
    const slot = shell.length;
    shell.push({ ...p, merges: 1 });
    welded.set(key, slot);
    return slot;
  };

  const triangles = [];
  for (let corner = 0; corner < index.count; corner += 3) {
    const set = [index.data[corner], index.data[corner + 1], index.data[corner + 2]];
    if (!set.every((vertex) => onBody[vertex])) continue;
    let polygon = set.map(point);
    polygon = clip(polygon, true, WAIST_Y);
    if (polygon.length < 3) continue;
    polygon = clip(polygon, false, HEM_Y);
    if (polygon.length < 3) continue;
    const placed = polygon.map(place);
    for (let fan = 1; fan + 1 < placed.length; fan += 1) {
      const set1 = [placed[0], placed[fan], placed[fan + 1]];
      // A clip can leave a slither with two corners welded onto one; those
      // render as stray specks, so they are dropped rather than kept.
      if (set1[0] === set1[1] || set1[1] === set1[2] || set1[0] === set1[2]) continue;
      triangles.push(set1);
    }
  }

  for (const vertex of shell) {
    const total = [...vertex.from.values()].reduce((sum, weight) => sum + weight, 0);
    for (const [key, weight] of vertex.from) vertex.from.set(key, weight / total);
    const length = Math.hypot(vertex.nx, vertex.ny, vertex.nz) || 1;
    vertex.nx /= length;
    vertex.ny /= length;
    vertex.nz /= length;
  }

  /**
   * How far off the skin the cloth sits, and how close it is ever allowed to
   * come. Both tighten through the inseam: offsetting a narrow crease by a full
   * centimetre makes the two sides of it cross, and a garment's crotch seam is
   * close to the body anyway.
   */
  const inseam = shell.map((vertex) => {
    const midline = Math.max(0, Math.min(1, 1 - Math.abs(vertex.x) / 0.075));
    const low = Math.max(0, Math.min(1, (1.005 - vertex.y) / 0.05));
    // The inseam is the part that runs *between the legs*, so it has to be
    // gated on depth as well as height. Defined by height alone it also claims
    // the lower front, where its deliberately tight 3.5 mm standoff shrink-wraps
    // the anatomy — which is the pronounced shape at the front of the garment.
    const between = Math.max(0, Math.min(1, (INSEAM_FRONT - vertex.z) / 0.04));
    return midline * low * between;
  });
  /** The front panel mask, shared by the offset and the flattening pass. */
  const pouch = shell.map((vertex) => {
    const midline = Math.max(0, 1 - Math.abs(vertex.x) / POUCH_WIDTH);
    const above = Math.max(0, Math.min(1, (vertex.y - POUCH_LOW) / 0.05));
    const below = Math.max(0, Math.min(1, (1.135 - vertex.y) / 0.05));
    const front = Math.max(0, Math.min(1, (vertex.z - 0.005) / 0.03));
    return Math.min(1, midline * above * below * front * POUCH_GAIN);
  });
  const offsetAt = (slot) => {
    const base = OFFSET * (1 - inseam[slot]) + INSEAM_OFFSET * inseam[slot];
    return base * (1 - pouch[slot]) + FRONT_OFFSET * pouch[slot];
  };
  const clearanceAt = (slot) => {
    const base = MIN_CLEARANCE * (1 - inseam[slot]) + INSEAM_CLEARANCE * inseam[slot];
    return base * (1 - pouch[slot]) + FRONT_CLEARANCE * pouch[slot];
  };

  // The garment surface, lifted off the skin.
  const outer = shell.map((vertex, slot) => ({
    x: vertex.x + vertex.nx * offsetAt(slot),
    y: vertex.y + vertex.ny * offsetAt(slot),
    z: vertex.z + vertex.nz * offsetAt(slot),
  }));

  // Neighbourhood, for smoothing.
  const neighbours = shell.map(() => new Set());
  for (const [a, b, c] of triangles) {
    neighbours[a].add(b); neighbours[a].add(c);
    neighbours[b].add(a); neighbours[b].add(c);
    neighbours[c].add(a); neighbours[c].add(b);
  }

  // Boundary vertices are pinned: the waistband and the hems should stay where
  // they were cut rather than creeping up the body.
  const edgeUse = new Map();
  /** Each edge as its triangle actually traverses it, for the rim's winding. */
  const boundaryEdges = new Map();
  for (const [a, b, c] of triangles) {
    for (const [one, two] of [[a, b], [b, c], [c, a]]) {
      const key = one < two ? `${one}:${two}` : `${two}:${one}`;
      edgeUse.set(key, (edgeUse.get(key) ?? 0) + 1);
      if (!boundaryEdges.has(key)) boundaryEdges.set(key, [one, two]);
    }
  }
  const boundary = new Uint8Array(shell.length);
  for (const [key, uses] of edgeUse) {
    if (uses !== 1) continue;
    const [one, two] = key.split(':').map(Number);
    boundary[one] = 1;
    boundary[two] = 1;
  }

  /**
   * How much a vertex should be allowed to relax. Shorts hang smoothly across
   * the groin instead of wrapping it, so the midline front and the inner thighs
   * relax most; over the hips and seat the garment follows the body and barely
   * moves at all.
   */
  // A band across the front of the pelvis, fading out before the inseam so the
  // cloth still drops between the legs instead of being pulled up flat.
  const relaxation = pouch;

  for (let pass = 0; pass < SMOOTH_PASSES; pass += 1) {
    const next = outer.map((value) => ({ ...value }));
    for (let slot = 0; slot < shell.length; slot += 1) {
      if (boundary[slot]) continue;
      const amount = relaxation[slot];
      if (amount <= 0) continue;
      let sx = 0;
      let sy = 0;
      let sz = 0;
      let seen = 0;
      for (const other of neighbours[slot]) {
        sx += outer[other].x;
        sy += outer[other].y;
        sz += outer[other].z;
        seen += 1;
      }
      if (!seen) continue;
      const lambda = 0.55 * amount;
      next[slot].x += ((sx / seen) - outer[slot].x) * lambda;
      next[slot].y += ((sy / seen) - outer[slot].y) * lambda;
      next[slot].z += ((sz / seen) - outer[slot].z) * lambda;
    }
    // Smoothing must never pull the garment into the body.
    for (let slot = 0; slot < shell.length; slot += 1) {
      const skinPoint = shell[slot];
      const dx = next[slot].x - skinPoint.x;
      const dy = next[slot].y - skinPoint.y;
      const dz = next[slot].z - skinPoint.z;
      const along = dx * skinPoint.nx + dy * skinPoint.ny + dz * skinPoint.nz;
      const floor1 = clearanceAt(slot);
      if (along >= floor1) {
        outer[slot] = next[slot];
        continue;
      }
      const push = floor1 - along;
      outer[slot] = {
        x: next[slot].x + skinPoint.nx * push,
        y: next[slot].y + skinPoint.ny * push,
        z: next[slot].z + skinPoint.nz * push,
      };
    }
  }

  // Shorts hang across the groin rather than wrapping it, and the one thing
  // that cannot be given up is that the cloth stays outside the body. So this
  // pass relaxes the front panel but only ever accepts a move that takes a
  // vertex *further* from the skin: the apex of any protrusion therefore stays
  // put while everything around it rises to meet it, which flattens the panel
  // into something a garment would do and can never introduce a poke-through.
  for (let pass = 0; pass < OUTWARD_PASSES; pass += 1) {
    const next = outer.map((value) => ({ ...value }));
    for (let slot = 0; slot < shell.length; slot += 1) {
      if (boundary[slot] || relaxation[slot] <= 0) continue;
      let sx = 0;
      let sy = 0;
      let sz = 0;
      let seen = 0;
      for (const other of neighbours[slot]) {
        sx += outer[other].x;
        sy += outer[other].y;
        sz += outer[other].z;
        seen += 1;
      }
      if (!seen) continue;
      const lambda = 0.6 * relaxation[slot];
      const candidate = {
        x: outer[slot].x + ((sx / seen) - outer[slot].x) * lambda,
        y: outer[slot].y + ((sy / seen) - outer[slot].y) * lambda,
        z: outer[slot].z + ((sz / seen) - outer[slot].z) * lambda,
      };
      const skinPoint = shell[slot];
      const reach = (point1) =>
        (point1.x - skinPoint.x) * skinPoint.nx +
        (point1.y - skinPoint.y) * skinPoint.ny +
        (point1.z - skinPoint.z) * skinPoint.nz;
      if (reach(candidate) >= reach(outer[slot])) next[slot] = candidate;
    }
    for (let slot = 0; slot < shell.length; slot += 1) outer[slot] = next[slot];
  }

  // Outward normals of the finished garment surface.
  const shellNormal = outer.map(() => ({ x: 0, y: 0, z: 0 }));
  for (const [a, b, c] of triangles) {
    const ux = outer[b].x - outer[a].x;
    const uy = outer[b].y - outer[a].y;
    const uz = outer[b].z - outer[a].z;
    const vx = outer[c].x - outer[a].x;
    const vy = outer[c].y - outer[a].y;
    const vz = outer[c].z - outer[a].z;
    const nx = uy * vz - uz * vy;
    const ny = uz * vx - ux * vz;
    const nz = ux * vy - uy * vx;
    for (const slot of [a, b, c]) {
      shellNormal[slot].x += nx;
      shellNormal[slot].y += ny;
      shellNormal[slot].z += nz;
    }
  }
  for (let slot = 0; slot < shellNormal.length; slot += 1) {
    const n = shellNormal[slot];
    const length = Math.hypot(n.x, n.y, n.z) || 1;
    n.x /= length;
    n.y /= length;
    n.z /= length;
    // Keep the winding-derived normal pointing away from the skin.
    const skinPoint = shell[slot];
    if (n.x * skinPoint.nx + n.y * skinPoint.ny + n.z * skinPoint.nz < 0) {
      n.x = -n.x;
      n.y = -n.y;
      n.z = -n.z;
    }
  }

  // The garment has two faces and an edge, so it reads as cloth and not as a
  // sheet of paper: an outer surface, a lining just off the skin, and a rim
  // closing them at the waistband and both hems.
  const inner = outer.map((value, slot) => {
    const n = shellNormal[slot];
    const skinPoint = shell[slot];
    const candidate = {
      x: value.x - n.x * FABRIC,
      y: value.y - n.y * FABRIC,
      z: value.z - n.z * FABRIC,
    };
    const along =
      (candidate.x - skinPoint.x) * skinPoint.nx +
      (candidate.y - skinPoint.y) * skinPoint.ny +
      (candidate.z - skinPoint.z) * skinPoint.nz;
    const floor = clearanceAt(slot) * 0.7;
    if (along >= floor) return candidate;
    const push = floor - along;
    return {
      x: candidate.x + skinPoint.nx * push,
      y: candidate.y + skinPoint.ny * push,
      z: candidate.z + skinPoint.nz * push,
    };
  });

  const vertices = [];
  const outIndices = [];
  const pushVertex = (place1, normalVector, source) => {
    vertices.push({ position: place1, normal: normalVector, from: source });
    return vertices.length - 1;
  };

  const outerSlot = outer.map((value, slot) => pushVertex(value, shellNormal[slot], shell[slot].from));
  const innerSlot = inner.map((value, slot) =>
    pushVertex(
      value,
      { x: -shellNormal[slot].x, y: -shellNormal[slot].y, z: -shellNormal[slot].z },
      shell[slot].from,
    ),
  );

  for (const [a, b, c] of triangles) {
    outIndices.push(outerSlot[a], outerSlot[b], outerSlot[c]);
    outIndices.push(innerSlot[a], innerSlot[c], innerSlot[b]);
  }
  // The hem and waistband edge. The winding has to come from the direction the
  // edge runs in its own triangle, not from the sorted key the edge was stored
  // under: half of the rim faces the other way if it does, and single-sided
  // rendering culls every second one, which reads as a sawtooth along the
  // waistband exactly where the garment is seen edge-on.
  for (const [key, oriented] of boundaryEdges) {
    if (edgeUse.get(key) !== 1) continue;
    const [one, two] = oriented;
    outIndices.push(outerSlot[one], outerSlot[two], innerSlot[two]);
    outIndices.push(outerSlot[one], innerSlot[two], innerSlot[one]);
  }

  // Skin weights, inherited from the body surface each vertex came from.
  const jointData = new Uint16Array(vertices.length * 4);
  const weightData = new Float32Array(vertices.length * 4);
  const boneTally = new Map();
  vertices.forEach((vertex, slot) => {
    const pool = new Map();
    for (const [bodyVertex, share] of vertex.from) {
      for (let lane = 0; lane < skin.slots; lane += 1) {
        const at = bodyVertex * skin.slots + lane;
        const weight = skin.weights[at] * share;
        if (weight <= 0) continue;
        const joint = skin.joints[at];
        pool.set(joint, (pool.get(joint) ?? 0) + weight);
      }
    }
    const lanes = [...pool].sort((one, two) => two[1] - one[1]).slice(0, 4);
    const total = lanes.reduce((sum, [, weight]) => sum + weight, 0) || 1;
    lanes.forEach(([joint, weight], lane) => {
      jointData[slot * 4 + lane] = joint;
      weightData[slot * 4 + lane] = weight / total;
      boneTally.set(names[joint], (boneTally.get(names[joint]) ?? 0) + weight / total);
    });
  });

  // ---- write it into the file -------------------------------------------
  const chunks = [];
  let offset = glb.bin.length;
  const addView = (typed) => {
    const bytes = Buffer.from(typed.buffer, typed.byteOffset, typed.byteLength);
    const pad = (4 - (offset % 4)) % 4;
    if (pad) {
      chunks.push(Buffer.alloc(pad, 0));
      offset += pad;
    }
    glb.json.bufferViews.push({ buffer: 0, byteOffset: offset, byteLength: bytes.length });
    chunks.push(bytes);
    offset += bytes.length;
    return glb.json.bufferViews.length - 1;
  };
  const addAccessor = (view, componentType, type, countOf, extra = {}) => {
    glb.json.accessors.push({ bufferView: view, componentType, count: countOf, type, ...extra });
    return glb.json.accessors.length - 1;
  };

  const positionData = new Float32Array(vertices.length * 3);
  const normalData = new Float32Array(vertices.length * 3);
  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];
  vertices.forEach((vertex, slot) => {
    const values = [vertex.position.x, vertex.position.y, vertex.position.z];
    values.forEach((value, axis) => {
      positionData[slot * 3 + axis] = value;
      min[axis] = Math.min(min[axis], value);
      max[axis] = Math.max(max[axis], value);
    });
    normalData[slot * 3] = vertex.normal.x;
    normalData[slot * 3 + 1] = vertex.normal.y;
    normalData[slot * 3 + 2] = vertex.normal.z;
  });
  const indexData = new Uint32Array(outIndices);
  const colourData = new Uint16Array(vertices.length * 4);
  for (let slot = 0; slot < vertices.length; slot += 1) {
    colourData[slot * 4] = Math.round(CLOTH[0] * 65535);
    colourData[slot * 4 + 1] = Math.round(CLOTH[1] * 65535);
    colourData[slot * 4 + 2] = Math.round(CLOTH[2] * 65535);
    colourData[slot * 4 + 3] = 65535;
  }

  const positionAccessor = addAccessor(addView(positionData), 5126, 'VEC3', vertices.length, { min, max });
  const normalAccessor = addAccessor(addView(normalData), 5126, 'VEC3', vertices.length);
  const jointAccessor = addAccessor(addView(jointData), 5123, 'VEC4', vertices.length);
  const weightAccessor = addAccessor(addView(weightData), 5126, 'VEC4', vertices.length);
  const indexAccessor = addAccessor(addView(indexData), 5125, 'SCALAR', indexData.length);
  const colourAccessor = addAccessor(addView(colourData), 5123, 'VEC4', vertices.length, {
    normalized: true,
  });

  glb.bin = Buffer.concat([glb.bin, ...chunks]);
  glb.json.buffers[0].byteLength = glb.bin.length;

  glb.json.materials = glb.json.materials ?? [];
  glb.json.materials.push({
    name: 'HomeGymPT_Shorts',
    doubleSided: false,
    pbrMetallicRoughness: {
      baseColorFactor: [0.13, 0.135, 0.145, 1],
      metallicFactor: 0,
      roughnessFactor: 0.94,
    },
  });
  const material = glb.json.materials.length - 1;

  glb.json.meshes.push({
    name: 'HomeGymPT_Shorts',
    primitives: [
      {
        attributes: {
          POSITION: positionAccessor,
          NORMAL: normalAccessor,
          COLOR_0: colourAccessor,
          JOINTS_0: jointAccessor,
          WEIGHTS_0: weightAccessor,
        },
        indices: indexAccessor,
        material,
      },
    ],
  });
  const mesh = glb.json.meshes.length - 1;

  const bodyNode = glb.json.nodes.findIndex((node) => node.mesh === 0);
  glb.json.nodes.push({
    name: 'HomeGymPT_Shorts',
    mesh,
    skin: glb.json.nodes[bodyNode].skin,
    matrix: glb.json.nodes[bodyNode].matrix ?? [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
  });
  const node = glb.json.nodes.length - 1;

  const parent = glb.json.nodes.findIndex((entry) => (entry.children ?? []).includes(bodyNode));
  if (parent >= 0) glb.json.nodes[parent].children.push(node);
  else glb.json.scenes[0].nodes.push(node);

  glb.json.asset.extras = {
    ...(glb.json.asset.extras ?? {}),
    shorts: {
      base: inputPath.split('/').pop(),
      waistY: WAIST_Y,
      hemY: HEM_Y,
      offset: OFFSET,
      fabric: FABRIC,
      minClearance: MIN_CLEARANCE,
      inseamOffset: INSEAM_OFFSET,
      inseamClearance: INSEAM_CLEARANCE,
      frontOffset: FRONT_OFFSET,
      frontClearance: FRONT_CLEARANCE,
      pouchWidth: POUCH_WIDTH,
      pouchGain: POUCH_GAIN,
      pouchLow: POUCH_LOW,
      inseamFront: INSEAM_FRONT,
      clothColourLinear: CLOTH,
      note: 'Separate skinned clothing mesh; body mesh, weights and skeleton unchanged',
    },
  };

  const bytes = writeGlb(glb, outputPath);
  // Which body surface point each garment vertex was lifted from. A clearance
  // check needs this to know where the skin is under the cloth in a given pose.
  writeFileSync(
    `${outputPath}.correspondence.json`,
    JSON.stringify(vertices.map((vertex) => [...vertex.from])),
  );
  return {
    vertices: vertices.length,
    triangles: outIndices.length / 3,
    shellVertices: shell.length,
    shellTriangles: triangles.length,
    boundaryVertices: [...boundary].filter(Boolean).length,
    bones: [...boneTally].sort((one, two) => two[1] - one[1]),
    bytes,
    span: { min, max },
  };
}

if (process.argv[2] && process.argv[3]) {
  const result = buildShorts(process.argv[2], process.argv[3]);
  console.log(
    `shorts: ${result.vertices} vertices, ${result.triangles} triangles ` +
      `(shell ${result.shellVertices}/${result.shellTriangles}, ${result.boundaryVertices} boundary), wrote ${result.bytes} bytes`,
  );
  console.log(`span y ${result.span.min[1].toFixed(3)} .. ${result.span.max[1].toFixed(3)}`);
  console.log('bones influencing the shorts:');
  for (const [name, share] of result.bones) {
    console.log(`  ${name.padEnd(20)} ${share.toFixed(1)}`);
  }
}
