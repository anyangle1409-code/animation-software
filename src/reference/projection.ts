import { PerspectiveCamera, Vector3 } from 'three';
import type { Vec3 } from '../rig/types';

export interface ProjectionCamera {
  position: Vec3;
  target: Vec3;
  fov: number;
  aspect: number;
  near?: number;
  far?: number;
}

export interface ProjectedPoint {
  /** Normalized image coordinate: 0 left, 1 right. */
  x: number;
  /** Normalized image coordinate: 0 top, 1 bottom. */
  y: number;
  /** Three.js normalized device depth, -1 near to +1 far. */
  depth: number;
  inFrame: boolean;
}

export interface ProjectedEnvelope {
  x?: { min?: number; max?: number };
  y?: { min?: number; max?: number };
}

export interface ProjectedEnvelopeResult {
  passed: boolean;
  point: ProjectedPoint;
  /** Maximum normalized-image excess outside the allowed envelope. */
  excess: number;
  detail: string;
}

const excess1d = (value: number, range?: { min?: number; max?: number }): number => {
  if (!range) return 0;
  if (range.min !== undefined && value < range.min) return range.min - value;
  if (range.max !== undefined && value > range.max) return value - range.max;
  return 0;
};

/** Project one world point through a deterministic review camera. */
export function projectWorldPoint(point: Vec3, setup: ProjectionCamera): ProjectedPoint {
  const camera = new PerspectiveCamera(
    setup.fov,
    setup.aspect,
    setup.near ?? 0.05,
    setup.far ?? 100,
  );
  camera.position.set(setup.position.x, setup.position.y, setup.position.z);
  camera.lookAt(setup.target.x, setup.target.y, setup.target.z);
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);

  const ndc = new Vector3(point.x, point.y, point.z).project(camera);
  const x = (ndc.x + 1) / 2;
  const y = (1 - ndc.y) / 2;
  return {
    x,
    y,
    depth: ndc.z,
    inFrame: ndc.x >= -1 && ndc.x <= 1 && ndc.y >= -1 && ndc.y <= 1 && ndc.z >= -1 && ndc.z <= 1,
  };
}

export function evaluateProjectedEnvelope(
  point: Vec3,
  camera: ProjectionCamera,
  envelope: ProjectedEnvelope,
): ProjectedEnvelopeResult {
  const projected = projectWorldPoint(point, camera);
  const xExcess = excess1d(projected.x, envelope.x);
  const yExcess = excess1d(projected.y, envelope.y);
  const excess = Math.max(xExcess, yExcess);
  const passed = projected.inFrame && excess <= 1e-9;

  return {
    passed,
    point: projected,
    excess,
    detail: !projected.inFrame
      ? `Projected point is outside the review frame at (${projected.x.toFixed(4)}, ${projected.y.toFixed(4)}).`
      : passed
        ? `Projected point (${projected.x.toFixed(4)}, ${projected.y.toFixed(4)}) is inside the allowed corridor.`
        : `Projected point (${projected.x.toFixed(4)}, ${projected.y.toFixed(4)}) is outside the allowed corridor by ${excess.toFixed(4)} normalized image units.`,
  };
}

/**
 * Euclidean screen-space distance in normalized image units. This is useful for
 * comparing candidate and reference landmarks while staying independent of
 * pixel resolution.
 */
export function projectedDistance(a: ProjectedPoint, b: ProjectedPoint): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
}
