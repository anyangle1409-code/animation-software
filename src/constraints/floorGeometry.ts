import type { IKChainId } from '../ik/types';
import { canonicalSkeleton, type Skeleton } from '../rig/skeleton';
import type { Vec3 } from '../rig/types';

/**
 * Exercise definitions are authored in the current canonical floor coordinate
 * frame. Translate only the vertical contact coordinate when another compatible
 * skeleton has a different ankle/ball height.
 *
 * This leaves clip data unchanged: adaptation happens only at the solver
 * boundary. X/Z placement and every authored pole/orientation remain exact.
 */
export function floorTargetForSkeleton(
  skeleton: Skeleton,
  chain: IKChainId,
  target: Vec3,
  onBall: boolean,
): Vec3 {
  if (!chain.startsWith('leg')) return { ...target };
  const side = chain.endsWith('_r') ? 'r' : 'l';
  const activeFoot = skeleton.bone(`foot_${side}`);
  const referenceFoot = canonicalSkeleton.bone(`foot_${side}`);
  const activeHeight = onBall ? activeFoot.restTail.y : activeFoot.restHead.y;
  const referenceHeight = onBall ? referenceFoot.restTail.y : referenceFoot.restHead.y;
  return {
    ...target,
    y: target.y + activeHeight - referenceHeight,
  };
}
