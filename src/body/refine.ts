import { BufferAttribute, BufferGeometry } from 'three';

/**
 * Local refinement of a skinned surface.
 *
 * The anatomy view needs more surface than the character has, but only in a few
 * places: an elbow ring with a dozen vertices around it folds into a wedge at
 * high flexion no matter how the muscle relief is authored, because there is
 * nothing there to fold *with*. Subdividing the whole body to fix an elbow
 * would quadruple 27,460 triangles to buy detail on a shin nobody is looking at,
 * so this refines a named region and leaves the rest of the mesh exactly as it
 * was.
 *
 * The split is red-green. Every triangle in the region has all three edges split
 * and becomes four (red); a triangle just outside it that ends up with one split
 * edge is halved (green) so the two meshes still share whole edges. Without that
 * closure the boundary would carry T-junctions, and a T-junction is a crack that
 * opens as soon as the surface deforms.
 *
 * Original vertices keep their indices, so anything that referred to a vertex of
 * the character's own mesh still refers to the same point afterwards.
 *
 * Written, tested, and currently switched off at its call site in
 * `body/ecorche.ts`. It was built to fix the elbow's high-flexion fold, and the
 * measurements said not to use it there: most of the surface contact at 126° is
 * the upper arm meeting the forearm rather than anything about the elbow ring's
 * density, and adding surface to a crowded crease makes crossings more numerous.
 * See the note at the top of `body/elbow.ts`. It stays here because the shoulder
 * cap and the forearm may still want it for contour rather than for deformation.
 */

/** A vertex the region includes. Triangles are refined if any corner is in it. */
export type RegionTest = (vertex: number) => boolean;

interface Blend {
  bones: number[];
  weights: number[];
}

/** The four strongest influences, renormalised — the format the mesh stores. */
function mergeSkin(a: Blend, b: Blend): Blend {
  const total = new Map<number, number>();
  for (const source of [a, b]) {
    for (let slot = 0; slot < source.bones.length; slot += 1) {
      const weight = source.weights[slot];
      if (weight <= 0) continue;
      total.set(source.bones[slot], (total.get(source.bones[slot]) ?? 0) + weight * 0.5);
    }
  }
  const ranked = [...total.entries()].sort((one, two) => two[1] - one[1]).slice(0, 4);
  const sum = ranked.reduce((carry, [, weight]) => carry + weight, 0) || 1;
  return {
    bones: ranked.map(([bone]) => bone),
    weights: ranked.map(([, weight]) => weight / sum),
  };
}

