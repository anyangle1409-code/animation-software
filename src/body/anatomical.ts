import { BufferAttribute, BufferGeometry } from 'three';
import type { Skeleton } from '../rig/skeleton';
import { correctNeckLedge, correctNeckWeights } from './neck';
import { buildArmpitCorrectives, correctArmpitWeights, smoothShoulderFins } from './shoulder';
import { shapeHead } from './head';
import { canonicalSkeleton } from '../rig/skeleton';
import { ANATOMICAL_COLOURS } from './anatomicalColours';
import { ANATOMICAL_INDICES } from './anatomicalIndices';
import { ANATOMICAL_TRIANGLE_COUNT, ANATOMICAL_VERTEX_COUNT } from './anatomicalMeta';
import { SHOULDER_SETBACK, SHOULDER_WIDENING } from '../rig/humanoid';
import { ANATOMICAL_POSITIONS } from './anatomicalPositions';
import { ANATOMICAL_SKIN_INDICES } from './anatomicalSkinIndices';
import { ANATOMICAL_SKIN_WEIGHTS } from './anatomicalSkinWeights';
import type { BodyGeometry } from './mesh';

export { ANATOMICAL_PALETTE } from './anatomicalPalette';

const bytes = (encoded: string): Uint8Array => {
  const decoded = atob(encoded);
  const result = new Uint8Array(decoded.length);
  for (let index = 0; index < decoded.length; index += 1) result[index] = decoded.charCodeAt(index);
  return result;
};

const float32 = (encoded: string): Float32Array => new Float32Array(bytes(encoded).buffer);
const uint16 = (encoded: string): Uint16Array => new Uint16Array(bytes(encoded).buffer);

/**
 * The bones `ANATOMICAL_SKIN_INDICES` numbers, in the order it numbers them.
 *
 * The baked skin stores each influence as a position in the rig's bone list,
 * and that list was the 53-bone rig's when it was generated. Positions are not
 * a stable name for a bone: inserting the scapulae after the clavicles shifted
 * every bone below them, and read positionally the baked skin would have bound
 * 8,387 of the 13,952 vertices to the wrong bone. So the positions are resolved
 * to names through this table and then to whatever index the rig in use gives
 * each name. The table is data about the baked file and must never be edited
 * to follow the rig; it changes only if the skin itself is re-baked.
 */
export const ANATOMICAL_SKIN_BONES: readonly string[] = [
  'root', 'pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck', 'head', 'clavicle_l', 'upperarm_l',
  'forearm_l', 'hand_l', 'thigh_l', 'shin_l', 'foot_l', 'toe_l', 'thumb_01_l', 'thumb_02_l',
  'thumb_03_l', 'index_01_l', 'index_02_l', 'index_03_l', 'middle_01_l', 'middle_02_l',
  'middle_03_l', 'ring_01_l', 'ring_02_l', 'ring_03_l', 'pinky_01_l', 'pinky_02_l', 'pinky_03_l',
  'clavicle_r', 'upperarm_r', 'forearm_r', 'hand_r', 'thigh_r', 'shin_r', 'foot_r', 'toe_r',
  'thumb_01_r', 'thumb_02_r', 'thumb_03_r', 'index_01_r', 'index_02_r', 'index_03_r',
  'middle_01_r', 'middle_02_r', 'middle_03_r', 'ring_01_r', 'ring_02_r', 'ring_03_r', 'pinky_01_r',
  'pinky_02_r', 'pinky_03_r',
];

/** The baked influences, renumbered for `rig` by bone name. */
function skinIndicesFor(rig: Skeleton): Uint16Array {
  const baked = uint16(ANATOMICAL_SKIN_INDICES);
  const slots = ANATOMICAL_SKIN_BONES.map((name) => {
    if (!rig.has(name)) {
      throw new Error(`The anatomical skin binds to "${name}", which this rig does not have.`);
    }
    return rig.bone(name).index;
  });
  for (let entry = 0; entry < baked.length; entry += 1) baked[entry] = slots[baked[entry]];
  return baked;
}

