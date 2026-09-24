import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { EXERCISES } from '../library';
import { overheadExtension } from '../definitions/overheadExtension';

/**
 * The elbow-extension family: the upper arm points at the ceiling and holds
 * still, and the forearm folds down behind the head and back up. These hold
 * both halves, and the one new thing the family does — load passing behind
 * the head — to a clear gap between the two dumbbells.
 */
const rig = canonicalSkeleton;
const evaluation = new PoseEvaluation(rig);
const clip = generateClip(rig, overheadExtension);
const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);

function at(time: number) {
  const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
  evaluation.apply(frame.pose);
  const shoulder = evaluation.head('upperarm_l', new Vector3());
  const elbow = evaluation.head('forearm_l', new Vector3());
  return {
    upperArm: (elbow.clone().sub(shoulder).normalize().angleTo(new Vector3(0, 1, 0)) * 180) / Math.PI,
    elbow,
    hand: evaluation.head('hand_l', new Vector3()),
    head: evaluation.head('head', new Vector3()),
    gap: frame.equipment.get('dumbbell_l')!.position.distanceTo(frame.equipment.get('dumbbell_r')!.position),
  };
}

describe('the extension family', () => {
  it('holds the upper arm still, pointing at the ceiling', () => {
    const first = at(0);
    // 11.2° off vertical, measured: elbows up and a little forward.
    expect(first.upperArm).toBeLessThan(15);
    for (let step = 0; step <= 40; step += 1) {
      const frame = at((step / 40) * clip.duration);
      expect(Math.abs(frame.upperArm - first.upperArm), `step ${step}`).toBeLessThan(1);
      expect(frame.elbow.distanceTo(first.elbow), `elbow at step ${step}`).toBeLessThan(1e-6);
    }
  });

  it('folds the forearm down behind the head, and keeps the dumbbells apart', () => {
    const stretch = at(overheadExtension.tempo.eccentric + overheadExtension.tempo.pauseStretched / 2);
    expect(stretch.hand.z).toBeLessThan(stretch.head.z - 0.2);
    expect(stretch.hand.y).toBeLessThan(stretch.elbow.y);
    for (let step = 0; step <= 40; step += 1) {
      // Two 48 mm plates side by side need 96 mm; 380 mm measured at the closest.
      expect(at((step / 40) * clip.duration).gap, `step ${step}`).toBeGreaterThan(0.25);
    }
  });

  it('has exactly one registered variant', () => {
    expect(EXERCISES.filter((exercise) => exercise.clipName.includes('triceps')).map((exercise) => exercise.id))
      .toEqual(['dumbbell_overhead_triceps_extension']);
  });
});
