import { Vector3 } from 'three';
import type { BufferGeometry } from 'three';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { boneInfluence, smoothstep } from './skinning';

/**
 * The head-to-neck junction.
 *
 * `scripts/generate-anatomical-body.mjs` binds by a single rule near the top of
 * the body:
 *
 *     if (part !== 'body' || sourcePoint.y > 1.50) influences = [{ sourceName: 'head', weight: 1 }];
 *
 * Everything above 1.50 m in the source becomes head:1.00, with no blend at all.
 * On the finished mesh that leaves 3,868 vertices bound wholly to the head,
 * reaching down to y = 1.397 — below the top of the spine. The neck bone runs
 * from 1.420 to 1.520 and drives almost none of the surface over it: only seven
 * vertices in the whole body carry both head and neck weight.
 *
 * Two consequences, and the second is the visible one.
 *
 * The neck does not deform. It is rigid with the skull, and the transition to
 * the chest happens as a step at the edge of the head's region rather than along
 * the neck.
 *
 * And that step has a height. Further down the generator the head is compressed
 * vertically, scaled by head weight:
 *
 *     compressedY = 1.52 + (oldY - 1.52) * 0.92 + 0.018
 *     targetPoint.y += (compressedY - oldY) * headWeight
 *
 * At the base of the neck that lift is about 28 mm, and it applies at full
 * strength to a head:1.00 vertex and not at all to the neck-and-spine vertex
 * beside it. Meanwhile the shoulder correction just above pushes the other side
 * *down*. The notch at the nape is the seam between two opposite displacements
 * that were applied through a hard weight boundary.
 *
 * So this repairs the junction rather than hiding it, in two separate places.
 *
 * `correctNeckWeights` rewrites the binding, and it runs inside
 * `buildAnatomicalBodyGeometry` — the one place the decoded surface is built —
 * so the studio's Character view, the Anatomy view and the GLB exporter all get
 * the same corrected weights without any of them asking for them. It changes
 * which bones move the neck and nothing else: positions and colours come out
 * exactly as they went in.
 *
 * `correctNeckLedge` is the other half. The same rule sends the head block
 * through its own conversion transform, which does not land where the spine's
 * does, so the seam is a ledge in the surface as well as a cliff in the weights.
 * It runs in the same place and on the same mesh, before the weights are
 * rewritten, so the character, the anatomy view and the exported file share one
 * corrected base surface rather than one mode carrying a private copy of the
 * fix.
 */

/**
 * The chain the neck should be driven by, and where each hand-over happens.
 *
 * Two influences per vertex, never more, which is what the rest of the character
 * uses. That forces a chain rather than a blend: spine to neck over the lower
 * half of the band, neck to head over the upper. Each ramp is a smoothstep, so
 * its gradient falls to zero exactly where the band meets weights that are
 * already pure — spine below, head above — and nothing steps at either end.
 *
 * The band is 140 mm long for one reason: the steepest weight gradient it can
 * produce is 1.5 / half-length, and that gradient is what a joint turns into
 * stretch. Shortening the band would make the transition tidier to describe and
 * the deformation worse.
 */
const NECK_CHAIN = {
  /** Below this the spine already owns the surface outright. */
  bottom: 1.375,
  /** Where the neck owns it alone. */
  middle: 1.45,
  /** Above this the head owns it outright. */
  top: 1.525,
};

/** A straight 0 → 1 across a span, clamped at both ends. */
const ramp = (low: number, high: number, value: number): number =>
  Math.min(1, Math.max(0, (value - low) / (high - low)));