/** Build the reproducible anatomical surface in the canonical rig's bind pose. */
export interface AnatomicalOptions {
  /**
   * The shared repairs, all of them. Off gives the surface exactly as the
   * source encodes it, which is what the before-and-after tests measure
   * against.
   */
  repair?: boolean;
  /** The skull's proportions, the eyes and the hair. */
  head?: boolean;
  /** The head-to-neck binding and the ledge at the nape. */
  neck?: boolean;
  /** The folds at the neck-to-shoulder junction. */
  fins?: boolean;
  /** The armpit's binding and the shoulder correctives. */
  shoulder?: boolean;
}

/**
 * Carry the shoulder widening and setback into the baked surface.
 *
 * The bones moved outward; this surface is baked against where they used to be,
 * so without this the arm hangs off a shoulder no longer under it — the
 * measured symptom was upper-arm girth collapsing from 97 mm to 30 mm, because
 * girth is read as the arm's own width beyond the shoulder head.
 *
 * The transition has to spread over several edges. The shift is 33.7 mm and the
 * median shoulder edge is 7 mm, so any mask that turns over within one edge
 * moves its two ends past each other and inverts it: shifting by raw skin
 * weight took the worst edge to 5.5% of its rest length against a 10% floor.
 * Averaging the weight field was worse still and bled the shift up into the
 * neck. So the field is built by graph distance instead — vertices the arm owns
 * outright are held at 1, and the rest ramps to 0 over HOPS edges of the
 * surface, smooth by construction rather than by averaging.
 *
 * The band is local to the shoulder seam and decays to nothing well before the
 * chest, waist and ribcage the reference already places within tolerance, so
 * the torso is not widened and no belly is scaled. Measured at HOPS = 2 the
 * shoulder's worst and tightest edge strains both come out BETTER than leaving
 * the surface unshifted (5.215 against 5.308, and 0.1580 against 0.1324).
 *
 * Applied at build time rather than re-baked: the encoded arrays stay as
 * authored and one constant drives the rig, the character and this surface.
 *
 * The clavicle's corrected rest angle is the same problem in the other axis and
 * takes the same treatment. It moved the arm chain SHOULDER_SETBACK behind the
 * old centre line, and left unshifted the surface stayed put: measured, the
 * upper-arm bone ended up 38.7 mm behind the middle of its own arm surface,
 * where it had been within 3.7 mm. Everything downstream reads that gap — the
 * arm/torso blend strains over a joint that is no longer inside it, the muscle
 * map loses vertices it should claim, and the ecorche sculpt displaces from a
 * belly sitting off-centre.
 *
 * The same field drives both. Widening is handed, so it uses the signed field;
 * the setback is not — both arms move the same way — so it uses its magnitude.
 */
