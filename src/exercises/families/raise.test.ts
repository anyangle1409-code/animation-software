import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { EXERCISES } from '../library';
import { lateralRaise } from '../definitions/lateralRaise';
import { frontRaise } from '../definitions/frontRaise';
import type { ExerciseDefinition } from '../types';

/**
 * The shoulder-raise family: a soft-elbowed arm swung up to shoulder height and
 * no higher, out to the side or straight ahead, with only the shoulder moving.
 */
const rig = canonicalSkeleton;

function frames(exercise: ExerciseDefinition) {
  const evaluation = new PoseEvaluation(rig);
  const clip = generateClip(rig, exercise);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  return Array.from({ length: 41 }, (_, step) => {
    const frame = resolveFrame(rig, evaluation, clip, (step / 40) * clip.duration, { anchors });
    evaluation.apply(frame.pose);
    const shoulder = evaluation.head('upperarm_l', new Vector3());
    const elbow = evaluation.head('forearm_l', new Vector3());
    const hand = evaluation.head('hand_l', new Vector3());
    const arm = elbow.clone().sub(shoulder).normalize();
    return {
      shoulder,
      hand,
      fromHanging: (arm.angleTo(new Vector3(0, -1, 0)) * 180) / Math.PI,
      elbowBend: (frame.pose.rotations.forearm_l!.x * 180) / Math.PI,
      dumbbells: [frame.equipment.get('dumbbell_l')!.position.y, frame.equipment.get('dumbbell_r')!.position.y],
    };
  });
}

describe('the shoulder-raise family', () => {
  it.each([
    ['lateral', lateralRaise],
    ['front', frontRaise],
  ] as const)('%s raise: up to shoulder height and no higher, on a fixed elbow', (_name, exercise) => {
    const all = frames(exercise);
    const top = Math.max(...all.map((frame) => frame.fromHanging));
    // Measured: 84° from hanging at the top for both.
    expect(top).toBeGreaterThan(80);
    expect(top).toBeLessThan(90);
    for (const frame of all) {
      expect(frame.hand.y - frame.shoulder.y).toBeLessThan(0.04);
      expect(Math.abs(frame.elbowBend - all[0].elbowBend)).toBeLessThan(0.5);
      expect(Math.abs(frame.dumbbells[0] - frame.dumbbells[1])).toBeLessThan(0.005);
    }
  });

  it('raises the lateral raise out to the side, a little forward of the body', () => {
    const top = frames(lateralRaise).reduce((a, b) => (b.fromHanging > a.fromHanging ? b : a));
    // Out past the shoulder by most of an arm, and forward of it by 10 cm.
    expect(top.shoulder.x - top.hand.x).toBeGreaterThan(0.45);
    expect(top.hand.z - top.shoulder.z).toBeGreaterThan(0.05);
    expect(top.hand.z - top.shoulder.z).toBeLessThan(0.2);
  });

  it('raises the front raise straight ahead', () => {
    const all = frames(frontRaise);
    for (const frame of all) expect(Math.abs(frame.hand.x - all[0].hand.x)).toBeLessThan(0.01);
    const top = all.reduce((a, b) => (b.fromHanging > a.fromHanging ? b : a));
    expect(top.hand.z - top.shoulder.z).toBeGreaterThan(0.5);
  });

  it('has its two registered variants', () => {
    expect(EXERCISES.filter((exercise) => exercise.clipName.endsWith('_raise')).map((exercise) => exercise.id))
      .toEqual(['dumbbell_lateral_raise', 'dumbbell_front_raise']);
  });
});
