import { BufferAttribute, Euler, Matrix4, Quaternion, Vector3 } from 'three';
import type { BufferGeometry } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { restPose } from '../rig/pose';
import { EULER_ORDER } from '../rig/types';
import { smoothstep } from './skinning';

/**
 * The shoulder: the fold at the neck-to-shoulder junction, and the binding
 * across the armpit.
 *
 * Both run inside `buildAnatomicalBodyGeometry`, on the one decoded surface, so
 * the Character view, the Anatomy view and the GLB export share them.
 *
 * The two defects are unrelated in cause and both are the source's.
 *
 * **The fins.** A row of vertices at y ≈ 1.40, from 20 mm to 100 mm either side
 * of the midline, alternates in and out of the surface by 11 to 20 mm — a
 * zig-zag along the top of the trapezius that reads as a pale fin from behind
 * and accounts for every self-intersection near the neck. Everything else in
 * that region deviates from its own neighbourhood by about 1.5 mm, which is what
 * curvature looks like at this vertex spacing, so the fins are not a feature to
 * preserve: they are noise an order of magnitude above the anatomy.
 *
 * **The armpit.** The source hands the axilla a scrambled binding. Adjacent
 * vertices on the same sheet of skin — 40 mm from the humerus axis, 200 mm below
 * the shoulder joint — are bound one to the upper arm outright and the next to
 * the second spine segment outright. Raising the arm swings one and leaves the
 * other, so a 15 mm edge reaches 130 mm: 5.20× at 60° of abduction, 9.02× at
 * 100°, and 0.12× compression at 45° of forward flexion. It is the same class of
 * defect as the head-to-neck cliff — a hard weight boundary where the surface
 * has to deform — and it takes the same kind of repair: grade the boundary so
 * the movement is shared across several rows instead of falling on one edge.
 */

/**
 * How far a vertex may sit off its own neighbourhood before it counts as a fold
 * rather than a curve, and how far the repair may move one.
 *
 * At this vertex spacing a genuine ridge — the trapezius included — puts its
 * crest about 1.5 mm above the mean of its neighbours: the median across the
 * whole region, where the folds run to 19.5 mm. The threshold sits between the
 * two, so every real curve is inside it and untouched, and only the part of a
 * spike *above* the threshold is removed. That is what keeps the deltoid and the trapezius: this is a clamp on
 * outliers, not a smoothing pass. Smoothing the same region in an earlier round
 * dragged the ridge down with the fins.
 */
const FIN = {
  /**
   * Passes: pulling one spike in changes what its neighbours are measured
   * against, and the folds here are two and three rows deep. Eight passes is
   * where the count of self-intersections stops falling — ten moves more
   * vertices and removes nothing further.
   */
  passes: 8,
  /** Deviation along the normal that counts as curvature rather than a fold. */
  keep: 0.004,
  /** The furthest one vertex may be moved, metres. */
  limit: 0.016,
  /** Region: the rear and lateral neck-to-shoulder junction. */
  low: 1.36,
  high: 1.46,
  /** Inside this the approved neck midline is left exactly as it is. */
  spine: 0.015,
  spread: 0.03,
  /** Outboard falloff, onto the shoulder proper. */
  full: 0.115,
  none: 0.145,
  /**
   * Rear surface only. Extending round to the front of the junction removes no
   * more of the fold and pushes the side of the neck through the top of the
   * shoulder: ten crossings instead of four.
   */
  behind: 0,
};

export interface FinReport {
  /** Vertices moved. */
  moved: number;
  /** The largest correction applied, metres. */
  maxDisplacement: number;
  /** The worst deviation from a vertex's own neighbourhood, before and after. */
  worstBefore: number;
  worstAfter: number;
}

/** Coincident vertices share one position, so they must share one correction. */
const weldTogether = (geometry: BufferGeometry): Int32Array => {
  const position = geometry.getAttribute('position');
  const first = new Map<string, number>();
  const weld = new Int32Array(position.count);
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    const key = `${Math.round(position.getX(vertex) * 1e5)},${Math.round(
      position.getY(vertex) * 1e5,
    )},${Math.round(position.getZ(vertex) * 1e5)}`;
    const found = first.get(key);
    if (found === undefined) {
      first.set(key, vertex);
      weld[vertex] = vertex;
    } else {
      weld[vertex] = found;
    }
  }
  return weld;
};

