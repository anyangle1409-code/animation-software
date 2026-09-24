import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { EXERCISES } from '../library';
import { splitSquat } from '../definitions/splitSquat';

/**
 * The lunge family: a split stance, the two legs doing different things. The
 * front foot is flat; the back foot stands on its ball with the heel rising and
 * falling as the back knee drops, which is the new contact this family needed.
 */
const rig = canonicalSkeleton;
const deg = (radians: number | undefined) => ((radians ?? 0) * 180) / Math.PI;
const evaluation = new PoseEvaluation(rig);
const clip = generateClip(rig, splitSquat);
const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);

function at(time: number) {
  const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
  evaluation.apply(frame.pose);
  const heel = evaluation.head('foot_r', new Vector3());
  const ball = evaluation.tail('foot_r', new Vector3());
  return {
    pose: frame.pose,
    ball,
    toeTip: evaluation.tail('toe_r', new Vector3()),
    toe: new Vector3(0, 1, 0).applyQuaternion(evaluation.quaternion('toe_r')),
    /** How far the back foot is pitched up off the floor, degrees. */
    heel: (Math.asin((heel.y - ball.y) / heel.distanceTo(ball)) * 180) / Math.PI,
    backKnee: evaluation.head('shin_r', new Vector3()),
    frontKnee: evaluation.head('shin_l', new Vector3()),
    frontAnkle: evaluation.head('foot_l', new Vector3()),
  };
}
const bottom = splitSquat.tempo.eccentric + splitSquat.tempo.pauseStretched / 2;

describe('the lunge family', () => {
  it('pivots the back foot on its ball: the ball and toes stay put while the heel rises', () => {
    const first = at(0);
    const heels: number[] = [];
    for (let step = 0; step <= 40; step += 1) {
      const frame = at((step / 40) * clip.duration);
      expect(frame.ball.distanceTo(first.ball), `ball at step ${step}`).toBeLessThan(0.001);
      expect(Math.abs(frame.toeTip.y - first.toeTip.y), `toe tip at step ${step}`).toBeLessThan(0.001);
      expect((frame.toe.angleTo(first.toe) * 180) / Math.PI, `toes at step ${step}`).toBeLessThan(0.25);
      // The ankle holds its 25°.
      expect(Math.abs(deg(frame.pose.rotations.foot_r?.x) - 25), `ankle at step ${step}`).toBeLessThan(0.5);
      heels.push(frame.heel);
    }
    // And the heel does move: that is what the ball contact is for.
    expect(Math.max(...heels) - Math.min(...heels)).toBeGreaterThan(15);
  });

  it('reaches depth with the front knee over the front foot', () => {
    const frame = at(bottom);
    expect(frame.backKnee.y).toBeLessThan(0.12);
    expect(Math.abs(frame.frontKnee.x - frame.frontAnkle.x)).toBeLessThan(0.02);
    expect(frame.frontKnee.z - frame.frontAnkle.z).toBeLessThan(0.05);
  });

  it('authors leg angles that agree with what the solver produces', () => {
    for (const [time, key] of [[0, 'start'], [bottom, 'peak']] as const) {
      const rotations = at(time).pose.rotations;
      for (const target of splitSquat.jointTargets) {
        const solved = deg(rotations[target.bone]?.[target.axis]);
        expect(Math.abs(solved - target[key]), `${target.bone} ${key}: solved ${solved.toFixed(1)}`).toBeLessThan(1.5);
      }
    }
  });

  it('has exactly one registered variant', () => {
    // A foot held on its ball at a fixed ankle is a lunge's back foot; the calf
    // raise's feet are on their balls too, but hold the knee instead.
    expect(EXERCISES.filter((exercise) => exercise.locks.some((lock) => lock.onBall?.ankle !== undefined)).map((exercise) => exercise.id))
      .toEqual(['split_squat']);
  });
});
