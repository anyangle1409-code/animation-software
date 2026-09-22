// Local one-ring weight redistribution at the hand's two handover rings.
//
// The defect is a weight *gradient*, not a shape: at the finger-base and wrist
// rings the influence hands over from one bone to the next across a single
// edge — in places from 0.28 straight to 1.00 — so when the joint bends, two
// neighbouring vertices travel on entirely different arcs and the triangle
// between them folds shut.
//
// The repair caps that gradient and nothing else. For each named bone pair it
// works with the vertex's *pooled* weight on the two bones (wA + wB), which it
// never changes, and only moves where the pool sits between them. Total skin
// weight therefore stays exactly 1.0 by construction, no third bone is touched,
// and positions, topology, normals, UVs, the skeleton, the inverse binds and
// the morph targets are not read, let alone written.
//
// Editing is confined to vertices that sit on an over-steep edge or in its
// immediate one-ring neighbourhood; everything outside that band is pinned, so
// the change cannot creep up the forearm or out along the fingers.
import { readGlb, writeGlb, accessorView, readSkin, writeSkin } from './glb.mjs';

const CAP = Number(process.env.CAP ?? 0.45);
const POOL_FLOOR = 0.02;
const ITERATIONS = Number(process.env.ITER ?? 4000);

const pairsFor = (side) => [
  ...['index', 'middle', 'ring', 'pinky'].map((digit) => ({
    label: `mcp-${digit}.${side}`,
    a: `DEF-hand.${side}`,
    b: `DEF-f_${digit}.01.${side}`,
  })),
  { label: `wrist.${side}`, a: `DEF-forearm.${side}.001`, b: `DEF-hand.${side}` },
];

// Same sequence on both sides, so the two hands receive the same treatment.
const PAIRS = [...pairsFor('L'), ...pairsFor('R')];

