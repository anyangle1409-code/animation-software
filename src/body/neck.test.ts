import { describe, expect, it } from 'vitest';
import { Euler, Vector3 } from 'three';
import { canonicalSkeleton } from '../rig/skeleton';
import { EULER_ORDER } from '../rig/types';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { exportGlb } from '../export/glb';
import { buildBodyGeometry } from './mesh';
import { buildEcorcheGeometry } from './ecorche';
import { buildSkinnedRig } from './skin';
import type { LedgeReport, NeckReport } from './neck';

/**
 * The head-to-neck junction.
 *
 * The source binds everything above 1.50 m in its own space to the head alone,
 * which leaves the neck driven by the skull and a hard weight boundary at the
 * nape. `correctNeckWeights` runs inside the shared geometry builder, so what is
 * under test here is the character the studio shows and the exporter writes —
 * not an Anatomy-mode copy of it.
 *
 * The deformation limits below were fixed before the weighting was tuned, from
 * what the surface has to survive rather than from what it happened to measure:
 * a 20° nod and a 25° turn are ordinary head movement, and an edge that grows by
 * a third, or loses two fifths of its length, is where a viewer starts to see
 * the skin slide. Versions that failed them were changed until they passed;
 * none was admitted by moving the line.
 */
const MOST_STRETCH = 1.3;
const LEAST_SQUASH = 0.6;

const skeleton = canonicalSkeleton;
/** The character as the studio and the exporter get it: repaired. */
const character = buildBodyGeometry(skeleton).geometry;
/** The same mesh with the repair switched off — the binding as the source encodes it. */
const source = buildBodyGeometry(skeleton, { repair: false }).geometry;
/** The same mesh with only the neck's own two repairs applied. */
const neckOnly = buildBodyGeometry(skeleton, { fins: false, shoulder: false }).geometry;
const anatomy = buildEcorcheGeometry(skeleton);
/**
 * The corrected surface carrying the source's own binding. The only way to ask
 * what the *weights* did to the arm now that the *positions* have moved too.
 */
const sameSurface = character.clone();
sameSurface.setAttribute('skinIndex', source.getAttribute('skinIndex').clone());
sameSurface.setAttribute('skinWeight', source.getAttribute('skinWeight').clone());
const report = character.userData.neck as NeckReport;

const position = character.getAttribute('position');
const index = character.getIndex()!;
const ledge = character.userData.ledge as LedgeReport;

/** The back of the neck, where the ledge was: the region under test. */
const nape = (vertex: number): boolean =>
  position.getZ(vertex) < -0.005 &&
  position.getY(vertex) > 1.34 &&
  position.getY(vertex) < 1.46 &&
  Math.abs(position.getX(vertex)) < 0.095;

interface Slots {
  getComponent(vertex: number, slot: number): number;
}

/** Bone name to weight, for one vertex. */
const weightsOf = (
  geometry: { getAttribute(name: string): Slots },
  vertex: number,
): Map<string, number> => {
  const bones = geometry.getAttribute('skinIndex');
  const shares = geometry.getAttribute('skinWeight');
  const out = new Map<string, number>();
  for (let slot = 0; slot < 4; slot += 1) {
    const share = shares.getComponent(vertex, slot);
    if (share <= 0) continue;
    const bone = skeleton.bones[bones.getComponent(vertex, slot)];
    if (bone) out.set(bone.name, (out.get(bone.name) ?? 0) + share);
  }
  return out;
};

/** The largest per-bone difference in weight between two vertices. */
const weightGap = (one: Map<string, number>, two: Map<string, number>): number => {
  let gap = 0;
  for (const bone of new Set([...one.keys(), ...two.keys()])) {
    gap = Math.max(gap, Math.abs((one.get(bone) ?? 0) - (two.get(bone) ?? 0)));
  }
  return gap;
};

/**
 * How much of a vertex the skull drives.
 *
 * This is the defect in one number. The source hands the surface from the head
 * to no head at all across a single edge, and the head is the bone that moves
 * furthest of any near the neck, so that step is where the skin has to tear. How
 * far apart two *other* bones are in a vertex's weights says nothing on its own
 * — the collarbone and the top of the spine hold still together — which is why
 * the pose tests below, not this one, are the acceptance measure.
 */
