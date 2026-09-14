import {
  BufferAttribute,
  InterpolateLinear,
  NumberKeyframeTrack,
  Vector3,
} from 'three';
import type { Bone, KeyframeTrack, SkinnedMesh } from 'three';
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
  let affected = 0;

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    point.fromBufferAttribute(position, vertex);
    const away = point.clone().sub(joint);
    if (away.length() > reach) continue;
    let upperWeight = 0;
    let lowerWeight = 0;
    for (let slot = 0; slot < 4; slot += 1) {
      const bone = skinIndex.getComponent(vertex, slot);
      const weight = skinWeight.getComponent(vertex, slot);
      if (upperIndices.has(bone)) upperWeight += weight;
      if (lowerIndices.has(bone)) lowerWeight += weight;
    }
    const pair = upperWeight + lowerWeight;
    if (pair < 0.5) continue;
    const share = lowerWeight / pair;
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
    affected += 1;
  }
  if (!affected) return null;

  const morph = new BufferAttribute(delta, 3);
  morph.name = `homeGymPT_elbow_${side}`;
  mesh.geometry.morphTargetsRelative = true;
  const attributes = mesh.geometry.morphAttributes.position ?? [];
  mesh.geometry.morphAttributes.position = [...attributes, morph];
  mesh.updateMorphTargets();
  const influence = mesh.morphTargetDictionary?.[morph.name] ?? attributes.length;
  if (mesh.morphTargetInfluences) mesh.morphTargetInfluences[influence] = 0;
  return { mesh, side, influence, name: morph.name };
}

function matchingBones(mesh: SkinnedMesh, base: string, includeSplitHelpers = false): Set<number> {
  const result = new Set<number>();
  mesh.skeleton.bones.forEach((bone, index) => {
    if (bone.name === base || bone.name.startsWith(`${base}.`) || (includeSplitHelpers && bone.name.startsWith(base) && /^\d+$/.test(bone.name.slice(base.length)))) result.add(index);
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
