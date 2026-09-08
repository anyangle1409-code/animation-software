import {
  AnimationClip,
  Euler,
  InterpolateLinear,
  Matrix4,
  Quaternion,
  QuaternionKeyframeTrack,
  Vector3,
  VectorKeyframeTrack,
} from 'three';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { EULER_ORDER } from '../rig/types';
import type { StudioClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import { sampleClip } from '../animation/clip';
import { lockAnchors } from '../constraints/locks';

export interface BakedClip {
  clip: AnimationClip;
  /** Per-equipment baked transforms, for items no bone can carry. */
  equipmentTracks: Map<string, { position: number[]; quaternion: number[] }>;
  times: number[];
  fps: number;
}

/**
 * Bake a studio clip into a three.js `AnimationClip`.
 *
 * The whole frame pipeline runs at every sample — IK, locks and equipment — so
 * what is exported is what the studio showed, not the raw keyframes before the
 * constraints were applied.
 *
 * The last sample repeats the first exactly, so the exported clip loops without
 * a seam.
 */
export function bakeClip(
  studioClip: StudioClip,
  rig: Skeleton = canonicalSkeleton,
  options: { fps?: number } = {},
): BakedClip {
  const fps = options.fps ?? studioClip.fps;
  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(evaluation, sampleClip(studioClip, 0).pose, studioClip.locks);

  const frameCount = Math.max(2, Math.round(studioClip.duration * fps));
  const times: number[] = [];
  const quaternions = new Map<BoneName, number[]>();
  const rootPositions: number[] = [];
  const equipmentTracks = new Map<string, { position: number[]; quaternion: number[] }>();

  for (const bone of rig.bones) quaternions.set(bone.name, []);
  for (const instance of studioClip.equipment) {
    equipmentTracks.set(instance.id, { position: [], quaternion: [] });
  }

  const localQuaternion = new Quaternion();
  const poseQuaternion = new Quaternion();
  const euler = new Euler(0, 0, 0, EULER_ORDER);

  for (let index = 0; index <= frameCount; index += 1) {
    // The final sample lands exactly on the loop point rather than near it.
    const time = index === frameCount ? studioClip.duration : (index / frameCount) * studioClip.duration;
    times.push(time);

    const frame = resolveFrame(rig, evaluation, studioClip, time, { anchors });

    for (const bone of rig.bones) {
      const rotation = frame.pose.rotations[bone.name];
      euler.set(rotation?.x ?? 0, rotation?.y ?? 0, rotation?.z ?? 0, EULER_ORDER);
      poseQuaternion.setFromEuler(euler);
      localQuaternion.copy(bone.restLocalQuaternion).multiply(poseQuaternion);

      if (bone.parent === null) {
        // The root carries the rig's world placement as well as its rotation.
        euler.set(
          frame.pose.rootRotation.x,
          frame.pose.rootRotation.y,
          frame.pose.rootRotation.z,
          EULER_ORDER,
        );
        localQuaternion.premultiply(poseQuaternion.setFromEuler(euler));
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
    }
  }

  const tracks: (QuaternionKeyframeTrack | VectorKeyframeTrack)[] = [];
  const loopTimes = [times[0], times[times.length - 1]];

  for (const bone of rig.bones) {
    const values = quaternions.get(bone.name)!;
    const rest = [
      bone.restLocalQuaternion.x,
      bone.restLocalQuaternion.y,
      bone.restLocalQuaternion.z,
      bone.restLocalQuaternion.w,
    ];
    const compressed = compressTrack(values, 4, rest);
    if (!compressed) continue;
    tracks.push(
      new QuaternionKeyframeTrack(
        `${bone.name}.quaternion`,
        compressed.constant ? loopTimes : times,
        compressed.values,
      ),
    );
  }

  const rootBone = rig.bones[0];
  const restPosition = [rootBone.offset.x, rootBone.offset.y, rootBone.offset.z];
  const rootTrack = compressTrack(rootPositions, 3, restPosition);
  if (rootTrack) {
    tracks.push(
      new VectorKeyframeTrack(
        `${rootBone.name}.position`,
        rootTrack.constant ? loopTimes : times,
        rootTrack.values,
        InterpolateLinear,
      ),
    );
  }

  const clip = new AnimationClip(studioClip.name, studioClip.duration, tracks);
  // A stable id keeps repeated exports byte-identical, which makes the output
  // diffable and safe to commit alongside the app that consumes it. three.js
  // types the field as read-only, but it is a plain assignable property.
  (clip as { uuid: string }).uuid = `hgpt-clip-${studioClip.name}`;
  return { clip, equipmentTracks, times, fps };
}

interface CompressedTrack {
  values: number[];
  constant: boolean;
}

/**
 * Shrink a sampled track.
 *
 * A track that never changes is reduced to two keys — but only dropped
 * altogether when its constant value is the bone's rest value. Dropping a
 * constant track that differs from rest would silently reset the bone: a
 * planted foot, a closed grip or a set stance would all snap back on export.
 */
function compressTrack(
  values: number[],
  stride: number,
  restValue: number[],
): CompressedTrack | null {
  if (values.length < stride) return null;
  if (!isStatic(values, stride)) return { values, constant: false };

  const first = values.slice(0, stride);
  const atRest = first.every((value, index) => Math.abs(value - restValue[index]) < 1e-6);
  if (atRest) return null;
  return { values: [...first, ...first], constant: true };
}

/** True when every sample of a track is the same, so the track can be dropped. */
function isStatic(values: number[], stride: number): boolean {
  if (values.length <= stride) return true;
  for (let index = stride; index < values.length; index += 1) {
    if (Math.abs(values[index] - values[index % stride]) > 1e-6) return false;
  }
  return true;
}

/** Local transform of a hand-held item relative to the hand bone that carries it. */
export function handAttachmentMatrix(
  grip: { x: number; y: number; z: number },
  socket: { x: number; y: number; z: number },
): Matrix4 {
  return new Matrix4()
    .makeTranslation(grip.x, grip.y, grip.z)
    .multiply(new Matrix4().makeTranslation(-socket.x, -socket.y, -socket.z));
}

export const zeroVector = new Vector3();