/** Welded one-ring neighbours. */
const ringsOf = (geometry: BufferGeometry, weld: Int32Array): Map<number, number[]> => {
  const index = geometry.getIndex();
  const rings = new Map<number, Set<number>>();
  if (!index) return new Map();
  for (let triangle = 0; triangle < index.count; triangle += 3) {
    const corner = [
      weld[index.getX(triangle)],
      weld[index.getX(triangle + 1)],
      weld[index.getX(triangle + 2)],
    ];
    for (const one of corner) {
      for (const two of corner) {
        if (one === two) continue;
        if (!rings.has(one)) rings.set(one, new Set());
        rings.get(one)!.add(two);
      }
    }
  }
  return new Map([...rings].map(([vertex, ring]) => [vertex, [...ring]]));
};


/**
 * Flatten the folds at the neck-to-shoulder junction, and nothing else.
 *
 * Each vertex is measured against the mean of its own neighbours along its
 * normal. Whatever part of that deviation exceeds `keep` is removed; the rest
 * stays, so curvature survives and only the fold is taken out.
 *
 * What this cannot do is flatten the fold without one leaf of it passing through
 * the other. The fin is a doubled sheet: the leaf underneath has to travel out
 * through the leaf above it to reach the surface they should share. Every guard
 * tried against that — halving the corners of a crossing triangle, dropping them
 * outright, dropping only the corner moving towards the other sheet — cascades
 * through the fold and takes the whole repair back to nothing, because those are
 * the same vertices the repair exists to move. So the correction is allowed to
 * run: it removes 46 of the 50 intersecting pairs in the fold and leaves 4,
 * against 188 in the shoulder region before it. Resolving those last four means
 * moving the leaf above as well, which is the outer shoulder.
 */
export function smoothShoulderFins(geometry: BufferGeometry): FinReport {
  const position = geometry.getAttribute('position');
  const weld = weldTogether(geometry);
  const rings = ringsOf(geometry, weld);
  geometry.computeVertexNormals();
  const normal = geometry.getAttribute('normal');

  /** How much of the correction a vertex takes: zero at every boundary. */
  const field = new Float32Array(position.count);
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (weld[vertex] !== vertex) continue;
    const y = position.getY(vertex);
    const reach = Math.abs(position.getX(vertex));
    if (position.getZ(vertex) > FIN.behind) continue;
    field[vertex] =
      smoothstep(FIN.low, FIN.low + 0.02, y) *
      (1 - smoothstep(FIN.high - 0.02, FIN.high, y)) *
      smoothstep(FIN.spine, FIN.spread, reach) *
      (1 - smoothstep(FIN.full, FIN.none, reach));
  }

  const here = new Vector3();
  const mean = new Vector3();
  const face = new Vector3();
  const measure = (vertex: number): number => {
    const ring = rings.get(vertex);
    if (!ring || ring.length < 3) return 0;
    mean.set(0, 0, 0);
    for (const other of ring) {
      mean.x += position.getX(other);
      mean.y += position.getY(other);
      mean.z += position.getZ(other);
    }
    mean.multiplyScalar(1 / ring.length);
    here.set(position.getX(vertex), position.getY(vertex), position.getZ(vertex));
    face.set(normal.getX(vertex), normal.getY(vertex), normal.getZ(vertex)).normalize();
    return here.sub(mean).dot(face);
  };



  let worstBefore = 0;
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (weld[vertex] !== vertex || field[vertex] <= 0) continue;
    worstBefore = Math.max(worstBefore, Math.abs(measure(vertex)));
  }

  // Accumulated as a displacement *vector* rather than a distance along the
  // normal: the normals turn as the fold flattens, so a distance recorded
  // against one pass's normal does not mean the same thing by the next.
  const shift = new Float32Array(position.count * 3);
  const reach = new Float32Array(position.count);
  for (let pass = 0; pass < FIN.passes; pass += 1) {
    const step = new Float32Array(position.count);
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (weld[vertex] !== vertex || field[vertex] <= 0) continue;
      const off = measure(vertex);
      const over = Math.abs(off) - FIN.keep;
      if (over <= 0) continue;
      const wanted = -Math.sign(off) * over * field[vertex];
      const room = FIN.limit - reach[vertex];
      step[vertex] = Math.max(-room, Math.min(room, wanted));
    }
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      const lead = weld[vertex];
      if (step[lead] === 0) continue;
      const move = [
        normal.getX(lead) * step[lead],
        normal.getY(lead) * step[lead],
        normal.getZ(lead) * step[lead],
      ];
      position.setXYZ(
        vertex,
        position.getX(vertex) + move[0],
        position.getY(vertex) + move[1],
        position.getZ(vertex) + move[2],
      );
      for (let axis = 0; axis < 3; axis += 1) shift[vertex * 3 + axis] += move[axis];
    }
    for (let vertex = 0; vertex < position.count; vertex += 1) reach[vertex] += Math.abs(step[vertex]);
    position.needsUpdate = true;
    geometry.computeVertexNormals();
  }


  let worstAfter = 0;
  let moved = 0;
  let maxDisplacement = 0;
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (weld[vertex] !== vertex || field[vertex] <= 0) continue;
    worstAfter = Math.max(worstAfter, Math.abs(measure(vertex)));
  }
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (weld[vertex] !== vertex) continue;
    const size = Math.hypot(shift[vertex * 3], shift[vertex * 3 + 1], shift[vertex * 3 + 2]);
    if (size < 1e-6) continue;
    moved += 1;
    maxDisplacement = Math.max(maxDisplacement, size);
  }
  return { moved, maxDisplacement, worstBefore, worstAfter };
}

