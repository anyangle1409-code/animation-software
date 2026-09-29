import type { BoneName } from '../rig/boneNames';
import { HgQuat } from '../core/linearMath';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import type { StudioClip } from '../animation/clip';
import type { DeformationSampler, DeformationTrackData } from '../character/types';
import { resolveFrame } from '../animation/pipeline';
import { sampleClip } from '../animation/clip';
import { lockAnchors } from '../constraints/locks';
import { compressTrack } from './tracks';

export interface BakedBoneTrackData {
  bone: BoneName;
  property: 'quaternion' | 'position';
  times: number[];
  values: number[];
}

const asFloat32Numbers = (values: readonly number[]): number[] =>
  Array.from(new Float32Array(values));

export interface BakedClipData {
  name: string;
  duration: number;
  tracks: BakedBoneTrackData[];
  deformationTracks: DeformationTrackData[];
  equipmentTracks: Map<string, { position: number[]; quaternion: number[]; scale?: number[] }>;
  times: number[];
  fps: number;
}

/**
 * Project-owned baked animation data for formats that do not need Three scene
 * objects. The sampling/constraints path is identical to the compatibility
 * exporter, but quaternion composition is done with Home Gym PT math.
 */
export function bakeClipData(
  studioClip: StudioClip,
  rig: Skeleton = canonicalSkeleton,
  options: { fps?: number; boneTracks?: boolean; deformation?: DeformationSampler | null } = {},
): BakedClipData {
  const fps = options.fps ?? studioClip.fps;
  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(evaluation, sampleClip(studioClip, 0).pose, studioClip.locks);

  const frameCount = Math.max(2, Math.round(studioClip.duration * fps));
  const times: number[] = [];
  const quaternions = new Map<BoneName, number[]>();
  const rootPositions: number[] = [];
  const equipmentTracks = new Map<string, { position: number[]; quaternion: number[]; scale?: number[] }>();

  for (const bone of rig.bones) quaternions.set(bone.name, []);
  for (const instance of studioClip.equipment) {
    equipmentTracks.set(
      instance.id,
      instance.attachment.mode === 'cable'
        ? { position: [], quaternion: [], scale: [] }
        : { position: [], quaternion: [] },
    );
  }

  const localQuaternion = new HgQuat();
  const poseQuaternion = new HgQuat();
  const deformation = options.deformation ?? null;

  for (let index = 0; index <= frameCount; index += 1) {
    const time = index === frameCount
      ? studioClip.duration
      : (index / frameCount) * studioClip.duration;
    times.push(time);

    const frame = resolveFrame(rig, evaluation, studioClip, time, { anchors });

    deformation?.sample(frame.pose, { contacts: frame.contacts });

    for (const bone of rig.bones) {
      const rotation = frame.pose.rotations[bone.name];
      poseQuaternion.setFromEulerXZY(
        rotation?.x ?? 0,
        rotation?.y ?? 0,
        rotation?.z ?? 0,
      );
      localQuaternion
        .set(
          bone.restLocalQuaternion.x,
          bone.restLocalQuaternion.y,
          bone.restLocalQuaternion.z,
          bone.restLocalQuaternion.w,
        )
        .multiply(poseQuaternion);

      if (bone.parent === null) {
        poseQuaternion.setFromEulerXZY(
          frame.pose.rootRotation.x,
          frame.pose.rootRotation.y,
          frame.pose.rootRotation.z,
        );
        localQuaternion.premultiply(poseQuaternion);
        rootPositions.push(
          frame.pose.rootPosition.x,
          frame.pose.rootPosition.y,
          frame.pose.rootPosition.z,
        );
      }

      quaternions
        .get(bone.name)!
        .push(localQuaternion.x, localQuaternion.y, localQuaternion.z, localQuaternion.w);
    }

    for (const [id, track] of equipmentTracks) {
      const transform = frame.equipment.get(id);
      if (!transform) continue;
      track.position.push(transform.position.x, transform.position.y, transform.position.z);
      track.quaternion.push(
        transform.quaternion.x,
        transform.quaternion.y,
        transform.quaternion.z,
        transform.quaternion.w,
      );
      if (track.scale) {
        const scale = transform.scale ?? { x: 1, y: 1, z: 1 };
        track.scale.push(scale.x, scale.y, scale.z);
      }
    }
  }

  const tracks: BakedBoneTrackData[] = [];
  const loopTimes = [times[0], times[times.length - 1]];

  for (const bone of options.boneTracks === false ? [] : rig.bones) {
    const values = quaternions.get(bone.name)!;
    const rest = [
      bone.restLocalQuaternion.x,
      bone.restLocalQuaternion.y,
      bone.restLocalQuaternion.z,
      bone.restLocalQuaternion.w,
    ];
    const compressed = compressTrack(values, 4, rest);
    if (!compressed) continue;
    tracks.push({
      bone: bone.name,
      property: 'quaternion',
      // Match glTF/Three keyframe storage exactly: animation channels are
      // FLOAT (32-bit), so pin both time and value arrays to Float32 semantics.
      times: asFloat32Numbers(compressed.constant ? loopTimes : times),
      values: asFloat32Numbers(compressed.values),
    });
  }

  if (options.boneTracks !== false) {
    const rootBone = rig.bones[0];
    const restPosition = [rootBone.offset.x, rootBone.offset.y, rootBone.offset.z];
    const rootTrack = compressTrack(rootPositions, 3, restPosition);
    if (rootTrack) {
      tracks.push({
        bone: rootBone.name,
        property: 'position',
        times: asFloat32Numbers(rootTrack.constant ? loopTimes : times),
        values: asFloat32Numbers(rootTrack.values),
      });
    }
  }

  const deformationTracks = (deformation?.tracks(times) ?? []).map((track) => ({
    ...track,
    times: asFloat32Numbers(track.times),
    values: asFloat32Numbers(track.values),
  }));

  return {
    name: studioClip.name,
    duration: studioClip.duration,
    tracks,
    deformationTracks,
    equipmentTracks,
    times,
    fps,
  };
}
