import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { EXERCISES } from '../library';
import { dumbbellBenchPress } from '../definitions/dumbbellBenchPress';
import { dumbbellFly } from '../definitions/dumbbellFly';
import type { ExerciseDefinition } from '../types';

/**
 * The supine family: lying on a flat bench, the body held still by it, the
 * dumbbells pressed or swept over the chest.
 */
const rig = canonicalSkeleton;

function frames(exercise: ExerciseDefinition) {
  const evaluation = new PoseEvaluation(rig);
  const clip = generateClip(rig, exercise);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  return Array.from({ length: 41 }, (_, step) => {
    const frame = resolveFrame(rig, evaluation, clip, (step / 40) * clip.duration, { anchors });
    evaluation.apply(frame.pose);
    const dumbbell = frame.equipment.get('dumbbell_l')!;
    return {
      phase: frame.phaseId,
      pelvis: evaluation.head('pelvis', new Vector3()),
      shoulder: evaluation.head('upperarm_l', new Vector3()),
      elbow: evaluation.head('forearm_l', new Vector3()),
      wrist: evaluation.head('hand_l', new Vector3()),
      elbowBend: ((frame.pose.rotations.forearm_l?.x ?? 0) * 180) / Math.PI,
      grip: new Vector3(dumbbell.position.x, dumbbell.position.y, dumbbell.position.z),
      handle: new Vector3(0, 0, 1).applyQuaternion(dumbbell.quaternion),
    };
  });
}

describe('the supine family', () => {
  it('has exactly two registered variants', () => {
    const lying = EXERCISES.filter((exercise) => exercise.equipment.instances.some((i) => i.kind === 'flat_bench'))
      .filter((exercise) => (exercise.startPose.root?.rotation?.x ?? 0) < -45);
    expect(lying.map((exercise) => exercise.id)).toEqual(['dumbbell_bench_press', 'dumbbell_fly']);
  });

  it.each([dumbbellBenchPress, dumbbellFly].map((exercise) => [exercise.id, exercise] as const))(
    '%s lies still on the bench',
    (_id, exercise) => {
      const bench = exercise.equipment.instances.find((instance) => instance.kind === 'flat_bench');
      expect(bench?.supportsBody).toBe(true);
      expect(bench?.attachment.mode).toBe('static');
      for (const frame of frames(exercise)) {
        expect(frame.pelvis.y).toBeCloseTo(0.598, 9);
        expect(frame.pelvis.z).toBeCloseTo(0, 9);
      }
    },
  );
});

describe('dumbbell bench press', () => {
  const all = frames(dumbbellBenchPress);
  const top = all.find((frame) => frame.phase === 'top')!;
  const bottom = all.find((frame) => frame.phase === 'bottom')!;

  it('presses to a soft lockout over the shoulders', () => {
    expect(top.elbowBend).toBeGreaterThan(5);
    expect(top.elbowBend).toBeLessThan(20);
    expect(Math.abs(top.wrist.z - top.shoulder.z)).toBeLessThan(0.05);
    expect(top.wrist.y - top.shoulder.y).toBeGreaterThan(0.5);
  });

  it('lowers beside the chest on vertical forearms, elbows angled towards the hips', () => {
    const forearm = bottom.wrist.clone().sub(bottom.elbow).normalize();
    expect((Math.acos(forearm.y) * 180) / Math.PI).toBeLessThan(10);
    // About 60° out from the trunk, not flared to 90°.
    expect(bottom.elbow.z - bottom.shoulder.z).toBeGreaterThan(0.1);
    // Just below the shoulder: the upper arm level or a little under.
    expect(bottom.elbow.y - bottom.shoulder.y).toBeGreaterThan(-0.1);
    expect(bottom.elbow.y - bottom.shoulder.y).toBeLessThan(0);
  });

  it('holds the handles across the body, pronated', () => {
    // Within 45° of straight across: 31° at either end, 41.6° mid-press.
    for (const frame of all) expect(Math.abs(frame.handle.x)).toBeGreaterThan(Math.cos((45 * Math.PI) / 180));
  });
});

describe('dumbbell fly', () => {
  const all = frames(dumbbellFly);
  const top = all.find((frame) => frame.phase === 'top')!;
  const bottom = all.find((frame) => frame.phase === 'bottom')!;

  it('keeps the elbow soft and fixed', () => {
    for (const frame of all) expect(frame.elbowBend).toBeCloseTo(20, 6);
  });

  it('opens until the upper arm is level with the chest, and no lower', () => {
    const arm = bottom.elbow.clone().sub(bottom.shoulder).normalize();
    expect(Math.abs(arm.y)).toBeLessThan(0.1);
    for (const frame of all) expect(frame.grip.y).toBeGreaterThan(frame.shoulder.y);
  });

  it('sweeps across the chest, not towards the head or the hips', () => {
    for (const frame of all) {
      expect(frame.wrist.z - frame.shoulder.z).toBeGreaterThan(-0.08);
      expect(frame.wrist.z - frame.shoulder.z).toBeLessThan(0.12);
    }
  });

  it('holds the handles along the body, palms in at the top and up at the bottom', () => {
    // Within 12° of the body's long axis the whole way (11° measured).
    for (const frame of all) expect(Math.abs(frame.handle.z)).toBeGreaterThan(Math.cos((12 * Math.PI) / 180));
    // Palms in: the grip sits towards the midline of the wrist.
    expect(top.grip.x - top.wrist.x).toBeGreaterThan(0.03);
    // Palms up: the grip sits above the line of the forearm.
    const forearm = bottom.wrist.clone().sub(bottom.elbow).normalize();
    const up = new Vector3(-forearm.y, forearm.x, 0).normalize();
    if (up.y < 0) up.negate();
    expect(bottom.grip.clone().sub(bottom.wrist).dot(up)).toBeGreaterThan(0.01);
  });
});
