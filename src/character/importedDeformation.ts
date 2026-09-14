import {
  BufferAttribute,
  InterpolateLinear,
  NumberKeyframeTrack,
  Vector3,
} from 'three';
import type { Bone, BufferGeometry, InterleavedBufferAttribute, KeyframeTrack, SkinnedMesh } from 'three';
import type { Skeleton } from '../rig/skeleton';
import { PoseEvaluation as RigPoseEvaluation } from '../rig/skeleton';
import type { BoneName, Side } from '../rig/boneNames';
import type { Pose } from '../rig/types';
import { elbowFlexion } from '../body/elbow';
import { compressTrack } from '../export/tracks';
import type { DeformationSampler, DeformationStack } from './types';

export interface ImportedElbowCorrectiveOptions {
  enabled?: boolean;
  reach?: number;
  inner?: number;
  outer?: number;
  includeSplitHelpers?: boolean;
  /**
   * Optional outer-elbow surface settling. `1` is the measured candidate value;
   * zero/undefined preserves the earlier radial corrective exactly.
   *
   * This is deliberately opt-in metadata rather than a generic importer rule:
   * it is useful only when the source mesh's elbow point is visibly faceted at
   * flexion. The shape is zero at extension and shares the elbow-flexion drive.
   */
  outerSmooth?: number;
}

interface Target {
  mesh: SkinnedMesh;
  side: Side;
  influence: number;
  name: string;
}

/** Build opt-in pose shapes for an imported mesh's own elbow topology. */
export function importedElbowDeformation(
  meshes: SkinnedMesh[],
  boneByName: Map<BoneName, Bone>,
  rig: Skeleton,
  options?: ImportedElbowCorrectiveOptions,
): DeformationStack | null {
  if (!options?.enabled) return null;
  const targets: Target[] = [];
  for (const mesh of meshes) {
    for (const side of ['l', 'r'] as const) {
      const target = appendTarget(mesh, boneByName, side, options);
      if (target) targets.push(target);
    }
  }
  if (!targets.length) return null;

  return {
    update({ evaluation }) {
      for (const target of targets) {
        if (target.mesh.morphTargetInfluences) {
          target.mesh.morphTargetInfluences[target.influence] = elbowFlexion(evaluation, target.side);
        }
      }
    },
    sampler: () => correctiveSampler(targets, rig),
  };
}

function appendTarget(
  mesh: SkinnedMesh,
  boneByName: Map<BoneName, Bone>,
  side: Side,
  options: ImportedElbowCorrectiveOptions,
): Target | null {
  const upper = boneByName.get(`upperarm_${side}` as BoneName);
  const lower = boneByName.get(`forearm_${side}` as BoneName);
  if (!upper || !lower) return null;
  const upperIndices = matchingBones(mesh, upper.name, options.includeSplitHelpers);
  const lowerIndices = matchingBones(mesh, lower.name, options.includeSplitHelpers);
  if (!upperIndices.size || !lowerIndices.size) return null;

  mesh.updateWorldMatrix(true, false);
  const joint = mesh.worldToLocal(lower.getWorldPosition(new Vector3()));
  const shoulder = mesh.worldToLocal(upper.getWorldPosition(new Vector3()));
  const axis = joint.clone().sub(shoulder).normalize();
  const forward = new Vector3(0, 0, 1);
  const position = mesh.geometry.getAttribute('position');
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  if (!position || !skinIndex || !skinWeight) return null;

  const reach = options.reach ?? 0.095;
  const innerAmount = options.inner ?? 0.012;
  const outerAmount = options.outer ?? 0.006;
  const delta = new Float32Array(position.count * 3);
  const point = new Vector3();
  const radial = new Vector3();

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    pointFrom(position, vertex, point);
    const away = point.clone().sub(joint);
    if (away.length() > reach) continue;
    const weights = elbowPairWeights(
      skinIndex,
      skinWeight,
      vertex,
      upperIndices,
      lowerIndices,
    );
    const pair = weights.upper + weights.lower;
    if (pair < 0.5) continue;
    const share = weights.lower / pair;
    const centrality = 4 * share * (1 - share);
    if (centrality < 0.02) continue;
    radial.copy(away).addScaledVector(axis, -away.dot(axis));
    if (radial.lengthSq() < 1e-10) continue;
    radial.normalize();
    const facing = radial.dot(forward);
    const inner = Math.max(0, facing) ** 1.5;
    const outer = Math.max(0, -facing) ** 1.5;
    const push = (innerAmount * inner + outerAmount * outer) * centrality * pair;
    if (push < 1e-5) continue;
    delta[vertex * 3] = radial.x * push;
    delta[vertex * 3 + 1] = radial.y * push;
    delta[vertex * 3 + 2] = radial.z * push;
  }

  const outerSmooth = Math.max(0, options.outerSmooth ?? 0);
  if (outerSmooth > 0) {
    addOuterSmoothing(
      mesh.geometry,
      delta,
      joint,
      axis,
      forward,
      upperIndices,
      lowerIndices,
      reach,
      outerSmooth,
    );
  }

  let affected = 0;
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    const start = vertex * 3;
    if (
      Math.abs(delta[start]) > 1e-7 ||
      Math.abs(delta[start + 1]) > 1e-7 ||
      Math.abs(delta[start + 2]) > 1e-7
    ) {
      affected += 1;
    }
  }
  if (!affected) return null;

  // Three.js stores one morph convention per geometry. Do not flip an imported
  // character from absolute to relative morphs (or vice versa) just to append
  // this corrective: doing so would reinterpret every pre-existing expression
  // or body shape. Encode the new target in the geometry's existing convention.
  const morph = mesh.geometry.morphTargetsRelative
    ? new BufferAttribute(delta, 3)
    : absoluteMorph(position, delta);
  morph.name = `homeGymPT_elbow_${side}`;
  const attributes = mesh.geometry.morphAttributes.position ?? [];
  mesh.geometry.morphAttributes.position = [...attributes, morph];
  mesh.updateMorphTargets();
  const influence = mesh.morphTargetDictionary?.[morph.name] ?? attributes.length;
  if (mesh.morphTargetInfluences) mesh.morphTargetInfluences[influence] = 0;
  return { mesh, side, influence, name: morph.name };
}

