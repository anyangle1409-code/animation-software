import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { clonePose, poseFromDegrees, restPose } from '../rig/pose';
import { toDeg } from '../core/math';
import { IK_CHAINS } from './chains';
import { solveTwoBone } from './twoBone';
import { goalFromPose, solveGoals } from './solve';

const skeleton = canonicalSkeleton;
const evaluation = new PoseEvaluation(skeleton);

function solveArm(target: Vector3, pole: Vector3) {
  const pose = clonePose(restPose());
  const result = solveTwoBone(skeleton, evaluation, pose, IK_CHAINS.arm_l, target, pole);
  evaluation.apply(pose);
  return { pose, result };
}

describe('two-bone IK', () => {
  it('places the hand on a reachable target', () => {
    const target = new Vector3(-0.3, 1.15, 0.32);
    const { result } = solveArm(target, new Vector3(-0.5, 1.1, -0.5));
    expect(result.reached).toBe(true);
    expect(result.error).toBeLessThan(2e-3);
  });

  it('keeps the elbow on the pole side of the limb', () => {
    const target = new Vector3(-0.25, 1.2, 0.3);
    const front = solveArm(target, new Vector3(-0.4, 1.2, 1.5));
    const back = solveArm(target, new Vector3(-0.4, 1.2, -1.5));
    const frontElbow = new PoseEvaluation(skeleton).apply(front.pose).head('forearm_l', new Vector3());
    const backElbow = new PoseEvaluation(skeleton).apply(back.pose).head('forearm_l', new Vector3());
    expect(frontElbow.z).toBeGreaterThan(backElbow.z + 0.1);
  });

  it('keeps the elbow a hinge — no abduction is introduced', () => {
    // All within the 0.56 m reach of the shoulder at (-0.17, 1.44, 0).
    const targets = [
      new Vector3(-0.35, 1.3, 0.25),
      new Vector3(-0.25, 1.15, 0.3),
      new Vector3(-0.3, 1.05, 0.15),
      new Vector3(-0.22, 1.3, 0.35),
    ];
    for (const target of targets) {
      const { pose, result } = solveArm(target, new Vector3(-0.6, 1.0, -0.4));
      expect(result.error).toBeLessThan(5e-3);
      expect(pose.rotations.forearm_l?.z ?? 0).toBeCloseTo(0, 6);
      const flexion = toDeg(pose.rotations.forearm_l?.x ?? 0);
      expect(flexion).toBeGreaterThanOrEqual(-5);
      expect(flexion).toBeLessThanOrEqual(150);
    }
  });

  it('reaches towards an unreachable target without breaking the arm', () => {
    const target = new Vector3(-0.9, 1.44, 1.2);
    const { pose, result } = solveArm(target, new Vector3(-0.9, 1.2, 0));
    expect(result.overExtended).toBe(true);
    expect(result.reached).toBe(false);
    const elbow = toDeg(pose.rotations.forearm_l?.x ?? 0);
    expect(elbow).toBeLessThan(8);
    const evaluated = new PoseEvaluation(skeleton).apply(pose);
    const shoulder = evaluated.head('upperarm_l', new Vector3());
    const hand = evaluated.head('hand_l', new Vector3());
    const toHand = hand.clone().sub(shoulder).normalize();
    const toTarget = target.clone().sub(shoulder).normalize();
    expect(toHand.dot(toTarget)).toBeGreaterThan(0.98);
  });

  it('respects joint limits instead of producing an impossible pose', () => {
    // Directly behind the shoulder: the shoulder cannot extend that far.
    const target = new Vector3(-0.2, 1.44, -0.55);
    const { pose } = solveArm(target, new Vector3(-0.6, 1.2, -0.2));
    const shoulderFlexion = toDeg(pose.rotations.upperarm_l?.x ?? 0);
    expect(shoulderFlexion).toBeGreaterThanOrEqual(-60.0001);
  });
});

describe('leg IK', () => {
  it('plants the foot at a target with the knee tracking the pole', () => {
    const pose = clonePose(restPose());
    const target = new Vector3(-0.082, 0.42, 0.18);
    const result = solveTwoBone(
      skeleton,
      evaluation,
      pose,
      IK_CHAINS.leg_l,
      target,
      new Vector3(-0.1, 0.5, 1.4),
    );
    expect(result.reached).toBe(true);
    const evaluated = new PoseEvaluation(skeleton).apply(pose);
    const knee = evaluated.head('shin_l', new Vector3());
    expect(knee.z).toBeGreaterThan(0.05);
    expect(toDeg(pose.rotations.shin_l?.x ?? 0)).toBeLessThan(0);
    expect(pose.rotations.shin_l?.z ?? 0).toBeCloseTo(0, 6);
  });
});

describe('goals', () => {
  it('creates a goal that leaves the current pose untouched', () => {
    const pose = poseFromDegrees({
      upperarm_l: { x: 35, z: -20 },
      forearm_l: { x: 80 },
      thigh_l: { x: 20 },
      shin_l: { x: -40 },
    });
    for (const chain of ['arm_l', 'leg_l'] as const) {
      const before = new PoseEvaluation(skeleton).apply(pose);
      const beforeEnd = before.head(IK_CHAINS[chain].end, new Vector3());
      const goal = goalFromPose(evaluation, pose, chain);
      const solved = clonePose(pose);
      solveGoals(skeleton, evaluation, solved, [goal]);
      const after = new PoseEvaluation(skeleton).apply(solved);
      expect(after.head(IK_CHAINS[chain].end, new Vector3()).distanceTo(beforeEnd)).toBeLessThan(2e-3);
    }
  });
});
