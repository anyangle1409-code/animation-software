import { Euler, InterpolateLinear, NumberKeyframeTrack, Quaternion } from 'three';
import type { KeyframeTrack, SkinnedMesh } from 'three';
import type { Skeleton } from '../rig/skeleton';
import type { Pose } from '../rig/types';
import { EULER_ORDER } from '../rig/types';
import { applyElbowCorrective, buildElbowCorrective, elbowFlexion } from '../body/elbow';
import type { ElbowCorrective } from '../body/elbow';
import { shoulderInfluences } from '../body/shoulder';
import type { ShoulderCorrective } from '../body/shoulder';
import { compressTrack } from '../export/tracks';
import type { CharacterVariant, DeformationContext, DeformationSampler, DeformationStack } from './types';

/**
 * The built-in character's own corrections.
 *
 * Every one of these is authored against the vertices of the MakeHuman-derived
 * surface in `src/body` — the armpit correctives are literally a list of that
 * mesh's vertex offsets. They belong to that character and travel with it. A
 * new, better-weighted mesh brings its own stack, or none.
 */

/**
 * On. The widened skin blend rounds the elbow crease but leaves the inside of
 * the joint passing through itself at high flexion, so the pose-space
 * correction carries that part.
 */
const ELBOW_CORRECTIVE = true;

export function builtinDeformation(
  mesh: SkinnedMesh,
  rig: Skeleton,
  variant: CharacterVariant,
): DeformationStack | null {
  const shoulders = mesh.geometry.userData.shoulders as ShoulderCorrective[] | undefined;
  const elbow: ElbowCorrective | null =
    variant === 'ecorche' && ELBOW_CORRECTIVE ? buildElbowCorrective(mesh.geometry, rig) : null;
  if (!elbow && (!shoulders || shoulders.length === 0)) return null;

  const flexion: [number, number] = [-1, -1];
  const scratch = { world: new Quaternion(), local: new Quaternion(), influences: [] as number[] };

  return {
    update({ evaluation, character }: DeformationContext) {
      if (elbow) {
        const left = elbowFlexion(evaluation, 'l');
        const right = elbowFlexion(evaluation, 'r');
        // Rewriting the bind pose uploads a buffer, so only when it moved.
        if (Math.abs(left - flexion[0]) > 0.002 || Math.abs(right - flexion[1]) > 0.002) {
          flexion[0] = left;
          flexion[1] = right;
          applyElbowCorrective(mesh.geometry, elbow, flexion);
        }
      }

      const influences = mesh.morphTargetInfluences;
      if (!shoulders || !influences) return;
      for (const corrective of shoulders) {
        const bone = character.boneByName.get(corrective.bone);
        const rigBone = rig.bones.find((each) => each.name === corrective.bone);
        if (!bone || !rigBone) continue;
        scratch.world.setFromRotationMatrix(bone.matrix);
        scratch.local.copy(rigBone.restLocalQuaternion).invert().multiply(scratch.world);
        shoulderInfluences(corrective, scratch.local, scratch.influences);
        corrective.targets.forEach((target, slot) => {
          influences[target] = scratch.influences[slot];
        });
      }
    },

    sampler(): DeformationSampler | null {
      if (!shoulders || shoulders.length === 0) return null;
      return shoulderSampler(shoulders, mesh.name);
    },
  };
}

/**
 * The shoulder correctives as animation tracks.
 *
 * The exported file has to deform the way the studio does, so the same
 * influences the viewport computes per frame are sampled from the baked poses
 * and written as morph-target weights.
 */
function shoulderSampler(shoulders: ShoulderCorrective[], meshName: string): DeformationSampler {
  const tracks = new Map<number, number[]>();
  const euler = new Euler(0, 0, 0, EULER_ORDER);
  const rotation = new Quaternion();
  const influences: number[] = [];

  return {
    sample(pose: Pose) {
      for (const corrective of shoulders) {
        const value = pose.rotations[corrective.bone];
        euler.set(value?.x ?? 0, value?.y ?? 0, value?.z ?? 0, EULER_ORDER);
        shoulderInfluences(corrective, rotation.setFromEuler(euler), influences);
        corrective.targets.forEach((target, slot) => {
          const track = tracks.get(target) ?? [];
          track.push(influences[slot]);
          tracks.set(target, track);
        });
      }
    },

    tracks(times: number[]): KeyframeTrack[] {
      const built: KeyframeTrack[] = [];
      const loopTimes = [times[0], times[times.length - 1]];
      for (const [target, values] of [...tracks].sort((one, two) => one[0] - two[0])) {
        const compressed = compressTrack(values, 1, [0]);
        if (!compressed) continue;
        built.push(
          new NumberKeyframeTrack(
            `${meshName}.morphTargetInfluences[${target}]`,
            compressed.constant ? loopTimes : times,
            compressed.values,
            InterpolateLinear,
          ),
        );
      }
      return built;
    },
  };
}