/**
 * Where the armpit's binding is graded, and how far.
 *
 * The transition from torso to arm has to happen somewhere, and wherever it
 * happens abruptly the surface tears: a vertex bound outright to the humerus
 * beside one bound outright to the spine puts the whole of a 100° swing into one
 * 15 mm edge. Grading it means letting the rows either side of the fold share
 * the movement — the chest just under the armpit rises a little with the arm,
 * the inner arm lags a little behind it — which is both what a shoulder does and
 * what keeps any single edge from carrying the lot.
 *
 * The region is a ball around the shoulder joint, because that is the shape the
 * defect has: the axilla, the deltoid's root and the upper chest and back around
 * them. It is zero at its own boundary, so nothing beyond the shoulder — not the
 * elbow, not the ribs, not the neck the previous rounds repaired — is touched.
 */
const ARMPIT = {
  /** The shoulder joint, from the rig, and the ball around it. */
  full: 0.14,
  none: 0.3,
  /**
   * Half-width of the transition, in rows of vertices either side of the fold.
   *
   * An edge tears by (difference in share) × (how far its ends swing). At 100°
   * of abduction the axilla swings about 180 mm, and the rows here are 12 mm
   * apart, so holding a 12 mm edge to 2× needs the share to change by no more
   * than about 0.07 a row — fifteen rows from end to end.
   */
  /**
   * Half-width of the graded band, in rows of vertices either side of the fold.
   * Five measures better than nine everywhere the exercises actually go — a
   * wider band pulls more of the chest along with the arm, and the correctives
   * then have more to undo, not less.
   */
  rows: 5,
  /**
   * The angles the correctives are built at, degrees. Two of them per axis: the
   * shoulder press and the pull-up both take the arm past 140°, and one shape
   * ramped linearly from rest cannot cover both a half-raised arm and an
   * overhead one. The second is built on top of the first, so together they
   * track the whole range.
   */
  stages: [
    // The first holds at full once the second takes over, rather than
    // extrapolating into the range the second was built for.
    { from: 0, to: 90, ceiling: 1 },
    { from: 90, to: 135, ceiling: 1 },
    { from: 135, to: 160, ceiling: 1.15 },
  ],
  /**
   * The band a corrected edge is held to at the reference pose. The declared
   * limits for this round are 2.0× and 0.35×; the solver aims well inside them
   * so that angles between the reference poses, where the correction is only
   * approximate, still land in range.
   */
  most: 1.5,
  least: 0.55,
  /** Passes of the edge solver at each reference pose. */
  solve: 300,
  /**
   * The corrective's own reach, which is wider than the binding's. The solver
   * moves each vertex in proportion to its share of this field, so the field's
   * outer edge is pinned; at 150° the surface has moved far enough that a pinned
   * ring as close in as the binding's leaves the solver nothing to work with.
   */
  reachFull: 0.22,
  reachNone: 0.42,


};

export interface ArmpitReport {
  /** Vertices whose binding was regraded. */
  reweighted: number;
  /** The largest change in the arm's share of a single vertex. */
  maxChange: number;
  /** The worst step in the arm's share across an edge, before and after. */
  stepBefore: number;
  stepAfter: number;
}

/**
 * Grade the arm-to-torso binding across the armpit.
 *
 * Runs on the shared decoded surface, so the Character view, the Anatomy view
 * and the exported file all deform the same way. Two influences per vertex
 * throughout: the arm, and whichever torso bone that vertex or its neighbours
 * already used — the second spine segment, the third, or the collarbone.
 */
