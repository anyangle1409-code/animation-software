import { HgVec3 } from '../core/linearMath';

export interface HgRay {
  origin: HgVec3;
  direction: HgVec3;
}

/**
 * Parameter s of the point pivot + axis*s closest to the ray.
 * Returns null when ray and axis are effectively parallel.
 */
export function closestHgAxisParameter(
  ray: HgRay,
  pivot: HgVec3,
  axis: HgVec3,
): number | null {
  const d = ray.direction.clone().normalize();
  const a = axis.clone().normalize();
  if (d.lengthSq() < 1e-12 || a.lengthSq() < 1e-12) return null;

  const w = ray.origin.clone().sub(pivot);
  const b = d.dot(a);
  const denominator = 1 - b * b;
  if (Math.abs(denominator) < 1e-10) return null;

  const d0 = d.dot(w);
  const e = a.dot(w);
  return (e - b * d0) / denominator;
}

export function hgAxisTranslationDelta(
  startRay: HgRay,
  currentRay: HgRay,
  pivot: HgVec3,
  axis: HgVec3,
): number | null {
  const start = closestHgAxisParameter(startRay, pivot, axis);
  const current = closestHgAxisParameter(currentRay, pivot, axis);
  return start === null || current === null ? null : current - start;
}

export function intersectHgRayPlane(
  ray: HgRay,
  point: HgVec3,
  normal: HgVec3,
): HgVec3 | null {
  const d = ray.direction.clone().normalize();
  const n = normal.clone().normalize();
  if (d.lengthSq() < 1e-12 || n.lengthSq() < 1e-12) return null;

  const denominator = n.dot(d);
  if (Math.abs(denominator) < 1e-10) return null;

  const t = n.dot(point.clone().sub(ray.origin)) / denominator;
  if (t < 0) return null;
  return ray.origin.clone().addScaledVector(d, t);
}

/**
 * Signed angular drag around axis, measured in the plane through pivot.
 * Positive follows the right-hand rule around axis.
 */
export function hgSignedRotationAngle(
  startRay: HgRay,
  currentRay: HgRay,
  pivot: HgVec3,
  axis: HgVec3,
): number | null {
  const unitAxis = axis.clone().normalize();
  if (unitAxis.lengthSq() < 1e-12) return null;

  const start = intersectHgRayPlane(startRay, pivot, unitAxis);
  const current = intersectHgRayPlane(currentRay, pivot, unitAxis);
  if (!start || !current) return null;

  const from = start.sub(pivot);
  const to = current.sub(pivot);
  if (from.lengthSq() < 1e-12 || to.lengthSq() < 1e-12) return null;
  from.normalize();
  to.normalize();

  const cross = from.clone().cross(to);
  return Math.atan2(unitAxis.dot(cross), from.dot(to));
}
