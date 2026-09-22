// Upper-body appearance sculpt, in the review's priority order.
//
// Moves body vertex positions only. Topology, skin weights, the skeleton, joint
// matrices, inverse binds, scene extras and the garment are never written. Every
// co-located duplicate moves together, so no vertex pair is split apart and no
// crack appears. Normals are recomputed only where the surface moved, welded
// across UV seams so the Phase A seam repair is not undone, and the groups that
// were intentional hard edges in the reference body are left alone.
import { readGlb, accessorView, writeGlb } from './glb.mjs';

const SRC = process.argv[2];
const REF = process.argv[3];
const OUT = process.argv[4];
const STAGES = (process.env.STAGES ?? '1,2,3').split(',').map((s) => s.trim());

const read = (path) => {
  const glb = readGlb(path);
  const prim = glb.json.meshes[0].primitives[0];
  const names = glb.json.skins[0].joints.map((n) => glb.json.nodes[n].name.replace(/^DEF-/, ''));
  const jsets = [], wsets = [];
  for (let s = 0; prim.attributes[`JOINTS_${s}`] !== undefined; s += 1) {
    jsets.push(accessorView(glb, prim.attributes[`JOINTS_${s}`]));
    wsets.push(accessorView(glb, prim.attributes[`WEIGHTS_${s}`]));
  }
  return { glb, prim, names, jsets, wsets,
    pos: accessorView(glb, prim.attributes.POSITION),
    nor: accessorView(glb, prim.attributes.NORMAL),
    idx: accessorView(glb, prim.indices) };
};

const m = read(SRC);
const { pos, nor, idx } = m;
const weightOn = (v, test) => {
  let sum = 0;
  for (let s = 0; s < m.jsets.length; s += 1) for (let l = 0; l < 4; l += 1) {
    const w = m.wsets[s].data[v * 4 + l];
    if (w > 0 && test(m.names[m.jsets[s].data[v * 4 + l]] ?? '')) sum += w;
  }
  return sum;
};

// Co-located groups and the 1-ring, both keyed on position so a UV seam does not
// cut the surface in half.
const keyAt = (x, y, z) => `${x},${y},${z}`;
const key = (v) => keyAt(pos.data[v * 3], pos.data[v * 3 + 1], pos.data[v * 3 + 2]);
const group = new Map();
for (let v = 0; v < pos.count; v += 1) {
  const k = key(v);
  const l = group.get(k);
  if (l) l.push(v); else group.set(k, [v]);
}
const ring = new Map();
const link = (a, b) => {
  const k = key(a);
  const s = ring.get(k) ?? ring.set(k, new Set()).get(k);
  s.add(key(b));
};
for (let t = 0; t < idx.count; t += 3) {
  const a = idx.data[t], b = idx.data[t + 1], c = idx.data[t + 2];
  link(a, b); link(b, a); link(b, c); link(c, b); link(c, a); link(a, c);
}
const keys = [...group.keys()];
const rep = new Map(keys.map((k) => [k, group.get(k)[0]]));
// The grouping and the 1-ring are keyed on the ORIGINAL positions. Once the
// sculpt writes new positions, key(v) would answer with the new position and
// stop matching them, so each vertex's original key is captured up front.
const originalKey = new Array(pos.count);
for (const k of keys) for (const v of group.get(k)) originalKey[v] = k;
const P = new Map(keys.map((k) => {
  const v = rep.get(k);
  return [k, [pos.data[v * 3], pos.data[v * 3 + 1], pos.data[v * 3 + 2]]];
}));

