import { Vector3 } from 'three';
import type { BufferGeometry } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { restPose } from '../rig/pose';
import type { BoneName, Side } from '../rig/boneNames';
import { boneInfluence, smoothstep } from './skinning';

/**
 * The elbow corrective.
 *
 * Linear blend skinning has one failure it cannot avoid: as a joint closes, the
 * vertices around it are averaged between two transforms that are pointing in
 * very different directions, and the average falls *inside* the arm. The inside
 * of the elbow loses the roll of flesh that should gather there and folds to a
 * wedge instead; the point of the elbow flattens at the same time. Neither is a
 * fault in the pose — the curl is right — and neither can be authored out of the
 * bind pose, because at extension the arm is correct as it is.
 *
 * So the correction is driven by the joint. Each affected vertex carries a
 * bind-space offset that is scaled by how far the elbow is flexed: nothing at
 * all at extension, full at the top of the curl. Because the offset is applied
 * to the bind pose, the skinning that follows is the ordinary one — no custom
 * shader, no second surface, and the GLB path is untouched.
 *
 * ## What is deliberately not fixed
 *
 * At the top of the curl the arm is closed far enough that its own surfaces
 * touch. A triangle-by-triangle audit of the posed elbow found 128 intersecting
 * non-adjacent pairs at 126°, and only 40 of them are in the crease: the other
 * 84 are the upper arm meeting the forearm, roughly 100 mm above the joint
 * against 60–90 mm below it. That is the arm closing on itself. The character's
 * own mesh does the same thing on the same frame — 130 pairs, 108 of them the
 * same segment contact — so it is not something this view introduced, and no
 * amount of local subdivision would stop it: there is no elbow ring involved.
 *
 * It was accepted rather than chased. Every one of those crossings is inside the
 * fold, where none of the exercise cameras can see it, and the sweep behind the
 * amplitudes below showed that adding surface to the crease makes crossings more
 * numerous rather than fewer. Local refinement exists in `body/refine.ts` and is
 * switched off for exactly that reason.
 *
 * One warning for anyone measuring this later: the inverted-triangle count that
 * appears in the tests is a *fold severity* diagnostic, not a self-intersection
 * test. It fires on tight curvature that is not a crossing at all, and it moves
 * in the opposite direction to the real crossing count when this correction is
 * turned up. Do not accept or reject a change on it alone.
 */

/**
 * The correction's shape, in metres. Kept in one mutable place so it can be
 * swept against the inversion count rather than guessed at from renders.
 */
export const ELBOW_TUNING = {
  /** Where the correction ends, metres from the joint. */
  reach: 0.1,
  /** Full-flexion push on the inside of the elbow — the flesh roll. */
  inner: 0.016,
  /** Full-flexion push on the point of the elbow. */
  outer: 0.007,
  /**
   * How far the inner surface is spread along the arm. The crease is not only
   * shallow, it is crowded: the skin of the upper arm and the skin of the
   * forearm are driven into the same place. Pushing each side back towards its
   * own bone gives the fold room to be a roll instead of a pile.
   */
  spread: 0,
  /** Skin-weight band over which the correction fades in. */
  gateLow: 0.4,
  gateHigh: 0.8,
};
/** Elbow angles the drive runs between, radians: rest, and the top of a curl. */
const REST_ANGLE = 0.11;
const FULL_ANGLE = 2.2;

/** Half-width of the blend the elbow is re-weighted over, metres. */
const BLEND_BAND = 0.05;

