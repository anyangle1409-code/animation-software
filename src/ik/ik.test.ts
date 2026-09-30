import { describe, expect, it } from 'vitest';
import { HgVec3 } from '../core/linearMath';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { clonePose, poseFromDegrees, restPose } from '../rig/pose';
import { toDeg } from '../core/math';
import { IK_CHAINS } from './chains';
import { aimBone, solveTwoBone } from './twoBone';
import { goalFromPose, solveGoals } from './solve';

const skeleton = canonicalSkeleton;
const evaluation = new PoseEvaluation(skeleton);

function solveArm(target: HgVec3, pole: HgVec3) {
  const pose = clonePose(restPose());
  const result = solveTwoBone(skeleton, evaluation, pose, IK_CHAINS.arm_l, target, pole);
  evaluation.apply(pose);
  return { pose, result };
}

describe('two-bone IK', () => {
  it('preserves the shoulder hinge-twist solution for a reachable arm target', () => {
    const { pose, result } = solveArm(
      new HgVec3(-0.3, 1.15, 0.32),
      new HgVec3(-0.5, 1.1, -0.5),
    );
    expect(pose.rotations.upperarm_l?.y).toBeCloseTo(-0.3544732204228822, 10);
    expect(pose.rotations.upperarm_l?.x).toBeCloseTo(0.3755704592731539, 10);
    expect(pose.rotations.upperarm_l?.z).toBeCloseTo(-0.4391033302324271, 10);
    expect(pose.rotations.forearm_l?.x).toBeCloseTo(1.1634409553483458, 10);
    expect(result.error).toBeCloseTo(0, 10);
  });

  it('places the hand on a reachable target', () => {
    const target = new HgVec3(-0.3, 1.15, 0.32);
    const { result } = solveArm(target, new HgVec3(-0.5, 1.1, -0.5));
    expect(result.reached).toBe(true);
    expect(result.error).toBeLessThan(2e-3);
  });

  it('keeps the elbow on the pole side of the limb', () => {
    const target = new HgVec3(-0.25, 1.2, 0.3);
    const front = solveArm(target, new HgVec3(-0.4, 1.2, 1.5));
    const back = solveArm(target, new HgVec3(-0.4, 1.2, -1.5));
    const frontElbow = new PoseEvaluation(skeleton).apply(front.pose).head('forearm_l', new HgVec3());
    const backElbow = new PoseEvaluation(skeleton).apply(back.pose).head('forearm_l', new HgVec3());
    expect(frontElbow.z).toBeGreaterThan(backElbow.z + 0.1);
  });

  it('keeps the elbow a hinge — no abduction is introduced', () => {
    // All within the 0.56 m reach of the shoulder at (-0.17, 1.44, 0).
    const targets = [
      new HgVec3(-0.35, 1.3, 0.25),
      new HgVec3(-0.25, 1.15, 0.3),
      new HgVec3(-0.3, 1.05, 0.15),
      new HgVec3(-0.22, 1.3, 0.35),
    ];
    for (const target of targets) {
      const { pose, result } = solveArm(target, new HgVec3(-0.6, 1.0, -0.4));
      expect(result.error).toBeLessThan(5e-3);
      expect(pose.rotations.forearm_l?.z ?? 0).toBeCloseTo(0, 6);
      const flexion = toDeg(pose.rotations.forearm_l?.x ?? 0);
      expect(flexion).toBeGreaterThanOrEqual(-5);
      expect(flexion).toBeLessThanOrEqual(150);
    }
  });

  it('reaches towards an unreachable target without breaking the arm', () => {
    const target = new HgVec3(-0.9, 1.44, 1.2);
    const { pose, result } = solveArm(target, new HgVec3(-0.9, 1.2, 0));
    expect(result.overExtended).toBe(true);
    expect(result.reached).toBe(false);
    const elbow = toDeg(pose.rotations.forearm_l?.x ?? 0);
    expect(elbow).toBeLessThan(8);
    const evaluated = new PoseEvaluation(skeleton).apply(pose);
    const shoulder = evaluated.head('upperarm_l', new HgVec3());
    const hand = evaluated.head('hand_l', new HgVec3());
    const toHand = hand.clone().sub(shoulder).normalize();
    const toTarget = target.clone().sub(shoulder).normalize();
    expect(toHand.dot(toTarget)).toBeGreaterThan(0.98);
  });

  it('respects joint limits instead of producing an impossible pose', () => {
    // Directly behind the shoulder: the shoulder cannot extend that far.
    const target = new HgVec3(-0.2, 1.44, -0.55);
    const { pose } = solveArm(target, new HgVec3(-0.6, 1.2, -0.2));
    const shoulderFlexion = toDeg(pose.rotations.upperarm_l?.x ?? 0);
    expect(shoulderFlexion).toBeGreaterThanOrEqual(-60.0001);
  });
});

