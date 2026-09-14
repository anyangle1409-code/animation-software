import { Vector3 } from 'three';
import { resolveFrame } from '../animation/pipeline';
import type { StudioClip } from '../animation/clip';
import { IK_CHAINS } from '../ik/chains';
import type { IKChainId, IKResult } from '../ik/types';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Vec3 } from '../rig/types';
import type { LockMode } from './types';

export type ContactStatus = 'disabled' | 'unresolved' | 'reached' | 'limited' | 'overextended';

export interface ContactDiagnostic {
  id: string;
  chain: IKChainId;
  mode: LockMode;
  enabled: boolean;
  equipmentId?: string;
  socket?: string;
  target: Vec3 | null;
  actual: Vec3 | null;
  /** Final effector-to-target distance in metres. */
  error: number | null;
  reached: boolean | null;
  overExtended: boolean | null;
  status: ContactStatus;
}

const asVec3 = (point: Vector3): Vec3 => ({ x: point.x, y: point.y, z: point.z });

/**
 * Inspect the production contact solution at one playhead time.
 *
 * This deliberately calls the same `resolveFrame` pipeline as the viewport. It
 * does not run a second reach model or modify the clip: the target, final
 * effector position, solver `reached` flag and over-extension result are exactly
 * the values that produced the displayed pose.
 */
export function contactDiagnostics(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  clip: StudioClip,
  time: number,
  anchors?: Map<string, Vec3>,
): ContactDiagnostic[] {
  const frame = resolveFrame(skeleton, evaluation, clip, time, { anchors });
  evaluation.apply(frame.pose);

  const finalResults = new Map<IKChainId, IKResult>();
  for (const result of frame.ikResults) finalResults.set(result.chain, result);

  return clip.locks.map((lock) => {
    const common = {
      id: lock.id,
      chain: lock.chain,
      mode: lock.mode,
      enabled: lock.enabled,
      ...(lock.equipmentId ? { equipmentId: lock.equipmentId } : {}),
      ...(lock.socket ? { socket: lock.socket } : {}),
    };

    if (!lock.enabled) {
      return {
        ...common,
        target: null,
        actual: null,
        error: null,
        reached: null,
        overExtended: null,
        status: 'disabled' as const,
      };
    }

    const contact = [...frame.contacts]
      .reverse()
      .find((candidate) => candidate.chain === lock.chain && candidate.mode === lock.mode);
    if (!contact) {
      return {
        ...common,
        target: null,
        actual: null,
        error: null,
        reached: null,
        overExtended: null,
        status: 'unresolved' as const,
      };
    }

    const actualPoint = evaluation.head(IK_CHAINS[lock.chain].end, new Vector3());
    const targetPoint = new Vector3(contact.target.x, contact.target.y, contact.target.z);
    const result = finalResults.get(lock.chain);
    const error = actualPoint.distanceTo(targetPoint);
    const status: ContactStatus = result?.overExtended
      ? 'overextended'
      : result?.reached
        ? 'reached'
        : 'limited';

    return {
      ...common,
      target: { ...contact.target },
      actual: asVec3(actualPoint),
      error,
      reached: result?.reached ?? error < 1e-6,
      overExtended: result?.overExtended ?? false,
      status,
    };
  });
}
