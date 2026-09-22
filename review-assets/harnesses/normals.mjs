// Diagnose (and optionally repair) normal/smoothing discontinuity on a body GLB.
//
// Two separate questions, kept separate on purpose:
//   1. do co-located vertices disagree on their normal (a shading seam)?
//   2. do the stored normals agree with the geometry's own smooth normals?
// Neither question touches positions, topology, weights or the skeleton.
import { readGlb, accessorView, writeGlb } from './glb.mjs';

export function analyse(path) {
  const glb = readGlb(path);
  const prim = glb.json.meshes[0].primitives[0];
  const pos = accessorView(glb, prim.attributes.POSITION);
  const nor = accessorView(glb, prim.attributes.NORMAL);
  const idx = accessorView(glb, prim.indices);
  const names = glb.json.skins[0].joints.map((n) => glb.json.nodes[n].name);
  const jointSets = [];
  const weightSets = [];
  for (let s = 0; prim.attributes[`JOINTS_${s}`] !== undefined; s += 1) {
    jointSets.push(accessorView(glb, prim.attributes[`JOINTS_${s}`]));
    weightSets.push(accessorView(glb, prim.attributes[`WEIGHTS_${s}`]));
  }
  const dominant = (v) => {
    let best = -1;
    let bw = -1;
    for (let s = 0; s < jointSets.length; s += 1) {
      for (let l = 0; l < 4; l += 1) {
        const w = weightSets[s].data[v * 4 + l];
        if (w > bw) { bw = w; best = jointSets[s].data[v * 4 + l]; }
      }
    }
    return (names[best] ?? '?').replace(/^DEF-/, '');
  };

  // Co-located groups, keyed on the exact stored float triple.
  const groups = new Map();
  for (let v = 0; v < pos.count; v += 1) {
    const key = `${pos.data[v * 3]},${pos.data[v * 3 + 1]},${pos.data[v * 3 + 2]}`;
    const list = groups.get(key);
    if (list) list.push(v); else groups.set(key, [v]);
  }

  // Angle-weighted smooth normals, accumulated across a whole co-located group
  // so a seam's two sides agree — this is the normal the geometry implies.
  const smooth = new Float64Array(pos.count * 3);
  const groupOf = new Map();
  for (const [, list] of groups) for (const v of list) groupOf.set(v, list);
  const accumulate = (v, x, y, z) => {
    for (const other of groupOf.get(v)) {
      smooth[other * 3] += x;
      smooth[other * 3 + 1] += y;
      smooth[other * 3 + 2] += z;
    }
  };
  for (let t = 0; t < idx.count; t += 3) {
    const a = idx.data[t], b = idx.data[t + 1], c = idx.data[t + 2];
    const ax = pos.data[a * 3], ay = pos.data[a * 3 + 1], az = pos.data[a * 3 + 2];
    const bx = pos.data[b * 3], by = pos.data[b * 3 + 1], bz = pos.data[b * 3 + 2];
    const cx = pos.data[c * 3], cy = pos.data[c * 3 + 1], cz = pos.data[c * 3 + 2];
    const ux = bx - ax, uy = by - ay, uz = bz - az;
    const vx = cx - ax, vy = cy - ay, vz = cz - az;
    // Cross product magnitude is twice the triangle area, so an unnormalised
    // face normal is already area-weighted.
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    accumulate(a, nx, ny, nz);
    accumulate(b, nx, ny, nz);
    accumulate(c, nx, ny, nz);
  }
  for (let v = 0; v < pos.count; v += 1) {
    const l = Math.hypot(smooth[v * 3], smooth[v * 3 + 1], smooth[v * 3 + 2]);
    if (l > 0) { smooth[v * 3] /= l; smooth[v * 3 + 1] /= l; smooth[v * 3 + 2] /= l; }
  }

  const angleTo = (v, arr) => {
    const d = nor.data[v * 3] * arr[v * 3] + nor.data[v * 3 + 1] * arr[v * 3 + 1] + nor.data[v * 3 + 2] * arr[v * 3 + 2];
    return Math.acos(Math.max(-1, Math.min(1, d))) * 180 / Math.PI;
  };

  // 1. seams: co-located vertices whose stored normals disagree
  let seamGroups = 0;
  let seamVertices = 0;
  let worstSeam = 0;
  const seamByBone = new Map();
  const seamMembers = [];
  for (const [, list] of groups) {
    if (list.length < 2) continue;
    let worst = 0;
    for (let a = 0; a < list.length; a += 1) {
      for (let b = a + 1; b < list.length; b += 1) {
        const ia = list[a], ib = list[b];
        const d = nor.data[ia * 3] * nor.data[ib * 3] + nor.data[ia * 3 + 1] * nor.data[ib * 3 + 1] + nor.data[ia * 3 + 2] * nor.data[ib * 3 + 2];
        const ang = Math.acos(Math.max(-1, Math.min(1, d))) * 180 / Math.PI;
        if (ang > worst) worst = ang;
      }
    }
    if (worst <= 5) continue;
    seamGroups += 1;
    seamVertices += list.length;
    if (worst > worstSeam) worstSeam = worst;
    const bone = dominant(list[0]);
    seamByBone.set(bone, (seamByBone.get(bone) ?? 0) + 1);
    seamMembers.push(list);
  }

  // 2. stored vs the geometry's own smooth normal
  let worstDeviation = 0;
  let over15 = 0;
  let over45 = 0;
  const devByBone = new Map();
  for (let v = 0; v < pos.count; v += 1) {
    const ang = angleTo(v, smooth);
    if (ang > worstDeviation) worstDeviation = ang;
    if (ang > 15) {
      over15 += 1;
      const bone = dominant(v);
      devByBone.set(bone, (devByBone.get(bone) ?? 0) + 1);
    }
    if (ang > 45) over45 += 1;
  }

  return { glb, prim, pos, nor, idx, groups, smooth, dominant,
    seamGroups, seamVertices, worstSeam, seamByBone, seamMembers,
    worstDeviation, over15, over45, devByBone };
}

if (process.argv[1] && process.argv[1].endsWith('normals.mjs')) {
  for (const path of process.argv.slice(2)) {
    const r = analyse(path);
    const top = (m) => [...m].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, v]) => `${k}:${v}`).join(' ');
    console.log(path.split('/').pop());
    console.log(`  vertices ${r.pos.count}  triangles ${r.idx.count / 3}  co-located groups ${[...r.groups.values()].filter((l) => l.length > 1).length}`);
    console.log(`  SEAMS  groups ${r.seamGroups}  vertices ${r.seamVertices}  worst ${r.worstSeam.toFixed(1)}deg`);
    console.log(`         ${top(r.seamByBone)}`);
    console.log(`  VS GEOMETRY  worst deviation ${r.worstDeviation.toFixed(1)}deg  over15 ${r.over15}  over45 ${r.over45}`);
    console.log(`         ${top(r.devByBone)}`);
  }
}