describe('leg IK', () => {
  it('preserves the knee and hip solve for a planted-foot target', () => {
    const pose = clonePose(restPose());
    const result = solveTwoBone(
      skeleton,
      evaluation,
      pose,
      IK_CHAINS.leg_l,
      new HgVec3(-0.082, 0.42, 0.18),
      new HgVec3(-0.1, 0.5, 1.4),
    );
    expect(pose.rotations.thigh_l?.x).toBeCloseTo(1.2312145419964278, 10);
    expect(pose.rotations.thigh_l?.y).toBeCloseTo(0.002250570318530927, 10);
    expect(pose.rotations.thigh_l?.z).toBeCloseTo(-0.012030845204473612, 10);
    expect(pose.rotations.shin_l?.x).toBeCloseTo(-1.7716914028904953, 10);
    expect(result.error).toBeLessThan(1e-10);
  });

  it('plants the foot at a target with the knee tracking the pole', () => {
    const pose = clonePose(restPose());
    const target = new HgVec3(-0.082, 0.42, 0.18);
    const result = solveTwoBone(
      skeleton,
      evaluation,
      pose,
      IK_CHAINS.leg_l,
      target,
      new HgVec3(-0.1, 0.5, 1.4),
    );
    expect(result.reached).toBe(true);
    const evaluated = new PoseEvaluation(skeleton).apply(pose);
    const knee = evaluated.head('shin_l', new HgVec3());
    expect(knee.z).toBeGreaterThan(0.05);
    expect(toDeg(pose.rotations.shin_l?.x ?? 0)).toBeLessThan(0);
    expect(pose.rotations.shin_l?.z ?? 0).toBeCloseTo(0, 6);
  });
});

describe('goals', () => {
  it('preserves toe-out ball-foot IK rotation and contact', () => {
    const pose = clonePose(restPose());
    const ball = new PoseEvaluation(skeleton).apply(pose).tail('foot_r', new HgVec3());
    const result = solveGoals(skeleton, evaluation, pose, [{
      chain: 'leg_r',
      enabled: true,
      target: { x: 0, y: 0, z: 0 },
      pole: { x: 0.1, y: 0.5, z: 1.4 },
      ball: { anchor: { x: ball.x, y: ball.y, z: ball.z }, ankle: 25, toeOut: 15 },
    }])[0];
    expect(pose.rotations.foot_r?.x).toBeCloseTo(0.038754237982525176, 10);
    expect(pose.rotations.foot_r?.y).toBeCloseTo(0.06388643191545393, 10);
    expect(pose.rotations.foot_r?.z).toBeCloseTo(-0.04725902227983521, 10);
    expect(pose.rotations.shin_r?.x).toBeCloseTo(-0.06020742463045516, 10);
    expect(pose.rotations.toe_r?.x).toBeCloseTo(4.1091744118482174e-8, 10);
    expect(result.error).toBeCloseTo(0.001520585717277288, 10);
  });

  it('retains the authored arm bend when deriving an enabled IK goal', () => {
    const pose = poseFromDegrees({ upperarm_l: { x: 35, z: -20 }, forearm_l: { x: 80 } });
    const goal = goalFromPose(new PoseEvaluation(skeleton), pose, 'arm_l');
    expect(goal.target.x).toBeCloseTo(-0.3217177483973105, 10);
    expect(goal.target.y).toBeCloseTo(1.3211857870697203, 10);
    expect(goal.target.z).toBeCloseTo(0.3607739602603038, 10);
    expect(goal.pole.x).toBeCloseTo(-0.414850578920537, 10);
    expect(goal.pole.y).toBeCloseTo(0.7817780607343835, 10);
    expect(goal.pole.z).toBeCloseTo(0.03653366537729348, 10);
  });

  it('preserves an end-aim roll with a forward reference', () => {
    const pose = clonePose(restPose());
    const aimEvaluation = new PoseEvaluation(skeleton);
    aimBone(
      skeleton,
      aimEvaluation,
      pose,
      'hand_l',
      new HgVec3(0.2, 0.8, 0.4),
      new HgVec3(0.2, 0, 1),
    );
    expect(pose.rotations.hand_l?.x).toBeCloseTo(0.3490658503988659, 10);
    expect(pose.rotations.hand_l?.y).toBeCloseTo(0, 10);
    expect(pose.rotations.hand_l?.z).toBeCloseTo(0.2199879773954594, 10);
  });

  it('creates a goal that leaves the current pose untouched', () => {
    const pose = poseFromDegrees({
      upperarm_l: { x: 35, z: -20 },
      forearm_l: { x: 80 },
      thigh_l: { x: 20 },
      shin_l: { x: -40 },
    });
    for (const chain of ['arm_l', 'leg_l'] as const) {
      const before = new PoseEvaluation(skeleton).apply(pose);
      const beforeEnd = before.head(IK_CHAINS[chain].end, new HgVec3());
      const goal = goalFromPose(evaluation, pose, chain);
      const solved = clonePose(pose);
      solveGoals(skeleton, evaluation, solved, [goal]);
      const after = new PoseEvaluation(skeleton).apply(solved);
      expect(after.head(IK_CHAINS[chain].end, new HgVec3()).distanceTo(beforeEnd)).toBeLessThan(2e-3);
    }
  });
});