/**
 * Where the neck stops reaching sideways.
 *
 * The source binds twelve vertices on the top of each shoulder — out to 170 mm
 * from the neck's axis, on the deltoid — partly to the neck bone, paired with
 * the upper arm. Turning the head swings them while the vertex beside them,
 * bound to the arm and the collarbone, stays put: an 8.6 mm edge stretched to
 * 2.15× and its mirror squashed to 0.31×, the two worst numbers anywhere near
 * the neck, and neither of them the head-binding defect.
 *
 * So beyond `full` — 65 mm, which is the neck's own surface at its base — the
 * neck's share is faded out and handed to the bone the vertex already shares
 * with, and by `none` it is gone. Two influences per vertex throughout.
 *
 * This applies to the source's own neck weights, outside the head-bound block.
 * The block itself is never cut off by radius: putting head weight against spine
 * weight out at its edge is the one adjacency this file exists to prevent, and
 * every version that tried it tore the surface open. A radial fade inside the
 * block also measures worse — pulled in to 85 mm it takes rotation from 1.29×
 * to 1.59×, because it opens a step across the height where the block hands the
 * surface from the spine to the head.
 */
const NECK_SIDEWAYS = { full: 0.065, none: 0.145 };

/**
 * The ledge at the nape, and the shape of the correction for it.
 *
 * The same `y > 1.50` rule that ruins the binding also decides which conversion
 * transform each source vertex is carried through, and the head's transform does
 * not land where the spine's does. So the two blocks are offset in depth as well
 * as bound to different bones, and the seam between them is a ledge: down the
 * midline the surface sits at z = -35 mm from y = 1.39 to 1.41 and then steps
 * back to -69 mm in a single 13 mm row. The nape overhangs a recess. Off the
 * midline the step shrinks — 31 mm at 20 mm out, 21 mm at 35 mm, gone by 60 mm —
 * so the ledge is a crescent across the back of the neck.
 *
 * The block above the seam is the whole head: face, jaw, ears, cranium. Moving
 * it is out of the question, so the correction comes from below. Each row under
 * the seam slides back towards the nape's depth, most at the seam and less
 * further down, until the field reaches zero at `depth` below it and at `none`
 * out to the side. The ledge becomes a slope from the nape into the upper
 * trapezius.
 *
 * Only z moves. The trapezius ridge is a lateral form and sliding the surface
 * back in depth cannot flatten it, which a smoothing pass over the same region
 * would — that was tried in an earlier round and it dragged the ridge down.
 *
 * The maximum displacement is set by the ledge: the row directly under the seam
 * has to reach the nape, so it moves by nearly the whole 34 mm step. Spreading
 * the ramp over more height does not reduce that — it only makes the rows below
 * move further — so 28 mm is the floor for closing this ledge without touching
 * the head.
 */
const NECK_LEDGE = {
  /** How far below the seam the ramp reaches, metres. */
  depth: 0.055,
  /** Lateral falloff: full correction within `full`, none beyond `none`. */
  full: 0.05,
  none: 0.085,
  /** Spacing of the bands the seam and the step are measured in, metres. */
  band: 0.0025,
  /**
   * How far either side of a band's centre it gathers vertices. The rows across
   * the back of the neck are about 10 mm apart, so a band narrower than this
   * finds no head-bound vertex at all in places and the correction comes out as
   * a comb. Overlapping windows also make the measured step vary smoothly from
   * one band to the next by construction.
   */
  window: 0.013,
  /** Rear surface only — the throat is on the other side and is not involved. */
  behind: -0.005,
};

export interface NeckReport {
  /** Vertices whose weights were rewritten. */
  reweighted: number;
  /** Of those, how many were bound wholly to the head before. */
  fromHeadAlone: number;
  /** Of those, how many were shoulder vertices whose sideways neck share was trimmed. */
  sideways: number;
  /** The largest vertical correction applied, metres. */
  maxDisplacement: number;
}

export interface LedgeReport {
  /** Vertices whose depth was corrected. */
  moved: number;
  /** The largest correction applied, metres. */
  maxDisplacement: number;
  /** The measured ledge at the midline, metres. */
  step: number;
  /** Corner displacements halved to keep a triangle facing outward. */
  damped: number;
}