const smoothstep = (edge0, edge1, x) => {
  const t = Math.min(1, Math.max(0, (x - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
};
// A band that rises from 0 at `lo`, holds 1 between `inA`..`inB`, falls to 0 at `hi`.
const band = (y, lo, inA, inB, hi) => Math.min(smoothstep(lo, inA, y), 1 - smoothstep(inB, hi, y));

const moved = new Set();
const report = [];

/** Laplacian relaxation over a masked region, optionally on selected axes. */
const relax = (mask, iterations, lambda, axes) => {
  for (let it = 0; it < iterations; it += 1) {
    const next = new Map();
    for (const k of keys) {
      const w = mask.get(k) ?? 0;
      if (w <= 0) continue;
      const ns = ring.get(k);
      if (!ns || ns.size === 0) continue;
      const p = P.get(k);
      let cx = 0, cy = 0, cz = 0;
      for (const o of ns) { const q = P.get(o); cx += q[0]; cy += q[1]; cz += q[2]; }
      const n = ns.size;
      const t = w * lambda;
      next.set(k, [
        axes.includes('x') ? p[0] + t * (cx / n - p[0]) : p[0],
        axes.includes('y') ? p[1] + t * (cy / n - p[1]) : p[1],
        axes.includes('z') ? p[2] + t * (cz / n - p[2]) : p[2],
      ]);
    }
    for (const [k, p] of next) { P.set(k, p); moved.add(k); }
  }
};

// ---------------------------------------------------------------- stage 1
// The pec / rear-rib / armpit ripple. One region carries a +22 mm bump on the
// rear and a -17 mm hollow at the front armpit, and that single ripple is what
// reads as the back protrusion, the abrupt armpit and the unclean pec shape.
// Relaxing it addresses all three at once rather than sculpting each by hand.
if (STAGES.includes('1')) {
  const mask = new Map();
  for (const k of keys) {
    const v = rep.get(k);
    const [x, y] = P.get(k);
    const pec = weightOn(v, (n) => /^breast/.test(n));
    const rib = weightOn(v, (n) => /^(spine|shoulder)/.test(n));
    if (pec < 0.15 && rib < 0.5) continue;
    // Vertically feathered over the pec and rib cage only: nothing at the
    // waistband, nothing up into the neck.
    const height = band(y, 1.24, 1.32, 1.50, 1.60);
    // Laterally feathered from the sternum out to the arm.
    const lateral = smoothstep(0.04, 0.11, Math.abs(x));
    const own = Math.max(pec, Math.min(1, rib) * 0.6);
    const w = height * lateral * own;
    if (w > 0.01) mask.set(k, Math.min(1, w));
  }
  relax(mask, 6, 0.55, 'xyz');
  report.push(`stage 1  pec/rib/armpit ripple relaxed over ${mask.size} points`);
}

// ---------------------------------------------------------------- stage 2
// The pointed shoulder in side view. Measured as the radius of curvature of the
// cap's side-view silhouette: the baseline reads 109 mm, i.e. quite peaked, with
// the apex 55 mm behind centre.
//
// Laplacian relaxation is the wrong tool here and measured worse than nothing:
// holding x while relaxing y and z shears the cap, and y alone barely moves a
// convex apex. So this shapes the silhouette directly - it lifts the flanks
// toward a target arc of larger radius, anchored at the same apex height, so the
// cap fills out and rounds without the peak growing. Only y moves, so the
// shoulder span cannot change; the lift is capped so the deltoid cannot inflate.
if (STAGES.includes('2')) {
  const TARGET_R = Number(process.env.CAP_RADIUS ?? 0.16);
  const MAX_LIFT = Number(process.env.CAP_LIFT ?? 0.008);
  const REACH = 0.05; // how far down the cap surface the lift fades out

  for (const side of [1, -1]) {
    // The cap's upper envelope, per z column, on this side.
    const cols = new Map();
    const member = [];
    for (const k of keys) {
      const v = rep.get(k);
      const [x, y, z] = P.get(k);
      if (Math.sign(x) !== side || Math.abs(x) < 0.22 || Math.abs(x) > 0.34 || y < 1.40) continue;
      if (weightOn(v, (n) => /^(upper_arm|shoulder)/.test(n)) < 0.3) continue;
      member.push(k);
      const col = Math.round(z / 0.01);
      cols.set(col, Math.max(cols.get(col) ?? -9, y));
    }
    if (member.length === 0) continue;
    let apexCol = null;
    for (const [col, top] of cols) if (apexCol === null || top > cols.get(apexCol)) apexCol = col;
    const apexY = cols.get(apexCol);
    const apexZ = apexCol * 0.01;
    let lifted = 0, worst = 0;
    for (const k of member) {
      const p = P.get(k);
      const col = Math.round(p[2] / 0.01);
      const top = cols.get(col);
      if (top === undefined || top < -8) continue;
      const dz = p[2] - apexZ;
      const target = apexY - (dz * dz) / (2 * TARGET_R);
      const gap = target - top;
      if (gap <= 0) continue;
      // Only the top of the cap surface moves, fading out downwards, and fading
      // laterally so the join to torso and arm stays smooth.
      const depth = smoothstep(top - REACH, top, p[1]);
      const lateral = smoothstep(0.22, 0.25, Math.abs(p[0])) * (1 - smoothstep(0.31, 0.34, Math.abs(p[0])));
      const lift = Math.min(gap, MAX_LIFT) * depth * lateral;
      if (lift <= 0) continue;
      P.set(k, [p[0], p[1] + lift, p[2]]);
      moved.add(k);
      lifted += 1;
      worst = Math.max(worst, lift);
    }
    report.push(`stage 2  ${side > 0 ? 'left' : 'right'} cap: apex y ${apexY.toFixed(4)} at z ${apexZ.toFixed(3)}, ${lifted} points lifted, max ${(worst * 1000).toFixed(2)} mm, y only`);
  }
}

// ---------------------------------------------------------------- stage 3
// V-taper and obliques. A pure lateral draw-in, above the waistband only, so the
// garment interface is untouched. Depth (z) is left alone, so the ribcage keeps
// its front-to-back volume and only the outline narrows.
if (STAGES.includes('3')) {
  const DRAW = Number(process.env.WAIST_DRAW ?? 0.05);
  let count = 0, worst = 0;
  for (const k of keys) {
    const v = rep.get(k);
    const p = P.get(k);
    const torso = weightOn(v, (n) => /^(spine|breast|pelvis)/.test(n));
    if (torso < 0.5) continue;
    // Zero at and below the waistband top (the shorts reach y 1.177), peak
    // through the true waist, back to zero at the chest.
    const height = band(p[1], 1.19, 1.23, 1.30, 1.40);
    if (height <= 0) continue;
    const shift = p[0] * DRAW * height;
    P.set(k, [p[0] - shift, p[1], p[2]]);
    moved.add(k);
    count += 1;
    worst = Math.max(worst, Math.abs(shift));
  }
  report.push(`stage 3  waist drawn in on ${count} points, max ${(worst * 1000).toFixed(2)} mm per side`);
}

// ---------------------------------------------------------------- stage 4
// Pec shape. The outer pec collapses in depth from 105 mm at y 1.43 to 61 mm at
// y 1.40, and the upper/outer quadrant is dished rather than domed (relief runs
// -4.5 mm concave to only +1.6 mm convex). So this adds two low, smooth domes of
// forward depth - one on the upper/outer pec, one easing the lower/outer
// fall-off - and then eases the boundary contour.
//
// Depth (z) only. The ribcage half-width and the new waist taper are set by x, so
// neither can move. Nothing below y 1.30 is in the mask, so abs and lower torso
// are untouched.
if (STAGES.includes('4')) {
  const dome = (p, cx, cy, rx, ry, amp) => {
    const dx = (Math.abs(p[0]) - cx) / rx;
    const dy = (p[1] - cy) / ry;
    const r = Math.hypot(dx, dy);
    if (r >= 1) return 0;
    // cos^2 profile: zero value AND zero slope at the rim, so no ring shows.
    return amp * Math.cos(r * Math.PI / 2) ** 2;
  };
  let count = 0, worst = 0;
  for (const k of keys) {
    const v = rep.get(k);
    const p = P.get(k);
    const pec = weightOn(v, (n) => /^breast/.test(n));
    if (pec < 0.2) continue;
    // Front surface only, and never the sternum gutter itself.
    if (p[2] <= 0.02 || Math.abs(p[0]) < 0.03) continue;
    const upperOuter = dome(p, 0.175, 1.487, 0.085, 0.070, Number(process.env.PEC_UPPER ?? 0.009));
    const lowerOuter = dome(p, 0.170, 1.397, 0.075, 0.055, Number(process.env.PEC_LOWER ?? 0.007));
    const add = (upperOuter + lowerOuter) * Math.min(1, pec / 0.5);
    if (add <= 0) continue;
    P.set(k, [p[0], p[1], p[2] + add]);
    moved.add(k);
    count += 1;
    worst = Math.max(worst, add);
  }
  // Ease the lower/outer boundary so the new fullness flows into the ribcage
  // instead of ending in a lip.
  const edge = new Map();
  for (const k of keys) {
    const v = rep.get(k);
    const p = P.get(k);
    if (weightOn(v, (n) => /^breast/.test(n)) < 0.15) continue;
    if (p[2] <= 0.0) continue;
    const height = band(p[1], 1.30, 1.34, 1.44, 1.50);
    const lateral = smoothstep(0.10, 0.16, Math.abs(p[0]));
    const w = height * lateral;
    if (w > 0.01) edge.set(k, Math.min(1, w));
  }
  relax(edge, 2, 0.35, 'yz');
  report.push(`stage 4  pec domed on ${count} points, max ${(worst * 1000).toFixed(2)} mm forward; contour eased over ${edge.size} points`);
}

// ---------------------------------------------------------------- stage 5
// The shoulder still reads as a shelf: the clavicle junction stands +7.9 mm
// proud at x 0.10 y 1.62, there is a +6.2 mm ridge on the rear deltoid, and the
// cap's apex sits 55 mm behind centre.
//
// Centring by translating the cap would change the shoulder's depth, so instead
// the cap is re-balanced: the front flank rises and the rear flank drops by the
// same amount, which walks the apex forward without moving mass in z and softens
// the rear ridge at the same time. y only, so span and depth both hold.
if (STAGES.includes('5')) {
  const TILT_SHIFT = Number(process.env.CAP_SHIFT ?? 0.015); // how far forward to walk the apex
  const CAP_R = 0.128; // the round-2 silhouette radius the tilt is computed against
  for (const side of [1, -1]) {
    const member = [];
    const cols = new Map();
    for (const k of keys) {
      const v = rep.get(k);
      const [x, y, z] = P.get(k);
      if (Math.sign(x) !== side || Math.abs(x) < 0.20 || Math.abs(x) > 0.36 || y < 1.44) continue;
      if (weightOn(v, (n) => /^(upper_arm|shoulder)/.test(n)) < 0.25) continue;
      member.push(k);
      const col = Math.round(z / 0.01);
      cols.set(col, Math.max(cols.get(col) ?? -9, y));
    }
    if (!member.length) continue;
    let apexCol = null;
    for (const [col, top] of cols) if (apexCol === null || top > cols.get(apexCol)) apexCol = col;
    const apexZ = apexCol * 0.01;
    // A LINEAR tilt in y against z, not an S-curve. y = apexY - t^2/2R + b*t has
    // the same second derivative as y = apexY - t^2/2R, so the silhouette's
    // curvature is untouched while its apex walks to t = b*R. An S-curve instead
    // puts its steepest gradient at the apex and measured 88 mm of radius against
    // 128 - it sharpens exactly what it is meant to round.
    const tilt = TILT_SHIFT / CAP_R;
    let n = 0, worst = 0;
    for (const k of member) {
      const p = P.get(k);
      const lateral = smoothstep(0.20, 0.24, Math.abs(p[0])) * (1 - smoothstep(0.32, 0.36, Math.abs(p[0])));
      // Fades in below the cap so the tilt does not wrench the deltoid's lower
      // boundary; at the apex height the fade is already 1, so the tilt is pure
      // there and the curvature is preserved where it is measured.
      const vertical = smoothstep(1.40, 1.52, p[1]);
      const shift = tilt * (p[2] - apexZ) * lateral * vertical;
      if (shift === 0) continue;
      P.set(k, [p[0], p[1] + shift, p[2]]);
      moved.add(k);
      n += 1;
      worst = Math.max(worst, Math.abs(shift));
    }
    report.push(`stage 5  ${side > 0 ? 'left' : 'right'} cap tilted about z ${apexZ.toFixed(3)}: ${n} points, max ${(worst * 1000).toFixed(2)} mm, y only`);
  }
  // Soften the clavicle/deltoid junction ridge itself. The lateral mask stops
  // short of the deltoid apex on purpose: reaching out to x 0.38 smoothed the
  // cap itself and cost 25 mm of the silhouette radius won in round 2, which
  // works against the cap reading rounder rather than for it.
  const ridge = new Map();
  for (const k of keys) {
    const v = rep.get(k);
    const p = P.get(k);
    if (weightOn(v, (n) => /^(shoulder|upper_arm)/.test(n)) < 0.25) continue;
    const height = band(p[1], 1.53, 1.58, 1.64, 1.70);
    const lateral = smoothstep(0.06, 0.11, Math.abs(p[0])) * (1 - smoothstep(Number(process.env.RIDGE_OUT ?? 0.19), Number(process.env.RIDGE_OUT ?? 0.19) + 0.06, Math.abs(p[0])));
    const w = height * lateral;
    if (w > 0.01) ridge.set(k, Math.min(1, w));
  }
  relax(ridge, Number(process.env.RIDGE_ITERS ?? 2), 0.35, 'xyz');
  report.push(`stage 5  clavicle/deltoid junction softened over ${ridge.size} points`);
}

// ---------------------------------------------------------------- stage 6
// The outer pec still steps: 67 mm of forward depth at y 1.40 against 107 mm at
// y 1.43, a 40 mm jump over 30 mm of height.
//
// Relaxed rather than filled. A Laplacian on the depth channel redistributes -
// it eases the fuller band back a little and brings the flatter band forward a
// little - so the step smooths without broad chest mass being added. z only, so
// the ribcage half-width and the waist taper cannot move, and the mask starts at
// x 0.13 so the sternum is outside it.
//
// The band stops below the armpit on purpose: the pec/armpit hollow measured
// -6.7 mm at y 1.48 in the last round and is not this round's business.
if (STAGES.includes('6')) {
  const mask = new Map();
  for (const k of keys) {
    const v = rep.get(k);
    const p = P.get(k);
    if (weightOn(v, (n) => /^breast/.test(n)) < 0.2) continue;
    if (p[2] <= 0.02) continue;
    const height = band(p[1], 1.33, 1.37, 1.43, 1.45);
    const lateral = smoothstep(0.13, 0.16, Math.abs(p[0])) * (1 - smoothstep(0.21, 0.25, Math.abs(p[0])));
    const w = height * lateral;
    if (w > 0.01) mask.set(k, Math.min(1, w));
  }
  relax(mask, Number(process.env.STEP_ITERS ?? 5), Number(process.env.STEP_LAMBDA ?? 0.5), 'z');
  report.push(`stage 6  outer-pec depth step relaxed over ${mask.size} points, z only`);
}

// ---------------------------------------------------------------- stage 7
// The lower/outer pec corner, where the chest runs out before the armpit. Over
// the pec's real width the lower band reaches 87-93 mm of forward depth against
// 110-118 mm just above it, so the corner stops short instead of rounding off.
//
// Deliberately modest, because the topology is coarse here: 3-6 vertices per
// 20 mm of height and a 24.9 mm mean edge. A large local add would be carried by
// a handful of points and read as a faceted lump rather than a rounded corner,
// so this adds the minimum a patch this sparse can carry smoothly, over a reach
// wide enough to include the denser band above.
//
// Depth (z) only, front surface only. So the ribcage half-width, the waist and
// the V-taper cannot move, and the rear lat/rib contour is not in the mask at
// all. The band fades out by y 1.47, below the repaired pec/armpit hollow.
if (STAGES.includes('7')) {
  const AMP = Number(process.env.CORNER_AMP ?? 0.009);
  const CX = 0.175, CY = 1.405, RX = 0.065, RY = 0.065;
  let count = 0, worst = 0;
  for (const k of keys) {
    const v = rep.get(k);
    const p = P.get(k);
    if (weightOn(v, (n) => /^breast/.test(n)) < 0.15) continue;
    if (p[2] <= 0.02) continue;
    const dx = (Math.abs(p[0]) - CX) / RX;
    const dy = (p[1] - CY) / RY;
    const r = Math.hypot(dx, dy);
    if (r >= 1) continue;
    // cos^2: zero value and zero slope at the rim, so the addition cannot leave
    // a ring or a lip where it fades out.
    const add = AMP * Math.cos(r * Math.PI / 2) ** 2;
    if (add <= 0) continue;
    P.set(k, [p[0], p[1], p[2] + add]);
    moved.add(k);
    count += 1;
    worst = Math.max(worst, add);
  }
  // A light blend so the new corner flows into the pec above and the flank
  // beside it rather than sitting on top of them.
  const blend = new Map();
  for (const k of keys) {
    const v = rep.get(k);
    const p = P.get(k);
    if (weightOn(v, (n) => /^breast/.test(n)) < 0.1) continue;
    if (p[2] <= 0.0) continue;
    const height = band(p[1], 1.32, 1.36, 1.45, 1.49);
    const lateral = smoothstep(0.09, 0.13, Math.abs(p[0])) * (1 - smoothstep(0.23, 0.27, Math.abs(p[0])));
    const w = height * lateral;
    if (w > 0.01) blend.set(k, Math.min(1, w));
  }
  relax(blend, 2, 0.3, 'z');
  report.push(`stage 7  lower/outer pec corner: ${count} points raised, max ${(worst * 1000).toFixed(2)} mm forward; blended over ${blend.size}`);
}

// ============================================================ face stages
// Head shape only. Every face mask excludes the ears (they set the head's real
// max width and must not move) and excludes neck-weighted vertices, so the neck
// is preserved. Nothing reaches the scalp, so the pre-existing hairline hard
// edge is untouched.
const earWeight = (v) => weightOn(v, (n) => /^ear/.test(n));
const neckWeight = (v) => weightOn(v, (n) => /^spine\.00[45]$/.test(n));
const faceOK = (v) => earWeight(v) <= 0.05 && neckWeight(v) <= 0.35;

// ---------------------------------------------------------------- stage 8
// Taper the jaw. Measured, the jaw holds 74-78 mm of half-width from y 1.70 to
// y 1.78 while the cheekbones above it are only 68-69.5 mm - the face is widest
// at the mandible, which is what reads as heavy and square. This narrows the
// mandible on x alone and fades to nothing by y 1.82, so the cheekbones are not
// narrowed with it and the jaw ends up narrower than the mid-face.
if (STAGES.includes('8')) {
  const DRAW = Number(process.env.JAW_DRAW ?? 0.10);
  let count = 0, worst = 0;
  for (const k of keys) {
    const v = rep.get(k);
    const p = P.get(k);
    if (!faceOK(v)) continue;
    // Full strength across the mandible, out by the cheekbone, out by the neck.
    const height = band(p[1], 1.685, 1.715, 1.775, 1.825);
    if (height <= 0) continue;
    const shift = p[0] * DRAW * height;
    P.set(k, [p[0] - shift, p[1], p[2]]);
    moved.add(k);
    count += 1;
    worst = Math.max(worst, Math.abs(shift));
  }
  report.push(`stage 8  jaw tapered on ${count} points, max ${(worst * 1000).toFixed(2)} mm per side`);
}

// ---------------------------------------------------------------- stage 9
// Round the chin. Its front holds 120-123 mm of projection flat out to |x| = 20
// mm and only falls away past |x| = 30, which is the blocky front. This eases z
// back with increasing |x| so the front rounds, while the centre (|x| under
// 10 mm) keeps its projection so the chin does not recede.
if (STAGES.includes('9')) {
  const AMP = Number(process.env.CHIN_ROUND ?? 0.006);
  let count = 0, worst = 0;
  for (const k of keys) {
    const v = rep.get(k);
    const p = P.get(k);
    if (!faceOK(v) || p[2] <= 0.06) continue;
    const height = band(p[1], 1.700, 1.725, 1.765, 1.800);
    // Zero at the midline, peak across the corner of the chin, zero by the jaw.
    const across = smoothstep(0.010, 0.026, Math.abs(p[0])) * (1 - smoothstep(0.040, 0.058, Math.abs(p[0])));
    const ease = AMP * height * across;
    if (ease <= 0) continue;
    P.set(k, [p[0], p[1], p[2] - ease]);
    moved.add(k);
    count += 1;
    worst = Math.max(worst, ease);
  }
  report.push(`stage 9  chin front rounded on ${count} points, max ${(worst * 1000).toFixed(2)} mm back`);
}

// ---------------------------------------------------------------- stage 10
// Cheekbone and mid-face. A low dome placed on the zygomatic, lateral and
// forward together, so the mid-face gains the structure the jaw taper needs to
// read against. Paired with a slight hollow below it, which is what makes a face
// read lean rather than merely narrow.
if (STAGES.includes('10')) {
  const OUT = Number(process.env.CHEEK_OUT ?? 0.004);
  const FWD = Number(process.env.CHEEK_FWD ?? 0.003);
  const HOLLOW = Number(process.env.CHEEK_HOLLOW ?? 0.0025);
  let cheek = 0, hollow = 0;
  for (const k of keys) {
    const v = rep.get(k);
    const p = P.get(k);
    if (!faceOK(v) || p[2] <= 0.0) continue;
    const dome = (cy, cz, ry, rz) => {
      const dy = (p[1] - cy) / ry, dz = (p[2] - cz) / rz;
      const r = Math.hypot(dy, dz);
      return r >= 1 ? 0 : Math.cos(r * Math.PI / 2) ** 2;
    };
    const side = Math.sign(p[0]) || 1;
    const lateral = smoothstep(0.030, 0.050, Math.abs(p[0]));
    const zyg = dome(1.845, 0.078, 0.030, 0.030) * lateral;
    if (zyg > 0) {
      P.set(k, [p[0] + side * OUT * zyg, p[1], p[2] + FWD * zyg]);
      moved.add(k);
      cheek += 1;
    }
    const buccal = dome(1.790, 0.082, 0.026, 0.028) * lateral;
    if (buccal > 0) {
      const q = P.get(k);
      P.set(k, [q[0] - side * HOLLOW * buccal, q[1], q[2] - HOLLOW * buccal * 0.6]);
      moved.add(k);
      hollow += 1;
    }
  }
  report.push(`stage 10 cheekbone raised on ${cheek} points, cheek hollowed on ${hollow}`);
}

// ---------------------------------------------------------------- stage 11
// The set of the neutral face. Only what is shape rather than eyes or material:
// the brow ridge is eased back a little so it stops overhanging, and the mouth
// line is relaxed so the corners are not held compressed. The lids themselves
// are left alone - a genuinely focused gaze is an eye change, which this round
// excludes.
if (STAGES.includes('11')) {
  const BROW = Number(process.env.BROW_EASE ?? 0.0025);
  const MOUTH = Number(process.env.MOUTH_EASE ?? 0.0015);
  let brow = 0, mouth = 0;
  for (const k of keys) {
    const v = rep.get(k);
    const p = P.get(k);
    if (!faceOK(v) || p[2] <= 0.05) continue;
    const browBand = band(p[1], 1.868, 1.882, 1.898, 1.912) * (1 - smoothstep(0.040, 0.062, Math.abs(p[0])));
    if (browBand > 0) {
      P.set(k, [p[0], p[1], p[2] - BROW * browBand]);
      moved.add(k);
      brow += 1;
    }
    const mouthBand = band(p[1], 1.782, 1.792, 1.806, 1.818) * smoothstep(0.012, 0.024, Math.abs(p[0])) * (1 - smoothstep(0.034, 0.046, Math.abs(p[0])));
    if (mouthBand > 0) {
      const q = P.get(k);
      P.set(k, [q[0], q[1] + MOUTH * mouthBand, q[2]]);
      moved.add(k);
      mouth += 1;
    }
  }
  report.push(`stage 11 brow eased on ${brow} points, mouth corners relaxed on ${mouth}`);
}

// ---------------------------------------------------------------- write back
let maxShift = 0;
for (const k of keys) {
  const p = P.get(k);
  for (const v of group.get(k)) {
    maxShift = Math.max(maxShift, Math.hypot(p[0] - pos.data[v*3], p[1] - pos.data[v*3+1], p[2] - pos.data[v*3+2]));
    pos.data[v * 3] = p[0]; pos.data[v * 3 + 1] = p[1]; pos.data[v * 3 + 2] = p[2];
  }
}
// The accessor's own bounds have to follow the vertices.
const acc = m.glb.json.accessors[m.prim.attributes.POSITION];
const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
for (let v = 0; v < pos.count; v += 1) for (let c = 0; c < 3; c += 1) {
  lo[c] = Math.min(lo[c], pos.data[v*3+c]); hi[c] = Math.max(hi[c], pos.data[v*3+c]);
}
acc.min = lo; acc.max = hi;

// Normals, only where the surface moved plus one ring out, accumulated across
// whole co-located groups so both sides of a seam agree.
const dirty = new Set();
for (const k of moved) { dirty.add(k); for (const o of ring.get(k) ?? []) dirty.add(o); }
const ref = read(REF);
const refKey = (v) => keyAt(ref.pos.data[v*3], ref.pos.data[v*3+1], ref.pos.data[v*3+2]);
const refGroups = new Map();
for (let v = 0; v < ref.pos.count; v += 1) {
  const k = refKey(v);
  const l = refGroups.get(k);
  if (l) l.push(v); else refGroups.set(k, [v]);
}
const hardEdge = new Set();
for (const [, list] of refGroups) {
  if (list.length < 2) continue;
  let worstAngle = 0;
  for (let a = 0; a < list.length; a += 1) for (let b = a + 1; b < list.length; b += 1) {
    const d = ref.nor.data[list[a]*3]*ref.nor.data[list[b]*3] + ref.nor.data[list[a]*3+1]*ref.nor.data[list[b]*3+1] + ref.nor.data[list[a]*3+2]*ref.nor.data[list[b]*3+2];
    worstAngle = Math.max(worstAngle, Math.acos(Math.max(-1, Math.min(1, d))) * 180 / Math.PI);
  }
  if (worstAngle > 5) hardEdge.add(list.slice().sort((a, b) => a - b).join(','));
}
const accum = new Map();
const add = (k, x, y, z) => {
  const a = accum.get(k) ?? accum.set(k, [0, 0, 0]).get(k);
  a[0] += x; a[1] += y; a[2] += z;
};
for (let t = 0; t < idx.count; t += 3) {
  const a = idx.data[t], b = idx.data[t+1], c = idx.data[t+2];
  const ka = originalKey[a], kb = originalKey[b], kc = originalKey[c];
  if (!dirty.has(ka) && !dirty.has(kb) && !dirty.has(kc)) continue;
  const ux = pos.data[b*3]-pos.data[a*3], uy = pos.data[b*3+1]-pos.data[a*3+1], uz = pos.data[b*3+2]-pos.data[a*3+2];
  const vx = pos.data[c*3]-pos.data[a*3], vy = pos.data[c*3+1]-pos.data[a*3+1], vz = pos.data[c*3+2]-pos.data[a*3+2];
  const nx = uy*vz-uz*vy, ny = uz*vx-ux*vz, nz = ux*vy-uy*vx;
  add(ka, nx, ny, nz); add(kb, nx, ny, nz); add(kc, nx, ny, nz);
}
let rewritten = 0, skipped = 0;
for (const k of dirty) {
  const list = group.get(k);
  if (hardEdge.has(list.slice().sort((a, b) => a - b).join(','))) { skipped += 1; continue; }
  const a = accum.get(k);
  if (!a) continue;
  const len = Math.hypot(a[0], a[1], a[2]);
  if (len <= 0) continue;
  for (const v of list) {
    nor.data[v*3] = a[0]/len; nor.data[v*3+1] = a[1]/len; nor.data[v*3+2] = a[2]/len;
    rewritten += 1;
  }
}

for (const line of report) console.log('  ' + line);
console.log(`  largest vertex move ${(maxShift * 1000).toFixed(2)} mm over ${moved.size} points`);
console.log(`  normals rewritten ${rewritten} vertices (${dirty.size} dirty groups), ${skipped} reference hard-edge groups preserved`);
console.log(`  new bounds x ${lo[0].toFixed(4)}..${hi[0].toFixed(4)}`);
writeGlb(m.glb, OUT);
console.log(`  wrote ${OUT.split('/').pop()}`);