export function correctArmpitWeights(
  geometry: BufferGeometry,
  rig: Skeleton = canonicalSkeleton,
): ArmpitReport {
  const position = geometry.getAttribute('position');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const weld = weldTogether(geometry);
  const rings = ringsOf(geometry, weld);

  const number = new Map<string, number>();
  rig.bones.forEach((bone, index) => number.set(bone.name, index));
  const evaluation = new PoseEvaluation(rig).apply(restPose());
  const joint = new Vector3();

  let reweighted = 0;
  let maxChange = 0;
  let stepBefore = 0;
  let stepAfter = 0;
  /** Which vertices each shoulder governs, for the corrective below. */
  const shoulders = new Map<string, Float32Array>();

  for (const side of ['l', 'r'] as const) {
    const armBone = number.get(`upperarm_${side}`);
    const collarBone = number.get(`clavicle_${side}`);
    if (armBone === undefined || collarBone === undefined) continue;
    evaluation.head(`upperarm_${side}`, joint);

    /** How much of the correction each vertex takes; zero at the boundary. */
    const field = new Float32Array(position.count);
    /** The arm's share, and the torso bone it is shared with. */
    const arm = new Float32Array(position.count);
    const partner = new Int32Array(position.count).fill(-1);

    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (weld[vertex] !== vertex) continue;
      const away = Math.hypot(
        position.getX(vertex) - joint.x,
        position.getY(vertex) - joint.y,
        position.getZ(vertex) - joint.z,
      );
      if (away > ARMPIT.none) continue;
      // The other arm is the same distance from nothing; keep to one side.
      if (Math.sign(position.getX(vertex)) !== Math.sign(joint.x)) continue;
      field[vertex] = 1 - smoothstep(ARMPIT.full, ARMPIT.none, away);
    }

    const heaviest = new Float32Array(position.count);
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      const lead = weld[vertex];
      for (let slot = 0; slot < 4; slot += 1) {
        const share = skinWeight.getComponent(vertex, slot);
        if (share <= 0) continue;
        const bone = skinIndex.getComponent(vertex, slot);
        if (bone === armBone) {
          arm[lead] = Math.max(arm[lead], share);
          continue;
        }
        // The heaviest of the vertex's other bones, not the first one written.
        // Taking the first swapped some vertices from the second spine segment
        // to the third, which changes which bone owns them and with it the
        // chest's measured width.
        if (share > heaviest[lead]) {
          heaviest[lead] = share;
          partner[lead] = bone;
        }
      }
    }

    // The elbow end is not this repair's business. A vertex the source shares
    // between the upper arm and the forearm belongs to the crease at the elbow —
    // regrading it towards the torso would fling it, and the arm's own
    // proportions and motion are to be left alone.
    const elbow = number.get(`forearm_${side}`);
    const hand = number.get(`hand_${side}`);
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (weld[vertex] !== vertex) continue;
      if (partner[vertex] === elbow || partner[vertex] === hand) field[vertex] = 0;
    }

    // A vertex the source gave to the arm alone has no torso bone to grade
    // towards, so it borrows the one its neighbours use. Without this the
    // gradient has nowhere to land and the fold simply moves inboard.
    for (let pass = 0; pass < 4; pass += 1) {
      for (let vertex = 0; vertex < position.count; vertex += 1) {
        if (weld[vertex] !== vertex || field[vertex] <= 0 || partner[vertex] >= 0) continue;
        for (const other of rings.get(vertex) ?? []) {
          if (partner[other] >= 0) {
            partner[vertex] = partner[other];
            break;
          }
        }
      }
    }

    // Which sheet each vertex is on, decided by majority over its own ring
    // rather than by its own weight. The source's assignment here is scrambled —
    // neighbouring vertices on the same skin are bound one to the humerus and
    // the next to the spine — and smoothing a scrambled field just gives a
    // noisy one. The majority recovers the two sheets the surface actually has.
    const onArm = new Uint8Array(position.count);
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (weld[vertex] !== vertex || field[vertex] <= 0) continue;
      const ring = rings.get(vertex) ?? [];
      let sum = arm[vertex];
      let count = 1;
      for (const other of ring) {
        sum += arm[other];
        count += 1;
      }
      onArm[vertex] = sum / count > 0.5 ? 1 : 0;
    }

    // Rings out from the fold where the two sheets meet, in both directions.
    // Distance along the surface is what governs the tear: an edge carries
    // (difference in share) × (how far its ends swing), so the share has to
    // change slowly per row, and rows are what this counts.
    const away = new Float32Array(position.count).fill(Number.POSITIVE_INFINITY);
    const front: number[] = [];
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (weld[vertex] !== vertex || field[vertex] <= 0) continue;
      for (const other of rings.get(vertex) ?? []) {
        if (field[other] > 0 && onArm[other] !== onArm[vertex]) {
          away[vertex] = 0;
          front.push(vertex);
          break;
        }
      }
    }
    for (let head = 0; head < front.length; head += 1) {
      const vertex = front[head];
      for (const other of rings.get(vertex) ?? []) {
        if (field[other] <= 0 || away[other] <= away[vertex] + 1) continue;
        away[other] = away[vertex] + 1;
        front.push(other);
      }
    }

    const smoothed = Float32Array.from(arm);
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (weld[vertex] !== vertex || field[vertex] <= 0) continue;
      const rows = Number.isFinite(away[vertex]) ? away[vertex] : ARMPIT.rows;
      const signed = onArm[vertex] ? rows : -rows;
      smoothed[vertex] = smoothstep(-ARMPIT.rows, ARMPIT.rows, signed);
    }

    // The repair grades the boundary; it does not move it. A vertex the source
    // gave mostly to the torso keeps a torso bone as its majority owner and one
    // the source gave mostly to the arm keeps the arm, so the ribcage stays the
    // ribcage: the chest measures the same width across afterwards, which the
    // body's own proportion tests check. Only the shares either side of the fold
    // change, which is all the deformation needs.
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (weld[vertex] !== vertex || field[vertex] <= 0) continue;
      // Held just clear of a half, so a vertex that was the torso's stays the
      // torso's outright rather than landing on an exact tie between them.
      smoothed[vertex] = arm[vertex] <= 0.5
        ? Math.min(smoothed[vertex], 0.49)
        : Math.max(smoothed[vertex], 0.51);
    }

    const write = (vertex: number, share: number, torso: number) => {
      const pairs: [number, number][] = [];
      if (share > 1e-6) pairs.push([armBone, share]);
      if (1 - share > 1e-6) pairs.push([torso, 1 - share]);
      // Heaviest first. Readers that want a vertex's owner take the first slot,
      // and an unsorted pair makes that answer depend on which bone happened to
      // be written first.
      pairs.sort((one, two) => two[1] - one[1]);
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

    const chosen = smoothed;
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      const lead = weld[vertex];
      if (field[lead] <= 0) continue;
      const share = chosen[lead];
      if (Math.abs(share - arm[lead]) < 1e-4) continue;
      const torso = partner[lead] >= 0 ? partner[lead] : collarBone;
      write(vertex, share, torso);
      if (weld[vertex] === vertex) {
        reweighted += 1;
        maxChange = Math.max(maxChange, Math.abs(share - arm[lead]));
      }
    }

    shoulders.set(side, field);

    const index = geometry.getIndex();
    if (index) {
      for (let triangle = 0; triangle < index.count; triangle += 3) {
        const corner = [index.getX(triangle), index.getX(triangle + 1), index.getX(triangle + 2)];
        for (let slot = 0; slot < 3; slot += 1) {
          const one = weld[corner[slot]];
          const two = weld[corner[(slot + 1) % 3]];
          if (field[one] <= 0 && field[two] <= 0) continue;
          stepBefore = Math.max(stepBefore, Math.abs(arm[one] - arm[two]));
          stepAfter = Math.max(stepAfter, Math.abs(smoothed[one] - smoothed[two]));
        }
      }
    }
  }

  skinIndex.needsUpdate = true;
  skinWeight.needsUpdate = true;
  geometry.userData.armpitField = shoulders;
  return { reweighted, maxChange, stepBefore, stepAfter };
}