/**
 * Close the ledge the conversion transforms leave at the nape.
 *
 * Runs inside `buildAnatomicalBodyGeometry` alongside the weight repair, before
 * anything else reads the surface, so the character, the anatomy view and the
 * GLB export share one corrected base. It must run *before* `correctNeckWeights`
 * — it reads the source's own head binding to find the seam, and the repair
 * rewrites exactly that.
 *
 * Deterministic: the seam and the step are measured from the mesh in narrow
 * lateral bands, mirrored by construction because every band is keyed on |x|.
 */
export function correctNeckLedge(
  geometry: BufferGeometry,
  rig: Skeleton = canonicalSkeleton,
): LedgeReport {
  const position = geometry.getAttribute('position');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const head = new Set<string>(['head']);
  const bands = Math.ceil((NECK_LEDGE.none + NECK_LEDGE.window) / NECK_LEDGE.band) + 1;
  const bandOf = (x: number) => Math.min(bands - 1, Math.round(Math.abs(x) / NECK_LEDGE.band));
  const centre = (band: number) => band * NECK_LEDGE.band;

  /** The lowest head-bound vertex in each band: the seam the block ends at. */
  const seam = new Float32Array(bands).fill(Number.POSITIVE_INFINITY);
  /** The rearmost depth just above the seam, and just below it. */
  const above = new Float32Array(bands).fill(Number.POSITIVE_INFINITY);
  const below = new Float32Array(bands).fill(Number.POSITIVE_INFINITY);

  /** Rear-of-neck vertices, and how much of each the source gave to the head. */
  const region: number[] = [];
  const onHead = new Float32Array(position.count);
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    const z = position.getZ(vertex);
    const y = position.getY(vertex);
    if (z > NECK_LEDGE.behind || y < 1.34 || y > 1.5) continue;
    if (Math.abs(position.getX(vertex)) > NECK_LEDGE.none + NECK_LEDGE.window) continue;
    onHead[vertex] = boneInfluence(skinIndex, skinWeight, vertex, head, rig);
    region.push(vertex);
  }

  for (const vertex of region) {
    if (onHead[vertex] < 0.5) continue;
    const reach = Math.abs(position.getX(vertex));
    const y = position.getY(vertex);
    for (let band = 0; band < bands; band += 1) {
      if (Math.abs(reach - centre(band)) > NECK_LEDGE.window) continue;
      seam[band] = Math.min(seam[band], y);
    }
  }
  for (let band = 0; band < bands; band += 1) {
    if (!Number.isFinite(seam[band])) seam[band] = 1.4;
  }
  // The lowest head-bound vertex is a step function of the band — it drops 22 mm
  // the moment the window reaches one row further down — and a seam that jumps
  // puts a dimple in the corrected surface, because a vertex is measured against
  // a different height from its neighbour 13 mm away. Six passes of a 1-2-1
  // kernel turn the staircase into the smooth curve the seam actually follows.
  const settled = new Float32Array(seam);
  for (let pass = 0; pass < 6; pass += 1) {
    const previous = Float32Array.from(settled);
    for (let band = 0; band < bands; band += 1) {
      const low = previous[Math.max(0, band - 1)];
      const high = previous[Math.min(bands - 1, band + 1)];
      settled[band] = (low + 2 * previous[band] + high) / 4;
    }
  }
  seam.set(settled);

  for (const vertex of region) {
    const reach = Math.abs(position.getX(vertex));
    const y = position.getY(vertex);
    const z = position.getZ(vertex);
    for (let band = 0; band < bands; band += 1) {
      if (Math.abs(reach - centre(band)) > NECK_LEDGE.window) continue;
      // A 30 mm window either side of the seam: the two surfaces whose
      // separation is the ledge, and nothing further off that is another
      // feature entirely.
      if (onHead[vertex] >= 0.5) {
        if (y < seam[band] + 0.03) above[band] = Math.min(above[band], z);
      } else if (y > seam[band] - 0.03) {
        below[band] = Math.min(below[band], z);
      }
    }
  }

  /** How far back each band has to slide to meet the nape. Never forwards. */
  const shift = new Float32Array(bands);
  for (let band = 0; band < bands; band += 1) {
    if (!Number.isFinite(above[band]) || !Number.isFinite(below[band])) continue;
    shift[band] = Math.min(0, above[band] - below[band]);
  }
  // One smoothing pass across neighbouring bands, so a band that happened to
  // catch a single stray vertex cannot put a ripple into the corrected surface.
  const smoothed = new Float32Array(shift);
  for (let band = 0; band < bands; band += 1) {
    const low = shift[Math.max(0, band - 1)];
    const high = shift[Math.min(bands - 1, band + 1)];
    smoothed[band] = (low + 2 * shift[band] + high) / 4;
  }

  const move = new Float32Array(position.count);
  for (const vertex of region) {
    if (onHead[vertex] >= 0.5) continue;
    const y = position.getY(vertex);
    const reach = Math.abs(position.getX(vertex));
    if (reach > NECK_LEDGE.none) continue;
    const band = bandOf(position.getX(vertex));
    // Clamped, not skipped, when the vertex sits above its band's seam. The
    // seam undulates by a centimetre or so across the back of the neck, so a
    // vertex on the shallow side of the ledge can still be higher than the
    // lowest head-bound vertex near it. Skipping those left them stranded at the
    // old depth beside neighbours that had moved 25 mm, which is a worse ledge
    // than the one being corrected — and it was the only thing that folded a
    // triangle here. The head block is already excluded by weight, so nothing on
    // the nape itself can be caught by this.
    const under = Math.max(0, seam[band] - y);
    if (under > NECK_LEDGE.depth) continue;
    // One at the seam, zero at the bottom of the ramp and zero out to the side.
    const field =
      (1 - smoothstep(0, NECK_LEDGE.depth, under)) *
      (1 - smoothstep(NECK_LEDGE.full, NECK_LEDGE.none, reach));
    move[vertex] = smoothed[band] * field;
  }

  // The seam row ends up within a few millimetres of the nape, which makes the
  // triangles bridging it shallow. Halve the corners of any that would end up
  // facing inwards, repeatedly, so the correction can never fold the surface.
  const index = geometry.getIndex();
  const first = new Vector3();
  const second = new Vector3();
  const third = new Vector3();
  const before = new Vector3();
  const after = new Vector3();
  let damped = 0;
  const facing = (corner: number[], scale: number, out: Vector3) => {
    const at = (slot: number, point: Vector3) =>
      point.set(
        position.getX(corner[slot]),
        position.getY(corner[slot]),
        position.getZ(corner[slot]) + move[corner[slot]] * scale,
      );
    at(0, first);
    at(1, second);
    at(2, third);
    return out.crossVectors(second.sub(first), third.sub(first));
  };
  if (index) {
    for (let pass = 0; pass < 12; pass += 1) {
      let touched = false;
      for (let triangle = 0; triangle < index.count; triangle += 3) {
        const corner = [index.getX(triangle), index.getX(triangle + 1), index.getX(triangle + 2)];
        if (!corner.some((vertex) => move[vertex] !== 0)) continue;
        facing(corner, 0, before);
        facing(corner, 1, after);
        if (before.lengthSq() < 1e-20 || after.lengthSq() < 1e-20) continue;
        if (after.dot(before) > 0 && after.length() / before.length() > 0.25) continue;
        for (const vertex of corner) move[vertex] *= 0.5;
        touched = true;
        damped += 1;
      }
      if (!touched) break;
    }
  }

  let moved = 0;
  let maxDisplacement = 0;
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (Math.abs(move[vertex]) < 1e-6) continue;
    position.setZ(vertex, position.getZ(vertex) + move[vertex]);
    moved += 1;
    maxDisplacement = Math.max(maxDisplacement, Math.abs(move[vertex]));
  }
  position.needsUpdate = true;
  return { moved, maxDisplacement, step: -smoothed[0], damped };
}

