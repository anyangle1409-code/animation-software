import { HgVec3 } from '../core/linearMath';
import type { Side } from './boneNames';
import type { PoseEvaluation } from './skeleton';

/** Elbow angles the normalized drive runs between, radians: rest and deep flexion. */
const REST_ANGLE = 0.11;
const FULL_ANGLE = 2.2;

/**
 * Renderer/mesh-independent elbow flexion drive, 0..1.
 *
 * Measured from the evaluated upper-arm and forearm directions rather than from
 * an Euler channel, so imported/future deformation stacks can share one
 * biomechanical drive without depending on any particular character surface.
 */
export function elbowFlexion(evaluation: PoseEvaluation, side: Side): number {
  const upper = new HgVec3(0, 1, 0).applyQuaternion(
    evaluation.firstPartyEvaluation.quaternion(`upperarm_${side}`),
  );
  const lower = new HgVec3(0, 1, 0).applyQuaternion(
    evaluation.firstPartyEvaluation.quaternion(`forearm_${side}`),
  );
  const angle = upper.angleTo(lower);
  const t = Math.min(1, Math.max(0, (angle - REST_ANGLE) / (FULL_ANGLE - REST_ANGLE)));
  return t * t * (3 - 2 * t);
}
