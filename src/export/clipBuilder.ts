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
import type { KeyframeTrack } from 'three';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { EULER_ORDER } from '../rig/types';
import type { StudioClip } from '../animation/clip';
import type { Vec3 } from '../rig/types';
import { toRad } from '../core/math';
import { resolveFrame } from '../animation/pipeline';
import { sampleClip } from '../animation/clip';
import { lockAnchors } from '../constraints/locks';
import type { DeformationSampler } from '../character/types';
import { compressTrack } from './tracks';

export interface BakedClip {
  clip: AnimationClip;
  /** Per-equipment baked transforms, for items no bone can carry. */
  equipmentTracks: Map<string, { position: number[]; quaternion: number[]; scale?: number[] }>;
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
  options: {
    fps?: number;
    deformation?: DeformationSampler | null;
    /**
     * Off when the character has its own skeleton: the canonical bone tracks
     * then describe a rig the exported file does not contain, and the
     * character's own sampler carries the animation instead.
     */
    boneTracks?: boolean;
  } = {},
): BakedClip {
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
    // A cable changes length as it plays, so it alone carries a scale track.
    equipmentTracks.set(
      instance.id,
      instance.attachment.mode === 'cable' ? { position: [], quaternion: [], scale: [] } : { position: [], quaternion: [] },
    );
  }

  const localQuaternion = new Quaternion();
  const poseQuaternion = new Quaternion();
  const euler = new Euler(0, 0, 0, EULER_ORDER);
  // Whatever the character's own deformation stack does per frame beyond
  // posing bones — morph-target correctives, most of it — is sampled from the
  // same poses, so the exported file deforms the way the studio does.
  const deformation = options.deformation ?? null;

  for (let index = 0; index <= frameCount; index += 1) {
    // The final sample lands exactly on the loop point rather than near it.
    const time = index === frameCount ? studioClip.duration : (index / frameCount) * studioClip.duration;
    times.push(time);

    const frame = resolveFrame(rig, evaluation, studioClip, time, { anchors });

    deformation?.sample(frame.pose, { contacts: frame.contacts });

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
      if (track.scale) {
        const scale = transform.scale ?? { x: 1, y: 1, z: 1 };
        track.scale.push(scale.x, scale.y, scale.z);
      }
    }
  }

  const tracks: KeyframeTrack[] = [];
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
  const rootTrack = options.boneTracks === false ? null : compressTrack(rootPositions, 3, restPosition);
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

  if (deformation) tracks.push(...deformation.tracks(times));

  const clip = new AnimationClip(studioClip.name, studioClip.duration, tracks);
  // A stable id keeps repeated exports byte-identical, which makes the output
  // diffable and safe to commit alongside the app that consumes it. three.js
  // types the field as read-only, but it is a plain assignable property.
  (clip as { uuid: string }).uuid = `hgpt-clip-${studioClip.name}`;
  return { clip, equipmentTracks, times, fps };
}

/** Local transform of a hand-held item relative to the hand bone that carries it. */
export function handAttachmentMatrix(
  grip: { x: number; y: number; z: number },
  socket: { x: number; y: number; z: number },
  options: { gripRotation?: Vec3; socketRotation?: Vec3 } = {},
): Matrix4 {
  const gripRotation = options.gripRotation ?? { x: 0, y: 0, z: 0 };
  const socketRotation = options.socketRotation ?? { x: 0, y: 0, z: 0 };
  const gripMatrix = new Matrix4().compose(
    new Vector3(grip.x, grip.y, grip.z),
    new Quaternion().setFromEuler(
      new Euler(toRad(gripRotation.x), toRad(gripRotation.y), toRad(gripRotation.z), EULER_ORDER),
    ),
    new Vector3(1, 1, 1),
  );
  const socketMatrix = new Matrix4().compose(
    new Vector3(socket.x, socket.y, socket.z),
    new Quaternion().setFromEuler(
      new Euler(toRad(socketRotation.x), toRad(socketRotation.y), toRad(socketRotation.z), EULER_ORDER),
    ),
    new Vector3(1, 1, 1),
  );
  return gripMatrix.multiply(socketMatrix.invert());
}

export const zeroVector = new Vector3();