/**
 * Correct the head-to-neck binding on the character's own geometry.
 *
 * This runs inside `buildAnatomicalBodyGeometry`, which is the single place the
 * decoded surface is constructed, so Character mode, Anatomy mode and the GLB
 * export all read the same corrected weights without any of them knowing about
 * it. Positions and colours are untouched: this changes which bones move the
 * neck, not where the neck is.
 */
export function correctNeckWeights(
  geometry: BufferGeometry,
  rig: Skeleton = canonicalSkeleton,
): NeckReport {
  const position = geometry.getAttribute('position');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const head = new Set<string>(['head']);

  const number = new Map<string, number>();
  rig.bones.forEach((bone, index) => number.set(bone.name, index));
  const headBone = number.get('head');
  const neckBone = number.get('neck');
  const spineBone = number.get('spine_03');
  if (headBone === undefined || neckBone === undefined || spineBone === undefined) {
    return { reweighted: 0, fromHeadAlone: 0, sideways: 0, maxDisplacement: 0 };
  }

  const write = (vertex: number, pairs: [number, number][]) => {
    const total = pairs.reduce((carry, [, weight]) => carry + weight, 0) || 1;
    for (let slot = 0; slot < 4; slot += 1) {
      const entry = pairs[slot];
      (skinIndex as { setComponent(i: number, c: number, v: number): void }).setComponent(
        vertex,
        slot,
        entry ? entry[0] : 0,
      );
      (skinWeight as { setComponent(i: number, c: number, v: number): void }).setComponent(
        vertex,
        slot,
        entry ? entry[1] / total : 0,
      );
    }
  };

  const arms = new Set<number>();
  for (const side of ['l', 'r']) {
    for (const bone of [`upperarm_${side}`, `forearm_${side}`]) {
      const found = number.get(bone);
      if (found !== undefined) arms.add(found);
    }
  }

  let reweighted = 0;
  let fromHeadAlone = 0;
  let sideways = 0;
  const rewritten = new Uint8Array(position.count);

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    const y = position.getY(vertex);
    if (y < NECK_CHAIN.bottom || y > NECK_CHAIN.top) continue;
    // The region is the defect's own extent, not a cylinder round the neck. The
    // character binds a solid block to the head — the whole neck, the underside
    // of the jaw and the nape, down to y = 1.397 — and a cylinder drawn inside
    // that block leaves its own edge against head:1.00 surface, which is the
    // discontinuity moved rather than removed. Taking the block entire means the
    // only boundary is where the character already stops saying head, and there
    // the neighbour is shoulder: a difference between two bones that move
    // together while the neck turns, which costs nothing.
    // Any share of the head at all, not a majority: the character leaves a
    // handful of part-head vertices at the rim of the block, and skipping those
    // would leave head weight sitting directly against spine weight — the one
    // adjacency this correction exists to prevent.

    const wasHead = boneInfluence(skinIndex, skinWeight, vertex, head, rig);
    // Any share of the head at all, not a majority: the character leaves a
    // handful of part-head vertices at the rim of the block, and skipping those
    // would leave head weight sitting directly against spine weight.
    if (wasHead <= 0.05) continue;

    // How much of this vertex the neck drives: zero at the bottom of the block,
    // one across its middle, zero again at the top, and tapering at its rim and
    // its outer edge. Both of those tapers exist to hold down the weight
    // *difference* across the block's boundary, because that difference is what
    // a turning joint converts into stretch — at the rim the neighbour is
    // shoulder and at the outer edge it is jaw, and neither is driven by the
    // neck at all.
    // Linear along the neck, not a smoothstep. A smoothstep is flat at both ends
    // and steep in the middle; over a fixed span that costs half as much again in
    // peak gradient, and peak gradient is precisely what a turning joint converts
    // into stretch. The slope changes abruptly at each end of the ramp, but the
    // *weight* does not, and it is the weight that has to be continuous.
    const rise = ramp(NECK_CHAIN.bottom, NECK_CHAIN.middle, y);
    const fall = 1 - ramp(NECK_CHAIN.middle, NECK_CHAIN.top, y);

    // No radial taper. Every version that added one put head weight against
    // spine weight somewhere out at the block's edge — the two bones that move
    // most differently when the neck turns — and stretched an edge to five times
    // its length. The block is taken whole, and the only fade besides height is
    // at its rim, where the character's own weights are already thinning.
    const neck = Math.min(rise, fall) * smoothstep(0.05, 0.5, wasHead);

    // Above the middle the rest belongs to the head, below it to the spine. The
    // switch is a level surface at the height where the neck holds everything,
    // so the head and the spine are never neighbours anywhere. If they were, the
    // head would swing away from a static spine every time the neck turned, and
    // the surface between them would tear — which is exactly what a version of
    // this with a radial cut-off did.
    const partner = y < NECK_CHAIN.middle ? spineBone : headBone;

    const wasHeadAlone = wasHead > 0.999;
    write(
      vertex,
      ([
        [neckBone, neck],
        [partner, 1 - neck],
      ] as [number, number][]).filter(([, weight]) => weight > 1e-6),
    );
    reweighted += 1;
    if (wasHeadAlone) fromHeadAlone += 1;
    rewritten[vertex] = 1;
  }

  // The shoulders, which the block above never reaches because the source gives
  // them no head weight at all. Same fade, same rule: the neck's share goes to
  // the bone the vertex already shares with, so the influence count cannot rise.
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (rewritten[vertex]) continue;
    const radius = Math.hypot(position.getX(vertex), position.getZ(vertex));
    if (radius <= NECK_SIDEWAYS.full) continue;
    const keep = 1 - smoothstep(NECK_SIDEWAYS.full, NECK_SIDEWAYS.none, radius);
    if (keep > 0.999) continue;

    const pairs: [number, number][] = [];
    let neck = 0;
    for (let slot = 0; slot < 4; slot += 1) {
      const share = skinWeight.getComponent(vertex, slot);
      if (share <= 0) continue;
      const bone = skinIndex.getComponent(vertex, slot);
      if (bone === neckBone) neck += share;
      else pairs.push([bone, share]);
    }
    if (neck <= 1e-6 || pairs.length === 0) continue;

    // On the top of the shoulder the vertex's only other bone is the arm, and
    // there the neck's share is not faded but handed over whole to the
    // collarbone. Two reasons. The collarbone is the bone that actually carries
    // that surface — the vertices just inboard of it already use it — and it is
    // static exactly where the neck bone was not: it does not swing when the
    // head turns, and it does not lift when the arm does. Fading into the
    // deltoid instead would trade a neck that tears on a head turn for a
    // shoulder that tears on an arm raise, which is the pose these exercises
    // spend their time in.
    const collar = number.get(position.getX(vertex) < 0 ? 'clavicle_l' : 'clavicle_r');
    if (pairs.every(([bone]) => arms.has(bone)) && collar !== undefined) {
      const carried = pairs.find(([bone]) => bone === collar);
      if (carried) carried[1] += neck;
      else pairs.push([collar, neck]);
      write(vertex, pairs);
      reweighted += 1;
      sideways += 1;
      continue;
    }

    const moved = neck * (1 - keep);
    const total = pairs.reduce((carry, [, share]) => carry + share, 0) || 1;
    for (const pair of pairs) pair[1] += (moved * pair[1]) / total;
    if (neck * keep > 1e-6) pairs.push([neckBone, neck * keep]);
    write(vertex, pairs);
    reweighted += 1;
    sideways += 1;
  }

  skinIndex.needsUpdate = true;
  skinWeight.needsUpdate = true;
  return { reweighted, fromHeadAlone, sideways, maxDisplacement: 0 };
}