/**
 * Widen and even out the skin blend across the elbow.
 *
 * This is the actual cause of the wedge. Measured on the character's own
 * weights, the humerus hands over to the forearm across roughly 40 mm on its
 * side of the joint and only 20 mm on the other: by 20 mm past the elbow the
 * surface is 96% forearm and rotating rigidly with it. A joint weighted like
 * that is a hinge between two tubes, and it folds like one — the two rigid
 * surfaces drive into each other and meet at a point, and no corrective placed
 * on top can round a fold that has nothing to fold with.
 *
 * So the pair's share of each vertex is redistributed on a smooth ramp along the
 * humerus, symmetric about the joint and reaching 50 mm either side. Weights
 * from any other bone are left exactly as they were and the total still sums to
 * one; at the edges of the band the ramp already agrees with the weights outside
 * it, so nothing steps.
 *
 * Anatomy mode only. The character's own mesh and the GLB export keep the
 * weights they were authored with.
 */
export function blendElbowWeights(geometry: BufferGeometry, rig: Skeleton = canonicalSkeleton): void {
  const position = geometry.getAttribute('position');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const evaluation = new PoseEvaluation(rig).apply(restPose());

  const joint = new Vector3();
  const axis = new Vector3();
  const point = new Vector3();
  const boneNumber = new Map<string, number>();
  rig.bones.forEach((bone, number) => boneNumber.set(bone.name, number));

  for (const side of SIDES) {
    const upperName = `upperarm_${side}` as BoneName;
    const lowerName = `forearm_${side}` as BoneName;
    const upperBone = boneNumber.get(upperName);
    const lowerBone = boneNumber.get(lowerName);
    if (upperBone === undefined || lowerBone === undefined) continue;

    evaluation.head(lowerName, joint);
    axis.set(0, 1, 0).applyQuaternion(evaluation.quaternion(upperName)).normalize();

    for (let vertex = 0; vertex < position.count; vertex += 1) {
      point.fromBufferAttribute(position, vertex).sub(joint);
      const along = point.dot(axis);
      if (Math.abs(along) > BLEND_BAND) continue;

      const slots = new Map<number, number>();
      for (let slot = 0; slot < 4; slot += 1) {
        const weight = skinWeight.getComponent(vertex, slot);
        if (weight > 0) {
          const bone = skinIndex.getComponent(vertex, slot);
          slots.set(bone, (slots.get(bone) ?? 0) + weight);
        }
      }
      const pair = (slots.get(upperBone) ?? 0) + (slots.get(lowerBone) ?? 0);
      // Not this elbow's vertex: the wrist and the shoulder both come within the
      // band's reach along the axis without belonging to it.
      if (pair < 0.5) continue;

      // +Y runs shoulder to elbow, so a positive `along` is past the joint and
      // belongs to the forearm.
      const share = smoothstep(-BLEND_BAND, BLEND_BAND, along);
      slots.set(upperBone, pair * (1 - share));
      slots.set(lowerBone, pair * share);

      const ranked = [...slots.entries()]
        .filter(([, weight]) => weight > 1e-6)
        .sort((one, two) => two[1] - one[1])
        .slice(0, 4);
      const total = ranked.reduce((carry, [, weight]) => carry + weight, 0) || 1;
      for (let slot = 0; slot < 4; slot += 1) {
        const entry = ranked[slot];
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
    }
  }
  skinIndex.needsUpdate = true;
  skinWeight.needsUpdate = true;
}

/** The furthest the correction may move any vertex, metres. */
export const ELBOW_SAFE_PUSH = 0.025;

export interface ElbowCorrective {
  /** Vertices the correction moves. */
  vertex: Int32Array;
  /** Their bind positions, before correction. */
  bind: Float32Array;
  /** The offset each takes at full flexion. */
  offset: Float32Array;
  /** Which elbow drives each vertex: 0 left, 1 right. */
  side: Uint8Array;
  /** Triangles touching those vertices, as corner offsets into the index. */
  triangle: Int32Array;
  /** Vertices whose normal those triangles decide. */
  touched: Int32Array;
}

const SIDES: readonly Side[] = ['l', 'r'];

/**
 * Work out, once, which vertices the elbow owns and which way each of them has
 * to move. The direction is the humerus's own forward axis in the bind pose:
 * forward for the vertices on the inside of the joint, back for the ones over
 * the point of it.
 */
export function buildElbowCorrective(
  geometry: BufferGeometry,
  rig: Skeleton = canonicalSkeleton,
): ElbowCorrective {
  const position = geometry.getAttribute('position');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const evaluation = new PoseEvaluation(rig).apply(restPose());

  const vertices: number[] = [];
  const binds: number[] = [];
  const offsets: number[] = [];
  const sides: number[] = [];

  const joint = new Vector3();
  const point = new Vector3();
  const away = new Vector3();
  const radial = new Vector3();
  const axis = new Vector3();
  const forward = new Vector3();

  for (let index = 0; index < SIDES.length; index += 1) {
    const side = SIDES[index];
    const upperName = `upperarm_${side}` as BoneName;
    const lowerName = `forearm_${side}` as BoneName;
    const pairBones = new Set<string>([upperName, lowerName]);
    const lowerOnly = new Set<string>([lowerName]);

    evaluation.head(lowerName, joint);
    axis.set(0, 1, 0).applyQuaternion(evaluation.quaternion(upperName)).normalize();
    forward.set(0, 0, 1).applyQuaternion(evaluation.quaternion(upperName)).normalize();

    for (let vertex = 0; vertex < position.count; vertex += 1) {
      point.fromBufferAttribute(position, vertex);
      away.subVectors(point, joint);
      if (away.length() > ELBOW_TUNING.reach) continue;

      const pair = boneInfluence(skinIndex, skinWeight, vertex, pairBones, rig);
      if (pair < 0.5) continue;
      const share = boneInfluence(skinIndex, skinWeight, vertex, lowerOnly, rig) / pair;

      // What linear blend skinning actually crushes is the middle of a blend:
      // a vertex driven half by each bone lands on the average of two very
      // different transforms, and the average falls inside the arm. A vertex
      // that belongs to one bone alone is carried rigidly and is fine. So the
      // correction is strongest exactly where the blend is most even, and dies
      // out at both ends of the band on its own.
      const centrality = 4 * share * (1 - share);
      if (centrality <= 0.01) continue;

      // Straight out from the bone, which is forward on the inside of the joint
      // and back over the point of it.
      radial.copy(away).addScaledVector(axis, -away.dot(axis));
      const spread = radial.length();
      if (spread < 1e-5) continue;
      radial.divideScalar(spread);
      const facing = radial.dot(forward);

      const inner = Math.max(0, facing) ** 1.5;
      const outer = Math.max(0, -facing) ** 1.5;
      const push = (ELBOW_TUNING.inner * inner + ELBOW_TUNING.outer * outer) * centrality * pair;
      const slide = ELBOW_TUNING.spread * inner * centrality * pair * Math.sign(away.dot(axis) || 1);
      if (Math.abs(push) < 1e-5 && Math.abs(slide) < 1e-5) continue;

      vertices.push(vertex);
      binds.push(point.x, point.y, point.z);
      offsets.push(
        radial.x * push + axis.x * slide,
        radial.y * push + axis.y * slide,
        radial.z * push + axis.z * slide,
      );
      sides.push(index);
    }
  }

  // Normals are rebuilt for every vertex a moved triangle touches, which means
  // every triangle those vertices belong to has to be in the list — including
  // ones with no moved corner of their own, or a vertex on the boundary would
  // have its normal averaged from half its neighbours.
  const moved = new Set(vertices);
  const meshIndex = geometry.getIndex();
  const triangles = new Set<number>();
  const touched = new Set<number>();
  if (meshIndex) {
    for (let corner = 0; corner < meshIndex.count; corner += 3) {
      const a = meshIndex.getX(corner);
      const b = meshIndex.getX(corner + 1);
      const c = meshIndex.getX(corner + 2);
      if (!moved.has(a) && !moved.has(b) && !moved.has(c)) continue;
      triangles.add(corner);
      touched.add(a).add(b).add(c);
    }
    for (let corner = 0; corner < meshIndex.count; corner += 3) {
      if (triangles.has(corner)) continue;
      const a = meshIndex.getX(corner);
      const b = meshIndex.getX(corner + 1);
      const c = meshIndex.getX(corner + 2);
      if (touched.has(a) || touched.has(b) || touched.has(c)) triangles.add(corner);
    }
  }

  return {
    vertex: Int32Array.from(vertices),
    bind: Float32Array.from(binds),
    offset: Float32Array.from(offsets),
    side: Uint8Array.from(sides),
    triangle: Int32Array.from(triangles),
    touched: Int32Array.from(touched),
  };
}

/**
 * How hard the correction pulls, 0..1, from the angle between the two bones.
 * Measured off the bones themselves rather than off a rotation channel, so it
 * cannot be knocked out of step by a change of Euler convention.
 */
export function elbowFlexion(evaluation: PoseEvaluation, side: Side): number {
  const upper = new Vector3(0, 1, 0).applyQuaternion(evaluation.quaternion(`upperarm_${side}`));
  const lower = new Vector3(0, 1, 0).applyQuaternion(evaluation.quaternion(`forearm_${side}`));
  const angle = upper.angleTo(lower);
  const t = Math.min(1, Math.max(0, (angle - REST_ANGLE) / (FULL_ANGLE - REST_ANGLE)));
  return t * t * (3 - 2 * t);
}

const faceNormal = new Vector3();
const edgeOne = new Vector3();
const edgeTwo = new Vector3();
const corner = [new Vector3(), new Vector3(), new Vector3()];

/**
 * Write the corrected bind pose for the current elbow angles. Only the vertices
 * the correction owns are touched, and only the normals their triangles decide
 * are rebuilt, so this is cheap enough to run every frame.
 */
export function applyElbowCorrective(
  geometry: BufferGeometry,
  corrective: ElbowCorrective,
  flexion: readonly [number, number],
): void {
  const position = geometry.getAttribute('position');
  const normal = geometry.getAttribute('normal');
  const index = geometry.getIndex();

  for (let slot = 0; slot < corrective.vertex.length; slot += 1) {
    const vertex = corrective.vertex[slot];
    const drive = flexion[corrective.side[slot]];
    position.setXYZ(
      vertex,
      corrective.bind[slot * 3] + corrective.offset[slot * 3] * drive,
      corrective.bind[slot * 3 + 1] + corrective.offset[slot * 3 + 1] * drive,
      corrective.bind[slot * 3 + 2] + corrective.offset[slot * 3 + 2] * drive,
    );
  }
  position.needsUpdate = true;
  if (!index) return;

  for (const vertex of corrective.touched) normal.setXYZ(vertex, 0, 0, 0);
  for (const start of corrective.triangle) {
    for (let slot = 0; slot < 3; slot += 1) {
      corner[slot].fromBufferAttribute(position, index.getX(start + slot));
    }
    faceNormal
      .crossVectors(
        edgeOne.subVectors(corner[1], corner[0]),
        edgeTwo.subVectors(corner[2], corner[0]),
      );
    for (let slot = 0; slot < 3; slot += 1) {
      const vertex = index.getX(start + slot);
      normal.setXYZ(
        vertex,
        normal.getX(vertex) + faceNormal.x,
        normal.getY(vertex) + faceNormal.y,
        normal.getZ(vertex) + faceNormal.z,
      );
    }
  }
  for (const vertex of corrective.touched) {
    faceNormal.set(normal.getX(vertex), normal.getY(vertex), normal.getZ(vertex));
    if (faceNormal.lengthSq() < 1e-16) continue;
    faceNormal.normalize();
    normal.setXYZ(vertex, faceNormal.x, faceNormal.y, faceNormal.z);
  }
  normal.needsUpdate = true;
}
