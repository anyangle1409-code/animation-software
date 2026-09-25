import { Vector3 } from 'three';
import type { StudioClip } from '../animation/clip';
import { sampleClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import type { BoneName } from '../rig/boneNames';
import type { Vec3 } from '../rig/types';
import { PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';

export type LandmarkFrame = Partial<Record<BoneName, Vec3>>;

/** Resolve canonical bone-head landmarks at one exact clip time. */
export function sampleLandmarks(
  rig: Skeleton,
  clip: StudioClip,
  time: number,
  bones: BoneName[],
): LandmarkFrame {
  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(
    new PoseEvaluation(rig),
    sampleClip(clip, 0).pose,
    clip.locks,
  );
  const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
  evaluation.apply(frame.pose);

  const out: LandmarkFrame = {};
  for (const bone of bones) {
    const point = evaluation.head(bone, new Vector3());
    out[bone] = { x: point.x, y: point.y, z: point.z };
  }
  return out;
}

/**
 * Sample a normalized trajectory for a single landmark. Times are returned as
 * cycle positions so reference/candidate paths can be compared across tempo.
 */
export function sampleLandmarkTrajectory(
  rig: Skeleton,
  clip: StudioClip,
  bone: BoneName,
  samples = 41,
): { t: number; point: Vec3 }[] {
  const count = Math.max(2, samples);
  return Array.from({ length: count }, (_, index) => {
    const t = index / (count - 1);
    const time = Math.min(clip.duration, t * clip.duration);
    const frame = sampleLandmarks(rig, clip, time, [bone]);
    return { t, point: frame[bone]! };
  });
}