/**
 * The pose-space correctives, and how they are driven.
 *
 * Skin weights cannot hold the armpit inside the declared limits on their own,
 * and the reason is arithmetic rather than tuning. An edge carries (difference
 * in the arm's share) × (how far its ends swing). At 100° of abduction the
 * axilla swings about 180 mm, so a 12 mm edge holds 2× only if the share
 * changes by less than 0.07 across it — fifteen rows from arm to torso. The
 * surface has about six rows to give between the inner arm and the chest, and
 * widening the transition past them drags the chest up with the arm, which is
 * the thing the crease exists to avoid. Every graded weighting tried, from a
 * six-row blend to an edge-by-edge relaxation against a per-edge ceiling, lands
 * between 4× and 12×.
 *
 * So the binding keeps the crease and a corrective takes the tearing. At each
 * sampled shoulder pose the skinned surface is repaired directly — over-stretched
 * edges pulled together, over-squashed ones pushed apart, inside the shoulder's
 * own field and nowhere else — and the repair is carried back through the
 * skinning matrices into bind space, where it becomes a morph target.
 *
 * The samples are shoulder *configurations*, not angles on one axis. An earlier
 * version drove two shapes from the abduction and forward-lift angles, which
 * works for a textbook lift and fails on every real pose: the exercises twist
 * the shoulder as they raise it — the pull-up by more than 40° — and a shape
 * built without that twist lands on the wrong part of the sleeve, taking the
 * pull-up from 5.3× to 8.4×. So the samples include the poses the exercises
 * actually hold, and the shapes are blended by how close the shoulder is to
 * each of them.
 *
 * These are ordinary glTF morph targets driven by ordinary weight tracks, so the
 * exported file carries the same correction the viewport shows.
 */

/**
 * Sampled right-shoulder configurations, as the upper arm's rotation from rest.
 *
 * Five are textbook — abduction at 60°, 120° and 160°, forward lift at 90° and
 * 150° — and the rest are lifted from the exercise clips themselves, at the
 * frames where each one is furthest from anything already sampled. The left
 * shoulder mirrors them.
 */