const skullShare = (geometry: { getAttribute(name: string): Slots }, vertex: number): number =>
  weightsOf(geometry, vertex).get('head') ?? 0;

/**
 * Vertices the neck's repair rewrote, measured against a build carrying only
 * that repair. The shoulder round rebinds the armpit on the same mesh, and this
 * file is about the neck.
 */
const corrected: number[] = [];
for (let vertex = 0; vertex < position.count; vertex += 1) {
  if (weightGap(weightsOf(neckOnly, vertex), weightsOf(source, vertex)) > 1e-6) {
    corrected.push(vertex);
  }
}
const touched = new Uint8Array(position.count);
for (const vertex of corrected) touched[vertex] = 1;

/** Every edge with at least one corrected end, so the repair's own boundary is in. */
const edges: [number, number][] = [];
{
  const seen = new Set<number>();
  for (let corner = 0; corner < index.count; corner += 3) {
    const ids = [index.getX(corner), index.getX(corner + 1), index.getX(corner + 2)];
    for (let slot = 0; slot < 3; slot += 1) {
      const one = ids[slot];
      const two = ids[(slot + 1) % 3];
      if (!touched[one] && !touched[two]) continue;
      const key = one < two ? one * position.count + two : two * position.count + one;
      if (seen.has(key)) continue;
      seen.add(key);
      edges.push([one, two]);
    }
  }
}

const here = new Vector3();
const there = new Vector3();
const restLength = edges.map(([one, two]) => {
  here.fromBufferAttribute(neckOnly.getAttribute('position'), one);
  there.fromBufferAttribute(neckOnly.getAttribute('position'), two);
  return here.distanceTo(there);
});

type Rig = ReturnType<typeof buildSkinnedRig>;

/** Nod and turn, in degrees, shared between the neck and the head. */
const holdNeck = (rig: Rig, nod: number, turn: number) => {
  for (const name of ['neck', 'head'] as const) {
    const bone = rig.boneByName.get(name);
    if (!bone) continue;
    // Half the movement each: the head follows the neck rather than hinging on
    // it alone, which is how a person looks around.
    bone.rotation.copy(
      new Euler(((nod / 2) * Math.PI) / 180, ((turn / 2) * Math.PI) / 180, 0, EULER_ORDER),
    );
  }
  rig.root.updateMatrixWorld(true);
  rig.skeleton.update();
};

/** The worst stretch and the worst squash across the junction, in one pose. */
const strain = (rig: Rig, from: typeof position): [number, number] => {
  let most = 1;
  let least = 1;
  edges.forEach(([one, two], slot) => {
    here.fromBufferAttribute(from, one);
    there.fromBufferAttribute(from, two);
    rig.mesh.applyBoneTransform(one, here);
    rig.mesh.applyBoneTransform(two, there);
    const ratio = here.distanceTo(there) / restLength[slot];
    most = Math.max(most, ratio);
    least = Math.min(least, ratio);
  });
  return [most, least];
};

const NODS: [string, number, number][] = [
  ['neutral', 0, 0],
  ['flexion', 20, 0],
  ['extension', -20, 0],
  ['turned left', 0, 25],
  ['turned right', 0, -25],
  ['flexed and turned', 15, 20],
];