function realignArmSurface(
  rig: Skeleton,
  position: BufferAttribute,
  joints: BufferAttribute,
  weights: BufferAttribute,
  index: BufferAttribute,
): void {
  const arm = /^(upperarm|forearm|hand|thumb|index|middle|ring|pinky)_(l|r)$|^(thumb|index|middle|ring|pinky)_0[123]_(l|r)$/;
  const side = rig.bones.map((bone) => (arm.test(bone.name) ? (bone.name.endsWith('_l') ? -1 : 1) : 0));
  const share = new Float32Array(position.count);
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    let signed = 0;
    let total = 0;
    for (let lane = 0; lane < 4; lane += 1) {
      const weight = weights.getComponent(vertex, lane);
      if (weight <= 0) continue;
      total += weight;
      signed += weight * (side[joints.getComponent(vertex, lane)] ?? 0);
    }
    share[vertex] = total > 0 ? signed / total : 0;
  }

  const neighbours: number[][] = Array.from({ length: position.count }, () => []);
  for (let triangle = 0; triangle < index.count; triangle += 3) {
    const a = index.getX(triangle);
    const b = index.getX(triangle + 1);
    const c = index.getX(triangle + 2);
    neighbours[a].push(b, c);
    neighbours[b].push(a, c);
    neighbours[c].push(a, b);
  }

  /** The signed 1-to-0 ramp off the arm, over `hops` edges of the surface. */
  const rampField = (hops: number): Float32Array => {
    const field = new Float32Array(position.count);
    for (const sign of [-1, 1]) {
      const hop = new Int32Array(position.count).fill(-1);
      let frontier: number[] = [];
      for (let vertex = 0; vertex < position.count; vertex += 1) {
        if (share[vertex] * sign < 0.95) continue;
        hop[vertex] = 0;
        frontier.push(vertex);
      }
      for (let distance = 1; distance <= hops && frontier.length; distance += 1) {
        const next: number[] = [];
        for (const vertex of frontier)
          for (const other of neighbours[vertex]) {
            if (hop[other] !== -1) continue;
            // Never ramp across the body's midline into the other side.
            if (position.getX(other) * sign < 0) continue;
            hop[other] = distance;
            next.push(other);
          }
        frontier = next;
      }
      for (let vertex = 0; vertex < position.count; vertex += 1) {
        if (hop[vertex] < 0) continue;
        const t = 1 - hop[vertex] / (hops + 1);
        // Smoothstep, so the band meets the arm and the torso with zero gradient.
        field[vertex] += sign * t * t * (3 - 2 * t);
      }
    }
    return field;
  };

  // Both shifts ride the same 2-hop band. Giving the setback a wider band of its
  // own was measured across 3 to 18 hops and rejected: it buys little on the
  // worst shoulder edge (6.34x at 2 hops against 5.91x at 12) and every width
  // past 2 breaks something the narrow band leaves alone — the arm's own
  // declared limits at 3 and 4, the neck-to-shoulder folds at 6, and the nape
  // ledge and head-turn strain by 12, which is the bleed into the neck this
  // function's own history warns about. The band stays where it was proven.
  const field = rampField(2);
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (field[vertex] === 0) continue;
    position.setX(vertex, position.getX(vertex) + field[vertex] * SHOULDER_WIDENING);
    position.setZ(vertex, position.getZ(vertex) - Math.abs(field[vertex]) * SHOULDER_SETBACK);
  }
}

export function buildAnatomicalBodyGeometry(
  rig: Skeleton = canonicalSkeleton,
  options: AnatomicalOptions = {},
): BodyGeometry {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(float32(ANATOMICAL_POSITIONS), 3));
  geometry.setAttribute('skinIndex', new BufferAttribute(skinIndicesFor(rig), 4));
  geometry.setAttribute('skinWeight', new BufferAttribute(float32(ANATOMICAL_SKIN_WEIGHTS), 4));
  geometry.setIndex(new BufferAttribute(uint16(ANATOMICAL_INDICES), 1));
  realignArmSurface(
    rig,
    geometry.getAttribute('position') as BufferAttribute,
    geometry.getAttribute('skinIndex') as BufferAttribute,
    geometry.getAttribute('skinWeight') as BufferAttribute,
    geometry.getIndex() as BufferAttribute,
  );
  geometry.setAttribute('color', new BufferAttribute(bytes(ANATOMICAL_COLOURS), 3, true));
  geometry.setIndex(new BufferAttribute(uint16(ANATOMICAL_INDICES), 1));
  // The source binds everything above 1.50 m in its own space to the head alone.
  // That leaves the neck rigid with the skull, and it carries the head through a
  // different conversion transform from the surface below it, which leaves a
  // ledge at the nape. Both are repaired here, once, so the character, the
  // anatomy view and the GLB export share one corrected base surface.
  const repair = options.repair !== false;
  if (repair && options.head !== false) {
    // The head first: it only moves head-owned surface, and the neck repair
    // below reads the source's head binding, which this does not touch.
    geometry.userData.head = shapeHead(geometry, rig);
  }
  if (repair && options.neck !== false) {
    // Positions before weights: the ledge is found from the source's own head
    // binding, which the weight repair is about to rewrite.
    geometry.userData.ledge = correctNeckLedge(geometry, rig);
  }
  if (repair && options.fins !== false) {
    geometry.userData.fins = smoothShoulderFins(geometry);
  }
  if (repair && options.neck !== false) {
    geometry.userData.neck = correctNeckWeights(geometry, rig);
  }
  if (repair && options.shoulder !== false) {
    geometry.userData.armpit = correctArmpitWeights(geometry, rig);
    buildArmpitCorrectives(geometry, rig);
  }
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return { geometry, vertices: ANATOMICAL_VERTEX_COUNT, triangles: ANATOMICAL_TRIANGLE_COUNT };
}
