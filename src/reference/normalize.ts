import type { Vec3 } from '../rig/types';
import type { Skeleton } from '../rig/skeleton';

export interface BodyNormalization {
  standingHeight: number;
  shoulderWidth: number;
  armLength: number;
  torsoLength: number;
}

/**
 * Stable body scales from the canonical rig's rest geometry.
 *
 * These are geometry measurements, not exercise-family values, so reference
 * trajectories can be stored independently of character size.
 */
export function bodyNormalization(rig: Skeleton): BodyNormalization {
  let minY = Number.POSITIVE_INFINITY;
  let maxY = Number.NEGATIVE_INFINITY;
  for (const bone of rig.bones) {
    minY = Math.min(minY, bone.restHead.y, bone.restTail.y);
    maxY = Math.max(maxY, bone.restHead.y, bone.restTail.y);
  }

  const leftShoulder = rig.bone('upperarm_l').restHead;
  const rightShoulder = rig.bone('upperarm_r').restHead;
  const pelvis = rig.bone('pelvis').restHead;
  const neck = rig.bone('neck').restHead;

  return {
    standingHeight: maxY - minY,
    shoulderWidth: leftShoulder.distanceTo(rightShoulder),
    armLength:
      rig.bone('upperarm_l').length +
      rig.bone('forearm_l').length +
      rig.bone('hand_l').length,
    torsoLength: pelvis.distanceTo(neck),
  };
}

export function normalizeDelta(value: number, scale: number): number {
  if (Math.abs(scale) < 1e-12) throw new Error('Cannot normalize by a zero scale');
  return value / scale;
}

export function normalizePoint(point: Vec3, origin: Vec3, scale: number): Vec3 {
  if (Math.abs(scale) < 1e-12) throw new Error('Cannot normalize by a zero scale');
  return {
    x: (point.x - origin.x) / scale,
    y: (point.y - origin.y) / scale,
    z: (point.z - origin.z) / scale,
  };
}
