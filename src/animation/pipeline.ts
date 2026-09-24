import { Vector3 } from 'three';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import { IK_CHAINS } from '../ik/chains';
import type { Pose } from '../rig/types';
import type { IKGoal, IKResult } from '../ik/types';
import { solveGoals } from '../ik/solve';
import { resolveLocks } from '../constraints/locks';
import type { Vec3 } from '../rig/types';
import type { EffectorLock, ResolvedContact } from '../constraints/types';
import { resolveEquipment, socketResolver } from '../equipment/attach';
import type { EquipmentTransform } from '../equipment/attach';
import type { EquipmentInstance } from '../equipment/types';
import { sampleClip } from './clip';
import type { StudioClip } from './clip';
import type { KeyframeIK } from './clip';
import type { IKChainId } from '../ik/types';

export interface ResolvedFrame {
  time: number;
  pose: Pose;
  equipment: Map<string, EquipmentTransform>;
  ikResults: IKResult[];
  /** Final lock targets, for preserved characters with different proportions. */
  contacts: ResolvedContact[];
  phaseId?: string;
}

/**
 * Turn a clip time into a finished frame.
 *
 * The order matters and is the heart of the system:
 *
 *   1. blend the keyframed forward-kinematic pose
 *   2. solve the keyframed IK targets
 *   3. place equipment from the resulting hands
 *   4. solve the locks, which may pull hands onto that equipment
 *   5. place equipment again, now from the locked hands
 *
 * Steps 4 and 5 run twice, which is what makes a two-handed bar settle: the bar
 * straightens between the grips, the grips are re-solved onto the straightened
 * bar, and the pair converges instead of drifting.
 */
export function resolveFrame(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  clip: StudioClip,
  time: number,
  options: {
    locks?: EffectorLock[];
    equipment?: EquipmentInstance[];
    /** Contact positions from the clip's opening pose; see `lockAnchors`. */
    anchors?: Map<string, Vec3>;
  } = {},
): ResolvedFrame {
  const sample = sampleClip(clip, time);
  const locks = options.locks ?? clip.locks;
  const equipment = options.equipment ?? clip.equipment;

  const pose = sample.pose;
  const ikResults: IKResult[] = [];

  const keyframeGoals = goalsFromKeyframe(sample.ik);
  if (keyframeGoals.length > 0) {
    ikResults.push(...solveGoals(skeleton, evaluation, pose, keyframeGoals));
  }
  evaluation.apply(pose);

  let transforms = resolveEquipment(evaluation, equipment);
  const activeLocks = locks.filter((lock) => lock.enabled);
  let finalLockGoals: IKGoal[] = [];

  if (activeLocks.length > 0) {
    const passes = activeLocks.some((lock) => lock.mode === 'equipment') ? 2 : 1;
    for (let pass = 0; pass < passes; pass += 1) {
      const resolver = socketResolver(equipment, transforms);
      const lockGoals = resolveLocks(evaluation, pose, activeLocks, resolver, options.anchors);
      finalLockGoals = lockGoals;
      const results = solveGoals(skeleton, evaluation, pose, lockGoals);
      if (pass === passes - 1) ikResults.push(...results);
      evaluation.apply(pose);
      transforms = resolveEquipment(evaluation, equipment);
    }
  }

  const contacts = finalLockGoals.map((goal) => ({
    chain: goal.chain,
    mode: activeLocks.find((lock) => lock.chain === goal.chain)?.mode ?? 'world',
    // A contact names where the limb's end joint goes. A foot on its ball is
    // anchored at the ball, which is where its lock's target points; its ankle
    // is wherever the heel's rise put it. Reporting the ball instead put a
    // character's ankle 14 cm forward, on the ball, in every exercise that
    // stands on one — the calf raises both feet, the split squat its back foot.
    target: goal.ball ? ankleOf(evaluation, goal.chain) : { ...goal.target },
    ...(goal.endAim ? { aim: goal.endAim } : {}),
  }));
  return { time, pose, equipment: transforms, ikResults, contacts, phaseId: sample.phaseId };
}

function ankleOf(evaluation: PoseEvaluation, chain: IKChainId): Vec3 {
  const ankle = evaluation.head(IK_CHAINS[chain].end, new Vector3());
  return { x: ankle.x, y: ankle.y, z: ankle.z };
}

function goalsFromKeyframe(ik: Partial<Record<IKChainId, KeyframeIK>>): IKGoal[] {
  const goals: IKGoal[] = [];
  for (const [chain, value] of Object.entries(ik)) {
    if (!value?.enabled) continue;
    goals.push({
      chain: chain as IKChainId,
      enabled: true,
      target: value.target,
      pole: value.pole,
      ...(value.aim ? { endAim: value.aim } : {}),
    });
  }
  return goals;
}