export function refineRegion(geometry: BufferGeometry, inRegion: RegionTest): BufferGeometry {
  const index = geometry.getIndex();
  if (!index) return geometry;

  const position = geometry.getAttribute('position');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const colour = geometry.getAttribute('color');
  const count = position.count;
  const triangles = index.count / 3;

  const corners = (triangle: number): [number, number, number] => [
    index.getX(triangle * 3),
    index.getX(triangle * 3 + 1),
    index.getX(triangle * 3 + 2),
  ];

  // Edges are keyed on the ordered pair, which stays inside a safe integer for
  // any mesh this project will ever hold.
  const edgeKey = (a: number, b: number): number => (a < b ? a * count + b : b * count + a);

  const red = new Uint8Array(triangles);
  const split = new Set<number>();
  const markRed = (triangle: number) => {
    red[triangle] = 1;
    const [a, b, c] = corners(triangle);
    split.add(edgeKey(a, b)).add(edgeKey(b, c)).add(edgeKey(c, a));
  };

  for (let triangle = 0; triangle < triangles; triangle += 1) {
    const [a, b, c] = corners(triangle);
    if (inRegion(a) || inRegion(b) || inRegion(c)) markRed(triangle);
  }

  // Closure: a triangle with two split edges cannot be halved cleanly, so it
  // joins the region. Promoting it splits its third edge, which can pull in a
  // neighbour, so this runs to a fixed point.
  for (let pass = 0; pass < 12; pass += 1) {
    let changed = false;
    for (let triangle = 0; triangle < triangles; triangle += 1) {
      if (red[triangle]) continue;
      const [a, b, c] = corners(triangle);
      const cut =
        (split.has(edgeKey(a, b)) ? 1 : 0) +
        (split.has(edgeKey(b, c)) ? 1 : 0) +
        (split.has(edgeKey(c, a)) ? 1 : 0);
      if (cut >= 2) {
        markRed(triangle);
        changed = true;
      }
    }
    if (!changed) break;
  }

  const positions: number[] = [];
  const bones: number[] = [];
  const weights: number[] = [];
  const colours: number[] = [];
  const source = colour.array as ArrayLike<number>;
  const midpoints = new Map<number, number>();

  const blendOf = (vertex: number): Blend => ({
    bones: [0, 1, 2, 3].map((slot) => skinIndex.getComponent(vertex, slot)),
    weights: [0, 1, 2, 3].map((slot) => skinWeight.getComponent(vertex, slot)),
  });

  const midpoint = (a: number, b: number): number => {
    const key = edgeKey(a, b);
    const existing = midpoints.get(key);
    if (existing !== undefined) return existing;

    const created = count + positions.length / 3;
    positions.push(
      (position.getX(a) + position.getX(b)) / 2,
      (position.getY(a) + position.getY(b)) / 2,
      (position.getZ(a) + position.getZ(b)) / 2,
    );
    const blend = mergeSkin(blendOf(a), blendOf(b));
    for (let slot = 0; slot < 4; slot += 1) {
      bones.push(blend.bones[slot] ?? 0);
      weights.push(blend.weights[slot] ?? 0);
    }
    for (let channel = 0; channel < 3; channel += 1) {
      colours.push(Math.round((source[a * 3 + channel] + source[b * 3 + channel]) / 2));
    }
    midpoints.set(key, created);
    return created;
  };

  const out: number[] = [];
  for (let triangle = 0; triangle < triangles; triangle += 1) {
    const [a, b, c] = corners(triangle);
    if (red[triangle]) {
      const ab = midpoint(a, b);
      const bc = midpoint(b, c);
      const ca = midpoint(c, a);
      out.push(a, ab, ca, ab, b, bc, ca, bc, c, ab, bc, ca);
      continue;
    }
    // At most one edge is split by now, so a halving keeps the surface watertight.
    const edges: [number, number, number][] = [
      [a, b, c],
      [b, c, a],
      [c, a, b],
    ];
    const cut = edges.find(([one, two]) => split.has(edgeKey(one, two)));
    if (!cut) {
      out.push(a, b, c);
      continue;
    }
    const [one, two, apex] = cut;
    const middle = midpoint(one, two);
    out.push(one, middle, apex, middle, two, apex);
  }

  const added = positions.length / 3;
  const total = count + added;
  const outPosition = new Float32Array(total * 3);
  const outBones = new Uint16Array(total * 4);
  const outWeights = new Float32Array(total * 4);
  const outColours = new Uint8Array(total * 3);

  for (let vertex = 0; vertex < count; vertex += 1) {
    outPosition[vertex * 3] = position.getX(vertex);
    outPosition[vertex * 3 + 1] = position.getY(vertex);
    outPosition[vertex * 3 + 2] = position.getZ(vertex);
    for (let slot = 0; slot < 4; slot += 1) {
      outBones[vertex * 4 + slot] = skinIndex.getComponent(vertex, slot);
      outWeights[vertex * 4 + slot] = skinWeight.getComponent(vertex, slot);
    }
    for (let channel = 0; channel < 3; channel += 1) {
      outColours[vertex * 3 + channel] = source[vertex * 3 + channel];
    }
  }
  outPosition.set(positions, count * 3);
  outBones.set(bones, count * 4);
  outWeights.set(weights, count * 4);
  outColours.set(colours, count * 3);

  const refined = new BufferGeometry();
  refined.setAttribute('position', new BufferAttribute(outPosition, 3));
  refined.setAttribute('skinIndex', new BufferAttribute(outBones, 4));
  refined.setAttribute('skinWeight', new BufferAttribute(outWeights, 4));
  refined.setAttribute('color', new BufferAttribute(outColours, 3, true));
  refined.setIndex(new BufferAttribute(new Uint32Array(out), 1));
  refined.computeVertexNormals();
  refined.computeBoundingBox();
  refined.computeBoundingSphere();
  return refined;
}