function elbowPairWeights(
  skinIndex: BufferAttribute | InterleavedBufferAttribute,
  skinWeight: BufferAttribute | InterleavedBufferAttribute,
  vertex: number,
  upperIndices: Set<number>,
  lowerIndices: Set<number>,
): { upper: number; lower: number } {
  let upper = 0;
  let lower = 0;
  for (let slot = 0; slot < 4; slot += 1) {
    const bone = skinIndex.getComponent(vertex, slot);
    const weight = skinWeight.getComponent(vertex, slot);
    if (upperIndices.has(bone)) upper += weight;
    if (lowerIndices.has(bone)) lower += weight;
  }
  return { upper, lower };
}

const clamp01 = (value: number): number => Math.min(1, Math.max(0, value));
const OUTER_SMOOTH_EXTRA_REACH = 0.025;
const OUTER_SMOOTH_RADIAL_FADE = 0.05;
const OUTER_SMOOTH_FACING_START = 0.25;
const OUTER_SMOOTH_FACING_RANGE = 0.6;
const OUTER_SMOOTH_MIN_WEIGHT = 0.03;
const OUTER_SMOOTH_MAX_OFFSET = 0.008;

/**
 * Add a small, topology-aware directional shape over the point of the elbow.
 *
 * The retained radial corrective restores volume to the bend. It cannot remove
 * a polygonal outer silhouette on a sparse imported mesh, and simply making it
 * larger was measured and rejected because that only added bulk. This pass does
 * something different: it measures the source surface's own one-ring curvature
 * in the bind pose and moves only the posterior/outer elbow along its bind-space
 * normal towards that local surface average. The movement is therefore
 * directional, follows the source topology, and remains zero until elbow
 * flexion drives the shared morph target.
 *
 * No topology or skin weight is changed. The maximum additional bind-space
 * offset is capped at 8 mm even when metadata asks for a stronger value.
 */