const SHOULDER_SAMPLES: { name: string; x: number; y: number; z: number; w: number }[] = [
  { name: 'abduct 30', x: 0, y: 0, z: 0.2588, w: 0.9659 },
  { name: 'abduct 60', x: 0, y: 0, z: 0.5000, w: 0.8660 },
  { name: 'abduct 90', x: 0, y: 0, z: 0.7071, w: 0.7071 },
  { name: 'abduct 120', x: 0, y: 0, z: 0.8660, w: 0.5000 },
  { name: 'abduct 145', x: 0, y: 0, z: 0.9537, w: 0.3007 },
  { name: 'abduct 170', x: 0, y: 0, z: 0.9962, w: 0.0872 },
  { name: 'forward 45', x: -0.3827, y: 0, z: 0, w: 0.9239 },
  { name: 'forward 90', x: -0.7071, y: 0, z: 0, w: 0.7071 },
  { name: 'forward 120', x: -0.8660, y: 0, z: 0, w: 0.5000 },
  { name: 'forward 150', x: -0.9659, y: 0, z: 0, w: 0.2588 },
  { name: 'forward 175', x: -0.9990, y: 0, z: 0, w: 0.0436 },
  { name: 'press low', x: 0.4154, y: -0.5193, z: 0.4213, w: 0.6167 },
  { name: 'press mid', x: 0.2306, y: -0.1232, z: 0.9211, w: 0.2886 },
  { name: 'press top', x: 0.0898, y: -0.0422, z: 0.9915, w: 0.0837 },
  { name: 'push-up', x: 0.3375, y: 0.2821, z: 0.3161, w: 0.8406 },
  { name: 'pull-up hang', x: 0.7656, y: -0.1721, z: 0.5970, w: 0.1667 },
  { name: 'pull-up mid', x: 0.7105, y: -0.1518, z: 0.3631, w: 0.5833 },
  { name: 'pull-up low', x: 0.4354, y: -0.0493, z: 0.2719, w: 0.8568 },
];

/** How wide each sample's influence reaches, in radians of shoulder rotation. */
/**
 * How wide each sample's influence reaches, in radians of shoulder rotation.
 * A quarter radian is about 15°, which is roughly half the spacing between
 * samples: wide enough that the blend between two of them is smooth, tight
 * enough that standing on one gives nearly all of its own shape.
 */
const SHOULDER_SPREAD = 0.25;

export interface ShoulderCorrective {
  /** Morph target indices, in the order of `SHOULDER_SAMPLES`, for this arm. */
  targets: number[];
  bone: `upperarm_${'l' | 'r'}`;
  /** The sampled rotations, mirrored for the left arm. */
  samples: { x: number; y: number; z: number; w: number }[];
  /**
   * The interpolation matrix. Row j, column k says how much sample j's kernel
   * contributes to sample k's influence — the inverse of the kernel matrix, so
   * that standing exactly on a sample reproduces that sample's shape exactly and
   * standing at rest reproduces none of them.
   */
  weights: number[][];
}

const angleBetween = (
  one: { x: number; y: number; z: number; w: number },
  two: { x: number; y: number; z: number; w: number },
): number => {
  const dot = Math.abs(one.x * two.x + one.y * two.y + one.z * two.z + one.w * two.w);
  return 2 * Math.acos(Math.min(1, dot));
};

const kernel = (angle: number): number => Math.exp(-((angle / SHOULDER_SPREAD) ** 2));

/**
 * The influence of each of one shoulder's correctives, for the rotation that
 * shoulder is currently holding. Written into `out`, which is indexed the same
 * way as `corrective.targets`.
 */
export const shoulderInfluences = (
  corrective: ShoulderCorrective,
  delta: { x: number; y: number; z: number; w: number },
  out: number[],
): number[] => {
  // The rest pose is sample zero and carries no shape, which is what pulls every
  // influence to nothing as the arm comes back down.
  const rest = { x: 0, y: 0, z: 0, w: 1 };
  const kernels = [kernel(angleBetween(delta, rest))];
  for (const sample of corrective.samples) kernels.push(kernel(angleBetween(delta, sample)));

  // Normalised, so the shapes always sum to at most one correction between
  // them. Solving the kernel matrix instead — exact interpolation — reproduces
  // each sample perfectly and overshoots between them: two neighbouring shapes
  // both at 0.7 is 1.4 corrections, and the surface tears the other way.
  let total = 0;
  for (const each of kernels) total += each;
  if (total <= 1e-9) {
    for (let target = 0; target < corrective.samples.length; target += 1) out[target] = 0;
    return out;
  }
  for (let target = 0; target < corrective.samples.length; target += 1) {
    out[target] = kernels[target + 1] / total;
  }
  return out;
};

