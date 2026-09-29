import { HgVec3 } from '../core/linearMath';
import type { PoseEvaluation } from '../rig/skeleton';
import type { Vec3 } from '../rig/types';
import type { PointRef } from './types';

const pointScratch = new HgVec3();

/** Resolve a `PointRef` to a world position for the currently evaluated pose. */
export function resolvePoint<T extends Vec3 = HgVec3>(
  evaluation: PoseEvaluation,
  point: PointRef,
  target?: T,
): T {
  const bone = evaluation.skeleton.bone(point.bone);
  const along = point.along ?? 0;
  pointScratch.set(
    point.offset?.x ?? 0,
    (point.offset?.y ?? 0) + bone.length * along,
    point.offset?.z ?? 0,
  );
  evaluation.firstPartyEvaluation.localToWorld(point.bone, pointScratch, pointScratch);
  const output = (target ?? new HgVec3()) as T;
  output.x = pointScratch.x;
  output.y = pointScratch.y;
  output.z = pointScratch.z;
  return output;
}

export const pointLabel = (point: PointRef): string =>
  point.along === 1 ? `${point.bone} (end)` : point.bone;
