// Where is the torso surface, and where does it bulge?
// Measured in the model's own bind pose, reported by dominant bone and
// quadrant so a finding can be pointed at rather than just felt.
import { readGlb, accessorView } from './glb.mjs';

export function body(path) {
  const glb = readGlb(path);
  const prim = glb.json.meshes[0].primitives[0];
  const pos = accessorView(glb, prim.attributes.POSITION);
  const nor = accessorView(glb, prim.attributes.NORMAL);
  const idx = accessorView(glb, prim.indices);
  const names = glb.json.skins[0].joints.map((n) => glb.json.nodes[n].name.replace(/^DEF-/, ''));
  const jsets = [], wsets = [];
  for (let s = 0; prim.attributes[`JOINTS_${s}`] !== undefined; s += 1) {
    jsets.push(accessorView(glb, prim.attributes[`JOINTS_${s}`]));
    wsets.push(accessorView(glb, prim.attributes[`WEIGHTS_${s}`]));
  }
  const dominant = (v) => {
    let best = -1, bw = -1;
    for (let s = 0; s < jsets.length; s += 1) for (let l = 0; l < 4; l += 1) {
      const w = wsets[s].data[v * 4 + l];
      if (w > bw) { bw = w; best = jsets[s].data[v * 4 + l]; }
    }
    return names[best] ?? '?';
  };
  const weightOn = (v, test) => {
    let sum = 0;
    for (let s = 0; s < jsets.length; s += 1) for (let l = 0; l < 4; l += 1) {
      const w = wsets[s].data[v * 4 + l];
      if (w > 0 && test(names[jsets[s].data[v * 4 + l]] ?? '')) sum += w;
    }
    return sum;
  };
  const key = (v) => `${pos.data[v*3]},${pos.data[v*3+1]},${pos.data[v*3+2]}`;
  const group = new Map();
  for (let v = 0; v < pos.count; v += 1) { const k = key(v); const l = group.get(k); if (l) l.push(v); else group.set(k, [v]); }
  const near = new Map();
  const link = (a, b) => { const k = key(a); const s = near.get(k) ?? near.set(k, new Set()).get(k); s.add(key(b)); };
  for (let t = 0; t < idx.count; t += 3) {
    const a = idx.data[t], b = idx.data[t+1], c = idx.data[t+2];
    link(a,b); link(b,a); link(b,c); link(c,b); link(c,a); link(a,c);
  }
  return { glb, prim, pos, nor, idx, dominant, weightOn, group, near, key, names };
}

/** Outward height above the local neighbourhood, along the vertex normal, mm. */
export function relief(m) {
  const out = new Map();
  for (const [k, list] of m.group) {
    const v = list[0];
    const ns = m.near.get(k);
    if (!ns || ns.size === 0) { out.set(k, 0); continue; }
    let cx = 0, cy = 0, cz = 0;
    for (const o of ns) { const w = m.group.get(o)[0]; cx += m.pos.data[w*3]; cy += m.pos.data[w*3+1]; cz += m.pos.data[w*3+2]; }
    const n = ns.size;
    out.set(k, ((m.pos.data[v*3] - cx/n) * m.nor.data[v*3]
      + (m.pos.data[v*3+1] - cy/n) * m.nor.data[v*3+1]
      + (m.pos.data[v*3+2] - cz/n) * m.nor.data[v*3+2]) * 1000);
  }
  return out;
}

if (process.argv[1] && process.argv[1].endsWith('torso.mjs')) {
  const cur = body(process.argv[2]);
  const { pos } = cur;
  let lo = [9,9,9], hi = [-9,-9,-9];
  for (let v = 0; v < pos.count; v += 1) for (let k = 0; k < 3; k += 1) {
    lo[k] = Math.min(lo[k], pos.data[v*3+k]); hi[k] = Math.max(hi[k], pos.data[v*3+k]);
  }
  let front = 0;
  for (let v = 0; v < pos.count; v += 1) {
    if (pos.data[v*3+1] < 1.75) continue;
    if (Math.abs(pos.data[v*3+2]) > Math.abs(front)) front = pos.data[v*3+2];
  }
  console.log(`bounds x ${lo[0].toFixed(3)}..${hi[0].toFixed(3)}  y ${lo[1].toFixed(3)}..${hi[1].toFixed(3)}  z ${lo[2].toFixed(3)}..${hi[2].toFixed(3)}`);
  console.log(`front is ${front > 0 ? '+z' : '-z'} (nose z ${front.toFixed(3)})`);
  const FRONT = Math.sign(front);

  const rel = relief(cur);
  const isTorso = (v) => cur.weightOn(v, (n) => /^(spine|breast|pelvis|shoulder)/.test(n)) > 0.5;
  const rows = [];
  for (const [k, list] of cur.group) {
    const v = list[0];
    if (!isTorso(v)) continue;
    rows.push({ v, h: rel.get(k), bone: cur.dominant(v), x: pos.data[v*3], y: pos.data[v*3+1], z: pos.data[v*3+2] });
  }
  rows.sort((a, b) => b.h - a.h);
  console.log(`\ntorso vertices ${rows.length}; biggest outward relief:`);
  for (const r of rows.slice(0, 16)) {
    console.log(`  ${r.h.toFixed(2)} mm  ${r.bone.padEnd(12)} ${r.x > 0 ? 'L' : 'R'} ${(r.z * FRONT > 0 ? 'front' : 'rear').padEnd(5)}  x ${r.x.toFixed(3)} y ${r.y.toFixed(3)} z ${r.z.toFixed(3)}`);
  }
  // Torso half-width by height, so a bulge shows as a step in the profile.
  console.log('\nhalf-width and depth profile up the torso (left side):');
  for (let y = 1.00; y <= 1.60; y += 0.04) {
    let wide = 0, zf = 0, zr = 0, n = 0;
    for (const r of rows) {
      if (r.y < y - 0.02 || r.y >= y + 0.02 || r.x < 0) continue;
      wide = Math.max(wide, r.x); n += 1;
      if (r.z * FRONT > 0) zf = Math.max(zf, r.z * FRONT); else zr = Math.max(zr, -r.z * FRONT);
    }
    if (n === 0) continue;
    console.log(`  y ${y.toFixed(2)}  half-width ${(wide*1000).toFixed(1)} mm  front depth ${(zf*1000).toFixed(1)}  rear depth ${(zr*1000).toFixed(1)}  (${n} verts)`);
  }
}