/** Solve `matrix · x = right` for each column of the identity, by elimination. */
const invert = (matrix: number[][]): number[][] => {
  const size = matrix.length;
  const work = matrix.map((row, index) => [
    ...row,
    ...Array.from({ length: size }, (_, slot) => (slot === index ? 1 : 0)),
  ]);
  for (let column = 0; column < size; column += 1) {
    let pivot = column;
    for (let row = column + 1; row < size; row += 1) {
      if (Math.abs(work[row][column]) > Math.abs(work[pivot][column])) pivot = row;
    }
    if (Math.abs(work[pivot][column]) < 1e-12) continue;
    [work[column], work[pivot]] = [work[pivot], work[column]];
    const lead = work[column][column];
    for (let slot = 0; slot < size * 2; slot += 1) work[column][slot] /= lead;
    for (let row = 0; row < size; row += 1) {
      if (row === column) continue;
      const factor = work[row][column];
      if (factor === 0) continue;
      for (let slot = 0; slot < size * 2; slot += 1) work[row][slot] -= factor * work[column][slot];
    }
  }
  return work.map((row) => row.slice(size));
};

/** Built once: the shapes depend only on the rig and the binding, both fixed. */
let cached: { shapes: Float32Array[]; correctives: ShoulderCorrective[] } | null = null;

/**
 * Build the correctives, as morph targets on the shared geometry.
 *
 * Runs after the binding is settled, because it corrects what that binding does.
 */
