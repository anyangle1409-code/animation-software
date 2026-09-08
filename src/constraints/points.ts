import { Vector3 } from 'three';
import type { PoseEvaluation } from '../rig/skeleton';
import type { PointRef } from './types';

/** Resolve a `PointRef` to a world position for the currently evaluated pose. */
export function resolvePoint(
  evaluation: PoseEvaluation,
  point: PointRef,
  target = new Vector3(),
): Vector3 {
  const bone = evaluation.skeleton.bone(point.bone);
  const along = point.along ?? 0;
  target.set(
    point.offset?.x ?? 0,
    (point.offset?.y ?? 0) + bone.length * along,
    point.offset?.z ?? 0,
  );
  return target.applyMatrix4(evaluation.matrix(point.bone));
}

export const pointLabel = (point: PointRef): string =>
  point.along === 1 ? `${point.bone} (end)` : point.bone;