describe('the head-to-neck junction', () => {
  it('rewrites the binding the source left rigid', () => {
    expect(corrected.length).toBeGreaterThan(1000);
    expect(report.reweighted).toBe(corrected.length);
    // Most of what it touched was head:1.00 before, which is the defect itself.
    expect(report.fromHeadAlone).toBeGreaterThan(report.reweighted * 0.8);
    expect(report.fromHeadAlone).toBeLessThanOrEqual(report.reweighted);
    // And a much smaller set out on the shoulders, where the source gave the
    // neck bone a share of surface up to 170 mm off its own axis.
    expect(report.sideways).toBeGreaterThan(50);
    expect(report.sideways).toBeLessThan(report.reweighted * 0.2);
  });

  it('leaves every vertex on two bones that still sum to one', () => {
    for (const geometry of [character, anatomy]) {
      const shares = geometry.getAttribute('skinWeight');
      const bones = geometry.getAttribute('skinIndex');
      for (let vertex = 0; vertex < shares.count; vertex += 1) {
        const seen = new Set<number>();
        let total = 0;
        let used = 0;
        for (let slot = 0; slot < 4; slot += 1) {
          const share = shares.getComponent(vertex, slot);
          expect(share, `vertex ${vertex} slot ${slot}`).toBeGreaterThanOrEqual(0);
          expect(share, `vertex ${vertex} slot ${slot}`).toBeLessThanOrEqual(1);
          total += share;
          if (share <= 0) continue;
          used += 1;
          const bone = bones.getComponent(vertex, slot);
          // A bone named twice in one vertex sums to more influence than the
          // renormalisation accounts for.
          expect(seen.has(bone), `vertex ${vertex} repeats a bone`).toBe(false);
          seen.add(bone);
        }
        expect(used, `vertex ${vertex} influences`).toBeLessThanOrEqual(2);
        expect(total, `vertex ${vertex}`).toBeCloseTo(1, 4);
      }
    }
  });

  it('hands the surface over by position rather than in a step', () => {
    let worstBefore = 0;
    let worstAfter = 0;
    for (const [one, two] of edges) {
      worstBefore = Math.max(
        worstBefore,
        Math.abs(skullShare(source, one) - skullShare(source, two)),
      );
      worstAfter = Math.max(
        worstAfter,
        Math.abs(skullShare(neckOnly, one) - skullShare(neckOnly, two)),
      );
    }
    // The source's boundary is a cliff: head:1.00 beside a vertex with no head
    // weight at all. The repair has to be visibly better than it.
    expect(worstBefore).toBeGreaterThan(0.9);
    expect(worstAfter).toBeLessThan(0.5);
    expect(worstAfter).toBeLessThan(worstBefore * 0.6);
  });

  it('treats both sides of the neck the same', () => {
    const mirror = new Map<string, number>();
    const key = (x: number, y: number, z: number) =>
      `${Math.round(x * 1e4)},${Math.round(y * 1e4)},${Math.round(z * 1e4)}`;
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      mirror.set(key(position.getX(vertex), position.getY(vertex), position.getZ(vertex)), vertex);
    }

    let checked = 0;
    for (const vertex of corrected) {
      const x = position.getX(vertex);
      if (x >= 0) continue;
      const twin = mirror.get(key(-x, position.getY(vertex), position.getZ(vertex)));
      if (twin === undefined) continue;
      checked += 1;
      const flipped = new Map<string, number>();
      for (const [bone, share] of weightsOf(neckOnly, twin)) {
        flipped.set(
          bone.endsWith('_r')
            ? `${bone.slice(0, -2)}_l`
            : bone.endsWith('_l')
              ? `${bone.slice(0, -2)}_r`
              : bone,
          share,
        );
      }
      expect(
        weightGap(weightsOf(neckOnly, vertex), flipped),
        `vertex ${vertex} against its mirror`,
      ).toBeLessThan(0.02);
    }
    expect(checked, 'mirrored pairs found').toBeGreaterThan(200);
  });

  it('holds together through the head movement it has to survive', () => {
    const rig = buildSkinnedRig(skeleton, { geometry: neckOnly });
    const plain = buildSkinnedRig(skeleton, { geometry: source });
    const sourcePosition = source.getAttribute('position');

    for (const [name, nod, turn] of NODS) {
      holdNeck(rig, nod, turn);
      holdNeck(plain, nod, turn);
      const [most, least] = strain(rig, neckOnly.getAttribute('position'));
      const [wasMost, wasLeast] = strain(plain, sourcePosition);

      expect(most, `${name} stretch`).toBeLessThanOrEqual(MOST_STRETCH);
      expect(least, `${name} squash`).toBeGreaterThanOrEqual(LEAST_SQUASH);
      // Wherever the source broke a limit, the repair has to beat it there —
      // not merely differ. Where the source stayed inside one it is no standard
      // to beat: a rigid neck travels with the skull and barely deforms at all,
      // and a neck that actually bends has to compress at the throat.
      if (wasMost > MOST_STRETCH) {
        expect(most, `${name} stretch against the source`).toBeLessThan(wasMost);
      }
      if (wasLeast < LEAST_SQUASH) {
        expect(least, `${name} squash against the source`).toBeGreaterThan(wasLeast);
      }
    }
  });

  it('repaints nothing, and moves only the back of the neck', () => {
    const fixed = neckOnly.getAttribute('color');
    const was = source.getAttribute('color');
    for (let slot = 0; slot < fixed.count * fixed.itemSize; slot += 1) {
      if ((fixed.array as ArrayLike<number>)[slot] !== (was.array as ArrayLike<number>)[slot]) {
        throw new Error(`colour changed at ${slot}`);
      }
    }

    const before = source.getAttribute('position');
    const after = neckOnly.getAttribute('position');
    let moved = 0;
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      // Depth only. The face, the jaw, the ears and the hairline are above the
      // region, the throat is on the other side of the neck, and the chest and
      // the outer shoulders are outside it — so nothing there may move at all,
      // and nothing anywhere may move sideways or vertically.
      expect(after.getX(vertex), `vertex ${vertex} sideways`).toBe(before.getX(vertex));
      expect(after.getY(vertex), `vertex ${vertex} vertically`).toBe(before.getY(vertex));
      const depth = after.getZ(vertex) - before.getZ(vertex);
      if (Math.abs(depth) < 1e-6) continue;
      moved += 1;
      expect(nape(vertex), `vertex ${vertex} is outside the nape`).toBe(true);
      // Backwards, towards the nape, never forwards into the neck.
      expect(depth, `vertex ${vertex}`).toBeLessThan(0);
    }
    expect(moved).toBe(ledge.moved);
    expect(ledge.maxDisplacement).toBeLessThan(ledge.step);
  });

  it('closes the ledge into a slope, symmetrically', () => {
    const before = source.getAttribute('position');
    const position = neckOnly.getAttribute('position');
    const shifted = new Map<number, number>();
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      const depth = position.getZ(vertex) - before.getZ(vertex);
      if (Math.abs(depth) > 1e-6) shifted.set(vertex, depth);
    }
    expect(shifted.size).toBeGreaterThan(20);

    // Mirrored: every moved vertex has a twin across the midline moved by the
    // same amount, because the correction is measured in bands keyed on |x|.
    const key = (x: number, y: number, z: number) =>
      `${Math.round(x * 1e5)},${Math.round(y * 1e5)},${Math.round(z * 1e5)}`;
    const at = new Map<string, number>();
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      at.set(key(before.getX(vertex), before.getY(vertex), before.getZ(vertex)), vertex);
    }
    for (const [vertex, depth] of shifted) {
      const twin = at.get(key(-before.getX(vertex), before.getY(vertex), before.getZ(vertex)));
      expect(twin, `vertex ${vertex} has no mirror`).toBeDefined();
      expect(shifted.get(twin!) ?? 0, `vertex ${vertex} against its mirror`).toBeCloseTo(depth, 6);
    }

    // The ledge itself: down the midline the surface stepped back 34 mm across
    // one 13 mm row. It now descends from the nape in steps no bigger than the
    // rows either side of it.
    const midline = (from: typeof position) => {
      const rows: { y: number; z: number }[] = [];
      for (let vertex = 0; vertex < from.count; vertex += 1) {
        if (Math.abs(from.getX(vertex)) > 0.014) continue;
        if (from.getZ(vertex) > -0.005 || from.getY(vertex) < 1.33 || from.getY(vertex) > 1.45) continue;
        rows.push({ y: from.getY(vertex), z: from.getZ(vertex) });
      }
      rows.sort((one, two) => one.y - two.y);
      let worst = 0;
      for (let slot = 1; slot < rows.length; slot += 1) {
        if (rows[slot].y - rows[slot - 1].y < 1e-4) continue;
        worst = Math.max(worst, Math.abs(rows[slot].z - rows[slot - 1].z));
      }
      return worst;
    };
    expect(midline(before)).toBeGreaterThan(0.03);
    expect(midline(position)).toBeLessThan(0.012);
  });

  it('turns no triangle over and pinches none into a sliver', () => {
    const before = source.getAttribute('position');
    const position = neckOnly.getAttribute('position');
    const corner = [new Vector3(), new Vector3(), new Vector3()];
    const other = [new Vector3(), new Vector3(), new Vector3()];
    const edge = new Vector3();
    const rest = new Vector3();
    const now = new Vector3();
    const was = new Vector3();
    let checked = 0;

    for (let start = 0; start < index.count; start += 3) {
      const ids = [index.getX(start), index.getX(start + 1), index.getX(start + 2)];
      for (let slot = 0; slot < 3; slot += 1) {
        corner[slot].fromBufferAttribute(position, ids[slot]);
        other[slot].fromBufferAttribute(before, ids[slot]);
      }
      was.crossVectors(edge.subVectors(other[1], other[0]), rest.subVectors(other[2], other[0]));
      if (was.lengthSq() < 1e-18) continue;
      now.crossVectors(edge.subVectors(corner[1], corner[0]), rest.subVectors(corner[2], corner[0]));
      checked += 1;
      expect(now.dot(was), `triangle at ${start}`).toBeGreaterThan(0);
      expect(now.length() / was.length(), `triangle at ${start}`).toBeGreaterThan(0.25);
    }
    expect(checked).toBeGreaterThan(20000);
  });

  it('gives the anatomy view the same corrected base as the character', () => {
    expect(anatomy.getAttribute('skinWeight').count).toBe(position.count);
    // The anatomy view sculpts relief on top, but it starts from the corrected
    // surface: every vertex the ledge correction moved arrives already moved,
    // rather than being levelled a second time by a mode-private pass.
    const sculpted = anatomy.getAttribute('position');
    const before = source.getAttribute('position');
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (Math.abs(position.getZ(vertex) - before.getZ(vertex)) < 1e-6) continue;
      const shared = position.getZ(vertex) - before.getZ(vertex);
      const inherited = sculpted.getZ(vertex) - before.getZ(vertex);
      // Within the relief's own bounded displacement of the shared correction.
      expect(Math.abs(inherited - shared), `vertex ${vertex}`).toBeLessThan(0.006);
    }
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      // The elbow is the one place the anatomy view deliberately rebinds, and it
      // is nowhere near the neck.
      if (position.getY(vertex) < 1.3) continue;
      expect(
        weightGap(weightsOf(character, vertex), weightsOf(anatomy, vertex)),
        `vertex ${vertex}`,
      ).toBeLessThan(1e-6);
    }
  });

  it('writes the corrected weights into the exported glb', async () => {
    const blob = await exportGlb(generateClip(skeleton, bicepCurl), bicepCurl, { fps: 10 });
    const buffer = await blob.arrayBuffer();
    const view = new DataView(buffer);
    const jsonLength = view.getUint32(12, true);
    const gltf = JSON.parse(
      new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength)),
    ) as {
      accessors: { bufferView: number; byteOffset?: number; count: number }[];
      bufferViews: { byteOffset: number; byteLength: number }[];
      meshes: { primitives: { attributes: Record<string, number> }[] }[];
      nodes: { name?: string }[];
      skins: { joints: number[] }[];
    };
    const binary = 20 + jsonLength + 8;

    const at = (accessor: number) => {
      const entry = gltf.accessors[accessor];
      const region = gltf.bufferViews[entry.bufferView];
      return [binary + region.byteOffset + (entry.byteOffset ?? 0), entry.count] as const;
    };
    const attributes = gltf.meshes[0].primitives[0].attributes;
    const [jointsAt, jointCount] = at(attributes.JOINTS_0);
    const [sharesAt] = at(attributes.WEIGHTS_0);
    const [pointsAt, pointCount] = at(attributes.POSITION);
    const joints = new Uint16Array(buffer, jointsAt, jointCount * 4);
    const shares = new Float32Array(buffer, sharesAt, jointCount * 4);
    const points = new Float32Array(buffer, pointsAt, pointCount * 3);
    const boneOf = gltf.skins[0].joints.map((node) => gltf.nodes[node].name ?? '');

    expect(jointCount).toBe(position.count);
    // The exported surface is the corrected surface, vertex for vertex — the
    // ledge correction has to reach the file, not just the viewport.
    let exportedMoves = 0;
    const before = source.getAttribute('position');
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      expect(points[vertex * 3], `exported vertex ${vertex} x`).toBeCloseTo(position.getX(vertex), 6);
      expect(points[vertex * 3 + 1], `exported vertex ${vertex} y`).toBeCloseTo(position.getY(vertex), 6);
      expect(points[vertex * 3 + 2], `exported vertex ${vertex} z`).toBeCloseTo(position.getZ(vertex), 6);
      if (nape(vertex) && Math.abs(points[vertex * 3 + 2] - before.getZ(vertex)) > 1e-6) {
        exportedMoves += 1;
      }
    }
    expect(exportedMoves, 'corrected depths present in the file').toBeGreaterThanOrEqual(ledge.moved);

    let checked = 0;
    for (const vertex of corrected) {
      const written = new Map<string, number>();
      for (let slot = 0; slot < 4; slot += 1) {
        const share = shares[vertex * 4 + slot];
        if (share <= 0) continue;
        const bone = boneOf[joints[vertex * 4 + slot]];
        written.set(bone, (written.get(bone) ?? 0) + share);
      }
      expect(
        weightGap(written, weightsOf(character, vertex)),
        `exported vertex ${vertex}`,
      ).toBeLessThan(1e-5);
      // And genuinely different from what the source held, which is the point.
      if (weightGap(weightsOf(source, vertex), weightsOf(character, vertex)) > 0.05) {
        expect(
          weightGap(written, weightsOf(source, vertex)),
          `exported vertex ${vertex}`,
        ).toBeGreaterThan(0.04);
        checked += 1;
      }
    }
    expect(checked, 'exported vertices carrying a real correction').toBeGreaterThan(500);
  });

  it('keeps every triangle in the junction facing the way it did', () => {
    // The anatomy view levels the vertical step the generator baked into the
    // nape, and moving vertices up and down is exactly the way to turn a shallow
    // triangle over. The character's own surface is the reference.
    const sculpted = anatomy.getAttribute('position');
    const corner = [new Vector3(), new Vector3(), new Vector3()];
    const other = [new Vector3(), new Vector3(), new Vector3()];
    const edge = new Vector3();
    const rest = new Vector3();
    const normal = new Vector3();
    const wasNormal = new Vector3();
    let checked = 0;

    for (let start = 0; start < index.count; start += 3) {
      const ids = [index.getX(start), index.getX(start + 1), index.getX(start + 2)];
      if (!ids.some((vertex) => nape(vertex))) continue;
      for (let slot = 0; slot < 3; slot += 1) {
        corner[slot].fromBufferAttribute(sculpted, ids[slot]);
        other[slot].fromBufferAttribute(position, ids[slot]);
      }
      normal.crossVectors(
        edge.subVectors(corner[1], corner[0]),
        rest.subVectors(corner[2], corner[0]),
      );
      wasNormal.crossVectors(
        edge.subVectors(other[1], other[0]),
        rest.subVectors(other[2], other[0]),
      );
      if (normal.lengthSq() < 1e-18 || wasNormal.lengthSq() < 1e-18) continue;
      checked += 1;
      expect(normal.normalize().dot(wasNormal.normalize()), `triangle at ${start}`).toBeGreaterThan(
        0,
      );
    }
    expect(checked).toBeGreaterThan(100);
  });

  it('changes nothing above the jaw', () => {
    const sculpted = anatomy.getAttribute('position');
    for (let vertex = 0; vertex < position.count; vertex += 1) {
      if (position.getY(vertex) < 1.56) continue;
      expect(sculpted.getX(vertex), `vertex ${vertex}`).toBe(position.getX(vertex));
      expect(sculpted.getY(vertex), `vertex ${vertex}`).toBe(position.getY(vertex));
      expect(sculpted.getZ(vertex), `vertex ${vertex}`).toBe(position.getZ(vertex));
    }
  });
});