export function repair(inputPath, outputPath, cap = CAP) {
  const glb = readGlb(inputPath);
  const primitive = glb.json.meshes[0].primitives[0];
  const skin = readSkin(glb, primitive);
  const names = glb.json.skins[0].joints.map((node) => glb.json.nodes[node].name);
  const boneIndex = new Map(names.map((name, index) => [name, index]));
  const index = accessorView(glb, primitive.indices);

  const before = Float32Array.from(skin.weights);

  const neighbours = Array.from({ length: skin.count }, () => new Set());
  for (let triangle = 0; triangle < index.count; triangle += 3) {
    const set = [index.data[triangle], index.data[triangle + 1], index.data[triangle + 2]];
    for (const one of set) for (const two of set) if (one !== two) neighbours[one].add(two);
  }

  const weightOn = (vertex, bone) => {
    let total = 0;
    for (let slot = 0; slot < skin.slots; slot += 1) {
      if (skin.joints[vertex * skin.slots + slot] === bone) total += skin.weights[vertex * skin.slots + slot];
    }
    return total;
  };

  /** Put the vertex's whole weight for one bone into a single lane. */
  const setWeight = (vertex, bone, value) => {
    let home = -1;
    for (let slot = 0; slot < skin.slots; slot += 1) {
      const base = vertex * skin.slots + slot;
      if (skin.joints[base] !== bone) continue;
      if (home < 0) home = base;
      else skin.weights[base] = 0;
    }
    if (home < 0) {
      for (let slot = 0; slot < skin.slots; slot += 1) {
        const base = vertex * skin.slots + slot;
        if (skin.weights[base] === 0) {
          skin.joints[base] = bone;
          home = base;
          break;
        }
      }
    }
    if (home < 0) return false;
    skin.weights[home] = value;
    return true;
  };

  const report = [];

  for (const pair of PAIRS) {
    const a = boneIndex.get(pair.a);
    const b = boneIndex.get(pair.b);
    if (a === undefined || b === undefined) throw new Error(`missing bone in ${pair.label}`);

    const pool = new Float32Array(skin.count);
    const blend = new Float32Array(skin.count).fill(-1);
    for (let vertex = 0; vertex < skin.count; vertex += 1) {
      const wa = weightOn(vertex, a);
      const wb = weightOn(vertex, b);
      const total = wa + wb;
      if (total < POOL_FLOOR) continue;
      pool[vertex] = total;
      blend[vertex] = wb / total;
    }

    // Edges the handover actually crosses, and how steep each one is.
    const edges = [];
    for (let vertex = 0; vertex < skin.count; vertex += 1) {
      if (blend[vertex] < 0) continue;
      for (const other of neighbours[vertex]) {
        if (other <= vertex || blend[other] < 0) continue;
        edges.push([vertex, other]);
      }
    }

    const band = new Set();
    let steepest = 0;
    for (const [one, two] of edges) {
      const jump = Math.abs(blend[one] - blend[two]);
      steepest = Math.max(steepest, jump);
      if (jump <= cap) continue;
      for (const vertex of [one, two]) {
        band.add(vertex);
        // One ring out, and no further.
        for (const other of neighbours[vertex]) if (blend[other] >= 0) band.add(other);
      }
    }

    if (band.size === 0) {
      report.push({ ...pair, steepest, changed: 0, band: 0, after: steepest });
      continue;
    }

    // Project onto "no edge steeper than the cap", moving only band vertices
    // and only by what each violation requires.
    // Jacobi rather than Gauss-Seidel: every correction in a sweep is computed
    // from the same snapshot, so the result does not depend on the order the
    // edges happen to be visited — which is what keeps the left and right hands
    // identical, their vertices being numbered differently.
    const working = Float32Array.from(blend);
    const correction = new Float64Array(skin.count);
    const votes = new Int32Array(skin.count);
    for (let pass = 0; pass < ITERATIONS; pass += 1) {
      correction.fill(0);
      votes.fill(0);
      let worst = 0;
      for (const [one, two] of edges) {
        const difference = working[one] - working[two];
        const magnitude = Math.abs(difference);
        worst = Math.max(worst, magnitude);
        if (magnitude <= cap) continue;
        const excess = magnitude - cap;
        const direction = Math.sign(difference);
        const movableOne = band.has(one);
        const movableTwo = band.has(two);
        if (!movableOne && !movableTwo) continue;
        const share = movableOne && movableTwo ? excess / 2 : excess;
        if (movableOne) {
          correction[one] -= direction * share;
          votes[one] += 1;
        }
        if (movableTwo) {
          correction[two] += direction * share;
          votes[two] += 1;
        }
      }
      if (worst <= cap + 1e-6) break;
      for (const vertex of band) {
        if (votes[vertex] === 0) continue;
        working[vertex] = Math.min(
          1,
          Math.max(0, working[vertex] + correction[vertex] / votes[vertex]),
        );
      }
    }

    let changed = 0;
    let largestMove = 0;
    for (const vertex of band) {
      const move = working[vertex] - blend[vertex];
      if (Math.abs(move) < 1e-4) continue;
      changed += 1;
      largestMove = Math.max(largestMove, Math.abs(move));
      const total = pool[vertex];
      if (!setWeight(vertex, a, (1 - working[vertex]) * total)) throw new Error('no free lane');
      if (!setWeight(vertex, b, working[vertex] * total)) throw new Error('no free lane');
    }

    let after = 0;
    for (const [one, two] of edges) {
      const wa = weightOn(one, a) + weightOn(one, b);
      const wb = weightOn(two, a) + weightOn(two, b);
      if (wa < POOL_FLOOR || wb < POOL_FLOOR) continue;
      after = Math.max(after, Math.abs(weightOn(one, b) / wa - weightOn(two, b) / wb));
    }
    report.push({ ...pair, steepest, changed, band: band.size, after, largestMove });
  }

  // Tidy every lane set we touched back into the source's own convention:
  // descending weight, zeros last.
  const touched = new Set();
  for (let vertex = 0; vertex < skin.count; vertex += 1) {
    let differs = false;
    for (let slot = 0; slot < skin.slots; slot += 1) {
      if (Math.abs(before[vertex * skin.slots + slot] - skin.weights[vertex * skin.slots + slot]) > 1e-7) {
        differs = true;
        break;
      }
    }
    if (!differs) continue;
    touched.add(vertex);
    const lanes = [];
    for (let slot = 0; slot < skin.slots; slot += 1) {
      lanes.push({
        joint: skin.joints[vertex * skin.slots + slot],
        weight: skin.weights[vertex * skin.slots + slot],
      });
    }
    const live = lanes.filter((lane) => lane.weight > 0).sort((one, two) => two.weight - one.weight);
    const sum = live.reduce((total, lane) => total + lane.weight, 0);
    for (const lane of live) lane.weight /= sum;
    for (let slot = 0; slot < skin.slots; slot += 1) {
      skin.joints[vertex * skin.slots + slot] = live[slot]?.joint ?? 0;
      skin.weights[vertex * skin.slots + slot] = live[slot]?.weight ?? 0;
    }
  }

  writeSkin(glb, skin);

  glb.json.asset.extras = {
    ...(glb.json.asset.extras ?? {}),
    handWristWeightRepair: {
      base: 'HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb v5',
      scope: 'MCP and wrist handover rings only; weights only',
      gradientCap: cap,
      verticesChanged: touched.size,
    },
  };

  const bytes = writeGlb(glb, outputPath);
  return { report, touched: [...touched].sort((one, two) => one - two), bytes, cap };
}

if (process.argv[2] && process.argv[3]) {
  const result = repair(process.argv[2], process.argv[3]);
  console.log(`cap ${result.cap}  vertices changed ${result.touched.length}  wrote ${result.bytes} bytes`);
  for (const row of result.report) {
    console.log(
      `${row.label.padEnd(16)} steepest ${row.steepest.toFixed(3)} -> ${row.after.toFixed(3)}  band ${String(row.band).padStart(4)}  changed ${String(row.changed).padStart(4)}  largest move ${(row.largestMove ?? 0).toFixed(3)}`,
    );
  }
}