function addOuterSmoothing(
  geometry: BufferGeometry,
  delta: Float32Array,
  joint: Vector3,
  axis: Vector3,
  forward: Vector3,
  upperIndices: Set<number>,
  lowerIndices: Set<number>,
  reach: number,
  amount: number,
): void {
  const index = geometry.getIndex();
  const position = geometry.getAttribute('position');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  if (!index || !position || !skinIndex || !skinWeight) return;

  const neighbours = Array.from({ length: position.count }, () => new Set<number>());
  const normals = new Float32Array(position.count * 3);
  const a = new Vector3();
  const b = new Vector3();
  const c = new Vector3();
  const edgeOne = new Vector3();
  const edgeTwo = new Vector3();
  const face = new Vector3();

  for (let corner = 0; corner < index.count; corner += 3) {
    const ia = index.getX(corner);
    const ib = index.getX(corner + 1);
    const ic = index.getX(corner + 2);
    neighbours[ia].add(ib).add(ic);
    neighbours[ib].add(ia).add(ic);
    neighbours[ic].add(ia).add(ib);

    pointFrom(position, ia, a);
    pointFrom(position, ib, b);
    pointFrom(position, ic, c);
    face.crossVectors(edgeOne.subVectors(b, a), edgeTwo.subVectors(c, a));
    for (const vertex of [ia, ib, ic]) {
      normals[vertex * 3] += face.x;
      normals[vertex * 3 + 1] += face.y;
      normals[vertex * 3 + 2] += face.z;
    }
  }

  const smoothReach = reach + OUTER_SMOOTH_EXTRA_REACH;
  const away = new Vector3();
  const radial = new Vector3();
  const normal = new Vector3();
  const mean = new Vector3();
  const neighbourPoint = new Vector3();
  const smooth = new Vector3();

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    pointFrom(position, vertex, a);
    away.subVectors(a, joint);
    const distance = away.length();
    if (distance > smoothReach) continue;

    const pairWeights = elbowPairWeights(
      skinIndex,
      skinWeight,
      vertex,
      upperIndices,
      lowerIndices,
    );
    const pair = pairWeights.upper + pairWeights.lower;
    if (pair < 0.5) continue;

    radial.copy(away).addScaledVector(axis, -away.dot(axis));
    if (radial.lengthSq() < 1e-10) continue;
    radial.normalize();
    const facing = radial.dot(forward);
    if (facing > -OUTER_SMOOTH_FACING_START) continue;

    const radialFade = clamp01((smoothReach - distance) / OUTER_SMOOTH_RADIAL_FADE);
    const facingFade = clamp01(
      (-facing - OUTER_SMOOTH_FACING_START) / OUTER_SMOOTH_FACING_RANGE,
    );
    const strength = radialFade * facingFade * pair;
    if (strength <= OUTER_SMOOTH_MIN_WEIGHT) continue;

    const adjacent = neighbours[vertex];
    if (!adjacent.size) continue;
    mean.set(0, 0, 0);
    for (const neighbour of adjacent) {
      pointFrom(position, neighbour, neighbourPoint);
      mean.add(neighbourPoint);
    }
    mean.multiplyScalar(1 / adjacent.size);

    normal.set(
      normals[vertex * 3],
      normals[vertex * 3 + 1],
      normals[vertex * 3 + 2],
    );
    if (normal.lengthSq() < 1e-12) continue;
    normal.normalize();

    smooth.subVectors(mean, a);
    const signedDistance = smooth.dot(normal) * strength * amount;
    const bounded = Math.min(OUTER_SMOOTH_MAX_OFFSET, Math.abs(signedDistance));
    if (bounded < 1e-6) continue;
    const signed = Math.sign(signedDistance || 1) * bounded;
    const start = vertex * 3;
    delta[start] += normal.x * signed;
    delta[start + 1] += normal.y * signed;
    delta[start + 2] += normal.z * signed;
  }
}

function pointFrom(
  position: BufferAttribute | InterleavedBufferAttribute,
  vertex: number,
  target: Vector3,
): Vector3 {
  return target.set(position.getX(vertex), position.getY(vertex), position.getZ(vertex));
}

/** Build an absolute-position morph target without changing the source convention. */
function absoluteMorph(
  position: BufferAttribute | InterleavedBufferAttribute,
  delta: Float32Array,
): BufferAttribute {
  const values = new Float32Array(position.count * 3);
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    const start = vertex * 3;
    values[start] = position.getX(vertex) + delta[start];
    values[start + 1] = position.getY(vertex) + delta[start + 1];
    values[start + 2] = position.getZ(vertex) + delta[start + 2];
  }
  return new BufferAttribute(values, 3);
}

function matchingBones(mesh: SkinnedMesh, base: string, includeSplitHelpers = false): Set<number> {
  const result = new Set<number>();
  mesh.skeleton.bones.forEach((bone, index) => {
    if (
      bone.name === base ||
      bone.name.startsWith(`${base}.`) ||
      (includeSplitHelpers &&
        bone.name.startsWith(base) &&
        /^\d+$/.test(bone.name.slice(base.length)))
    ) {
      result.add(index);
    }
  });
  return result;
}

function correctiveSampler(targets: Target[], rig: Skeleton): DeformationSampler {
  const evaluation = new RigPoseEvaluation(rig);
  const values = targets.map(() => [] as number[]);
  return {
    sample(pose: Pose) {
      evaluation.apply(pose);
      targets.forEach((target, index) => values[index].push(elbowFlexion(evaluation, target.side)));
    },
    tracks(times: number[]): KeyframeTrack[] {
      const loopTimes = [times[0], times[times.length - 1]];
      return targets.flatMap((target, index) => {
        const compressed = compressTrack(values[index], 1, [0]);
        if (!compressed) return [];
        return [new NumberKeyframeTrack(
          `${target.mesh.name}.morphTargetInfluences[${target.name}]`,
          compressed.constant ? loopTimes : times,
          compressed.values,
          InterpolateLinear,
        )];
      });
    },
  };
}