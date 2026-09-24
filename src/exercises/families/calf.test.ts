import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { EXERCISES } from '../library';
import { calfRaise } from '../definitions/calfRaise';
import { calfRoot } from './calf';

/**
 * The calf family: the body rising over the balls of the feet on soft, still
 * knees. These hold the pivot still, the knee still, and the heel doing all the
 * work — the three things `onBall` without an ankle promises.
 */
const rig = canonicalSkeleton;
const evaluation = new PoseEvaluation(rig);
const clip = generateClip(rig, calfRaise);
const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
const frames = Array.from({ length: 41 }, (_, step) => {
  const frame = resolveFrame(rig, evaluation, clip, (step / 40) * clip.duration, { anchors });
  evaluation.apply(frame.pose);
  return {
    ball: evaluation.tail('foot_l', new Vector3()),
    ankle: evaluation.head('foot_l', new Vector3()),
    toeTip: evaluation.tail('toe_l', new Vector3()),
    knee: (frame.pose.rotations.shin_l!.x * 180) / Math.PI,
    foot: (frame.pose.rotations.foot_l!.x * 180) / Math.PI,
    reached: frame.ikResults.every((result) => result.reached),
  };
});

describe('the calf family', () => {
  it('pivots on a ball of the foot that does not move, toes flat', () => {
    for (const frame of frames) {
      expect(frame.ball.distanceTo(frames[0].ball)).toBeLessThan(0.0005);
      expect(Math.abs(frame.toeTip.y - frames[0].toeTip.y)).toBeLessThan(0.0005);
      expect(frame.reached).toBe(true);
    }
  });

  it('holds the knee still while the heel lifts', () => {
    for (const frame of frames) expect(Math.abs(frame.knee - frames[0].knee)).toBeLessThan(0.1);
    // Measured: the ankle rises 7.0 cm, the foot turns to 32° of plantarflexion.
    const rise = Math.max(...frames.map((frame) => frame.ankle.y)) - frames[0].ankle.y;
    expect(rise).toBeCloseTo(calfRoot(35).y, 2);
    expect(Math.min(...frames.map((frame) => frame.foot))).toBeLessThan(-28);
    expect(frames[0].foot).toBeGreaterThan(-5);
  });

  it('has its two registered variants', () => {
    expect(EXERCISES.filter((exercise) => exercise.clipName.includes('calf_raise')).map((exercise) => exercise.id))
      .toEqual(['standing_calf_raise', 'dumbbell_calf_raise']);
  });
});

describe('calf raise contacts', () => {
  it('report each ankle, not the ball it pivots on, so a character stands where the rig does', () => {
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const clip = generateClip(canonicalSkeleton, calfRaise);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    for (const fraction of [0, 0.25, 0.5]) {
      const frame = resolveFrame(canonicalSkeleton, evaluation, clip, fraction * clip.duration, { anchors });
      evaluation.apply(frame.pose);
      for (const contact of frame.contacts) {
        const ankle = evaluation.head(contact.chain === 'leg_l' ? 'foot_l' : 'foot_r', new Vector3());
        expect(new Vector3(contact.target.x, contact.target.y, contact.target.z).distanceTo(ankle)).toBeLessThan(1e-12);
      }
    }
  });
});