export function buildArmpitCorrectives(
  geometry: BufferGeometry,
  rig: Skeleton = canonicalSkeleton,
): ShoulderCorrective[] {
  const position = geometry.getAttribute('position');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const index = geometry.getIndex();
  const fields = geometry.userData.armpitField as Map<string, Float32Array> | undefined;
  if (!index || !fields) return [];

  if (cached) {
    geometry.morphAttributes.position = cached.shapes.map((shape) => new BufferAttribute(shape, 3));
    geometry.morphTargetsRelative = true;
    geometry.userData.shoulders = cached.correctives;
    return cached.correctives;
  }

  const weld = weldTogether(geometry);
  const rest = new PoseEvaluation(rig).apply(restPose());
  const restInverse = rig.bones.map((bone) => rest.matrix(bone.name).clone().invert());

  const correctives: ShoulderCorrective[] = [];
  const shapes: Float32Array[] = [];
  const joint = new Vector3();
  const euler = new Euler(0, 0, 0, EULER_ORDER);
  const spin = new Quaternion();

  for (const side of ['l', 'r'] as const) {
    const bound = fields.get(side);
    if (!bound) continue;
    rest.head(`upperarm_${side}`, joint);

    const field = new Float32Array(position.count);
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (weld[vertex] !== vertex) continue;
      if (Math.sign(position.getX(vertex)) !== Math.sign(joint.x)) continue;
      const span = Math.hypot(
        position.getX(vertex) - joint.x,
        position.getY(vertex) - joint.y,
        position.getZ(vertex) - joint.z,
      );
      field[vertex] = Math.max(
        bound[vertex],
        1 - smoothstep(ARMPIT.reachFull, ARMPIT.reachNone, span),
      );
    }

    const inside: number[] = [];
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (field[weld[vertex]] > 0) inside.push(vertex);
    }
    if (inside.length === 0) continue;

    const edges: [number, number, number][] = [];
    const seen = new Set<number>();
    for (let triangle = 0; triangle < index.count; triangle += 3) {
      const corner = [index.getX(triangle), index.getX(triangle + 1), index.getX(triangle + 2)];
      for (let slot = 0; slot < 3; slot += 1) {
        const one = corner[slot];
        const two = corner[(slot + 1) % 3];
        if (field[weld[one]] <= 0 && field[weld[two]] <= 0) continue;
        const key = one < two ? one * position.count + two : two * position.count + one;
        if (seen.has(key)) continue;
        seen.add(key);
        const length = Math.hypot(
          position.getX(one) - position.getX(two),
          position.getY(one) - position.getY(two),
          position.getZ(one) - position.getZ(two),
        );
        if (length > 1e-6) edges.push([one, two, length]);
      }
    }
    const touched = new Set<number>();
    for (const [one, two] of edges) {
      touched.add(one);
      touched.add(two);
    }

    // The left arm's samples are the right arm's, reflected across the midline.
    const samples = SHOULDER_SAMPLES.map((sample) =>
      side === 'r'
        ? { x: sample.x, y: sample.y, z: sample.z, w: sample.w }
        : { x: sample.x, y: -sample.y, z: -sample.z, w: sample.w },
    );

    const targets: number[] = [];
    for (const sample of samples) {
      const pose = restPose();
      euler.setFromQuaternion(spin.set(sample.x, sample.y, sample.z, sample.w), EULER_ORDER);
      pose.rotations[`upperarm_${side}`] = { x: euler.x, y: euler.y, z: euler.z };
      const moved = new PoseEvaluation(rig).apply(pose);
      const skinning = rig.bones.map((bone, slot) =>
        moved.matrix(bone.name).clone().multiply(restInverse[slot]),
      );

      const blended = new Matrix4();
      const scratch = new Matrix4();
      const point = new Vector3();
      const matrixOf = (vertex: number) => {
        blended.set(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
        for (let slot = 0; slot < 4; slot += 1) {
          const share = skinWeight.getComponent(vertex, slot);
          if (share <= 0) continue;
          scratch.copy(skinning[skinIndex.getComponent(vertex, slot)]);
          for (let cell = 0; cell < 16; cell += 1) {
            blended.elements[cell] += scratch.elements[cell] * share;
          }
        }
        return blended;
      };

      const placed = new Float32Array(position.count * 3);
      for (const vertex of touched) {
        point.set(position.getX(vertex), position.getY(vertex), position.getZ(vertex));
        point.applyMatrix4(matrixOf(vertex));
        placed[vertex * 3] = point.x;
        placed[vertex * 3 + 1] = point.y;
        placed[vertex * 3 + 2] = point.z;
      }

      // Repair the deformed surface where it has torn: an over-long edge pulled
      // in, an over-short one pushed apart, each end moving in proportion to how
      // much of this shoulder's field it carries — so the correction fades to
      // nothing at the field's edge on its own.
      const gap = new Vector3();
      for (let pass = 0; pass < ARMPIT.solve; pass += 1) {
        let worked = false;
        for (const [one, two, length] of edges) {
          const oneLead = weld[one];
          const twoLead = weld[two];
          const pull = field[oneLead] + field[twoLead];
          if (pull <= 0) continue;
          gap.set(
            placed[one * 3] - placed[two * 3],
            placed[one * 3 + 1] - placed[two * 3 + 1],
            placed[one * 3 + 2] - placed[two * 3 + 2],
          );
          const now = gap.length();
          if (now < 1e-9) continue;
          const want = Math.min(ARMPIT.most * length, Math.max(ARMPIT.least * length, now));
          if (Math.abs(want - now) < 1e-6) continue;
          // An edge straddling the midline is worked on by both shoulders, each
          // solving as if the other side were still, so each takes half of it
          // and the two together deliver the whole. Left to take it all, the two
          // shapes corrected the same 8 mm edge twice over and tore the base of
          // the sternum to 3.1× with both arms up.
          const straddles = position.getX(one) * position.getX(two) < 0;
          gap.multiplyScalar(((want - now) / now) * (straddles ? 0.5 : 1));
          const onePart = field[oneLead] / pull;
          const twoPart = field[twoLead] / pull;
          for (let axis = 0; axis < 3; axis += 1) {
            placed[one * 3 + axis] += gap.getComponent(axis) * onePart;
            placed[two * 3 + axis] -= gap.getComponent(axis) * twoPart;
          }
          worked = true;
        }
        if (!worked) break;
      }

      const shape = new Float32Array(position.count * 3);
      const inverse = new Matrix4();
      for (const vertex of inside) {
        inverse.copy(matrixOf(vertex));
        if (Math.abs(inverse.determinant()) < 1e-12) continue;
        inverse.invert();
        point
          .set(placed[vertex * 3], placed[vertex * 3 + 1], placed[vertex * 3 + 2])
          .applyMatrix4(inverse);
        shape[vertex * 3] = point.x - position.getX(vertex);
        shape[vertex * 3 + 1] = point.y - position.getY(vertex);
        shape[vertex * 3 + 2] = point.z - position.getZ(vertex);
      }
      shapes.push(shape);
      targets.push(shapes.length - 1);
    }

    // The kernel matrix over the rest pose and every sample, inverted, so that
    // standing on a sample reproduces its shape and nothing else's.
    const all = [{ x: 0, y: 0, z: 0, w: 1 }, ...samples];
    const matrix = all.map((one) => all.map((two) => kernel(angleBetween(one, two))));
    const weights = invert(matrix).map((row) => row.slice(1));
    correctives.push({ targets, bone: `upperarm_${side}`, samples, weights });
  }

  if (shapes.length === 0) return [];
  cached = { shapes, correctives };
  geometry.morphAttributes.position = shapes.map((shape) => new BufferAttribute(shape, 3));
  geometry.morphTargetsRelative = true;
  geometry.userData.shoulders = correctives;
  return correctives;
}
