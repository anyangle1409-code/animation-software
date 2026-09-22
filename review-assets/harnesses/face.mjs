// Head measurements in the model's bind pose: widths up the skull, jaw and chin
// shape, cheekbone projection. Reported so a face change can be aimed.
import { body, relief } from './torso.mjs';
const m = body(process.argv[2]);
const { pos } = m;

const isHead = (v) => m.weightOn(v, (n) => /^(spine\.006|jaw|chin|cheek|temple|forehead|nose|lip|brow|lid|ear|tongue|teeth|eye)/.test(n)) > 0.5;
let n = 0, lo = [9, 9, 9], hi = [-9, -9, -9];
for (let v = 0; v < pos.count; v += 1) {
  if (!isHead(v)) continue;
  n += 1;
  for (let c = 0; c < 3; c += 1) { lo[c] = Math.min(lo[c], pos.data[v*3+c]); hi[c] = Math.max(hi[c], pos.data[v*3+c]); }
}
console.log(`head vertices ${n}`);
console.log(`  x ${(lo[0]*1000).toFixed(0)}..${(hi[0]*1000).toFixed(0)}  y ${(lo[1]*1000).toFixed(0)}..${(hi[1]*1000).toFixed(0)}  z ${(lo[2]*1000).toFixed(0)}..${(hi[2]*1000).toFixed(0)} mm`);

console.log('\nhalf-width and forward reach up the head (head-owned only):');
for (let y = 1.64; y <= 1.98; y += 0.02) {
  let w = 0, zf = -9, zb = 9, c = 0;
  for (let v = 0; v < pos.count; v += 1) {
    if (!isHead(v)) continue;
    const yy = pos.data[v*3+1];
    if (yy < y - 0.01 || yy >= y + 0.01) continue;
    c += 1;
    w = Math.max(w, Math.abs(pos.data[v*3]));
    zf = Math.max(zf, pos.data[v*3+2]);
    zb = Math.min(zb, pos.data[v*3+2]);
  }
  if (!c) continue;
  console.log(`  y ${y.toFixed(2)}  half-width ${(w*1000).toFixed(1).padStart(5)} mm  front z ${(zf*1000).toFixed(0).padStart(4)}  back z ${(zb*1000).toFixed(0).padStart(4)}  (${c})`);
}

// Jaw squareness: how much of the jaw's width is held all the way to the chin.
console.log('\njaw line, left side (widest |x| per height, mandible-owned):');
for (let y = 1.66; y <= 1.80; y += 0.02) {
  let w = 0, c = 0, zAt = 0;
  for (let v = 0; v < pos.count; v += 1) {
    const yy = pos.data[v*3+1];
    if (yy < y - 0.01 || yy >= y + 0.01 || pos.data[v*3] < 0) continue;
    if (m.weightOn(v, (k) => /^(jaw|chin|cheek\.B)/.test(k)) < 0.3) continue;
    c += 1;
    if (pos.data[v*3] > w) { w = pos.data[v*3]; zAt = pos.data[v*3+2]; }
  }
  if (c) console.log(`  y ${y.toFixed(2)}  jaw half-width ${(w*1000).toFixed(1).padStart(5)} mm at z ${(zAt*1000).toFixed(0)}  (${c})`);
}

// Chin front: a blocky chin holds nearly the same z across a wide band of x.
console.log('\nchin front profile (z at each |x|, y 1.67-1.71):');
for (let x = 0; x <= 0.05; x += 0.01) {
  let zf = -9, c = 0;
  for (let v = 0; v < pos.count; v += 1) {
    const xx = Math.abs(pos.data[v*3]), yy = pos.data[v*3+1];
    if (yy < 1.67 || yy > 1.71 || xx < x - 0.005 || xx >= x + 0.005) continue;
    if (m.weightOn(v, (k) => /^(chin|jaw)/.test(k)) < 0.3) continue;
    c += 1; zf = Math.max(zf, pos.data[v*3+2]);
  }
  if (c) console.log(`  |x| ${(x*1000).toFixed(0).padStart(2)} mm  front z ${(zf*1000).toFixed(1).padStart(5)} mm  (${c})`);
}

// Cheekbone: where the mid-face is widest and how far forward it sits.
console.log('\nmid-face, left (cheek/temple-owned):');
for (let y = 1.78; y <= 1.90; y += 0.02) {
  let w = 0, zAt = 0, c = 0;
  for (let v = 0; v < pos.count; v += 1) {
    const yy = pos.data[v*3+1];
    if (yy < y - 0.01 || yy >= y + 0.01 || pos.data[v*3] < 0) continue;
    if (m.weightOn(v, (k) => /^(cheek|temple|nose|lid)/.test(k)) < 0.3) continue;
    c += 1;
    if (pos.data[v*3] > w) { w = pos.data[v*3]; zAt = pos.data[v*3+2]; }
  }
  if (c) console.log(`  y ${y.toFixed(2)}  widest ${(w*1000).toFixed(1).padStart(5)} mm at z ${(zAt*1000).toFixed(0)}  (${c})`);
}
// where does the head hand over to the neck?
console.log('\nhandover to neck (neck weight by height):');
for (let y = 1.60; y <= 1.74; y += 0.02) {
  let neck = 0, c = 0;
  for (let v = 0; v < pos.count; v += 1) {
    const yy = pos.data[v*3+1];
    if (yy < y - 0.01 || yy >= y + 0.01) continue;
    c += 1;
    neck += m.weightOn(v, (k) => /^spine\.00[45]$/.test(k));
  }
  if (c) console.log(`  y ${y.toFixed(2)}  mean neck weight ${(neck/c).toFixed(3)}  (${c} verts)`);
}
