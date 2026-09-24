import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { EXERCISES } from '../library';
import { bentOverRow } from '../definitions/bentOverRow';
import { romanianDeadlift } from '../definitions/romanianDeadlift';
import { FOOT_L } from './row';

/**
 * The horizontal-pull family: a hinge held still while the arms row.
 *
 * The row starts bent over, so its feet cannot be anchored from its opening
 * frame the way every other standing exercise's are; they are pinned to where
 * the hinge's stand. These tests hold that pin to the hinge, and hold the pull
 * to what makes it a row rather than a curl or a shrug: the trunk does not
 * move, the forearm hangs under the weight, and the elbow finishes level with
 * the back.
 */
const rig = canonicalSkeleton;
const deg = (radians: number | undefined) => ((radians ?? 0) * 180) / Math.PI;

function playback(samples = 60) {
  const evaluation = new PoseEvaluation(rig);
  const clip = generateClip(rig, bentOverRow);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  return Array.from({ length: samples + 1 }, (_, step) => {
    const time = (step / samples) * clip.duration;
    const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
    evaluation.apply(frame.pose);
    const forearm = evaluation.tail('forearm_l', new Vector3()).sub(evaluation.head('forearm_l', new Vector3()));
    return {
      time,
      pose: frame.pose,
      chest: evaluation.tail('spine_03', new Vector3()),
      pelvis: evaluation.head('pelvis', new Vector3()),
      shoulder: evaluation.head('upperarm_l', new Vector3()),
      elbow: evaluation.head('forearm_l', new Vector3()),
      forearmFromVertical: (Math.acos(-forearm.normalize().y) * 180) / Math.PI,
    };
  });
}

/** The middle of the squeeze: the concentric phase has ended. */
const atPeak = (frames: ReturnType<typeof playback>) => {
  const peak = bentOverRow.tempo.concentric + bentOverRow.tempo.pauseContracted / 2;
  return frames.reduce((best, frame) => (Math.abs(frame.time - peak) < Math.abs(best.time - peak) ? frame : best));
};

describe('the row family', () => {
  it('stands exactly where the hinge stands', () => {
    // The pin is a copy of the hinge's standing feet; if the stance or the rig
    // moves, this is what notices.
    const evaluation = new PoseEvaluation(rig);
    const clip = generateClip(rig, romanianDeadlift);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    const vector = (value: { x: number; y: number; z: number }) => new Vector3(value.x, value.y, value.z);
    expect(vector(anchors.get('foot_l')!).distanceTo(vector(FOOT_L.position))).toBeLessThan(1e-4);
    for (const axis of ['direction', 'forward'] as const) {
      const hinge = vector(anchors.get(`foot_l#${axis}`)!);
      expect((hinge.angleTo(vector(FOOT_L.aim[axis])) * 180) / Math.PI, axis).toBeLessThan(0.02);
    }
    const lock = bentOverRow.locks.find((entry) => entry.id === 'foot_r')!;
    expect(lock.position!.x).toBeCloseTo(-FOOT_L.position.x, 12);
  });

  it('holds the hinge still while the arms work', () => {
    const frames = playback();
    const first = frames[0];
    for (const frame of frames) {
      expect(frame.chest.distanceTo(first.chest), `chest at ${frame.time.toFixed(2)}s`).toBeLessThan(1e-6);
      expect(frame.pelvis.distanceTo(first.pelvis), `pelvis at ${frame.time.toFixed(2)}s`).toBeLessThan(1e-6);
    }
    expect(first.pelvis.y).toBeCloseTo(0.9, 6);
    expect(first.pelvis.z).toBeCloseTo(-0.15, 6);
  });

  it('authors hip and knee angles that agree with the held hinge', () => {
    const solved = playback(4)[0].pose.rotations;
    const asked = (bone: string) =>
      bentOverRow.jointTargets.find((target) => target.bone === bone && target.axis === 'x')!.start;
    expect(Math.abs(deg(solved.thigh_l?.x) - asked('thigh_l'))).toBeLessThan(1.5);
    expect(Math.abs(deg(solved.shin_l?.x) - asked('shin_l'))).toBeLessThan(1.5);
  });

  it('finishes with the forearm under the weight and the elbow level with the back', () => {
    const peak = atPeak(playback(200));
    // 3.9° measured. A curl tips it forward; this fails at 12°.
    expect(peak.forearmFromVertical).toBeLessThan(8);
    // The elbow reaches the shoulder's height, give or take a few centimetres,
    // and sits behind it: pulled past the ribs, not just lifted.
    expect(Math.abs(peak.elbow.y - peak.shoulder.y)).toBeLessThan(0.06);
    expect(peak.elbow.z).toBeLessThan(peak.shoulder.z - 0.2);
    // And it starts from a full hang, forearm near vertical under the shoulder.
    const start = playback(4)[0];
    expect(start.forearmFromVertical).toBeLessThan(10);
  });

  it('has exactly one registered variant', () => {
    const rows = EXERCISES.filter((exercise) => exercise.category === 'upper_pull' && exercise.startPose.root?.rotation);
    expect(rows.map((exercise) => exercise.id)).toEqual(['dumbbell_bent_over_row']);
  });
});
