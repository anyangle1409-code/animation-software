import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { shoulderPress } from '../exercises/definitions/shoulderPress';
import type { BoneName, Side } from '../rig/boneNames';
import { anatomicalGripOffset } from './attach';

const skeleton = canonicalSkeleton;
const evaluation = new PoseEvaluation(skeleton);

/**
 * Points around the closed hand that should be wrapped around a handle, and how
 * far each may sit from the bar's centre line. The four fingers cross the bar,
 * so they are held close; the thumb lies along it, which this rig can manage
 * because its knuckle has no opposition joint to bring the pad across the palm.
 */
const gripPoints = (side: Side): { bone: BoneName; along: number; reach: number }[] => [
  { bone: `index_02_${side}` as BoneName, along: 0.5, reach: 0.032 },
  { bone: `index_03_${side}` as BoneName, along: 1, reach: 0.04 },
  { bone: `middle_02_${side}` as BoneName, along: 0.5, reach: 0.032 },
  { bone: `middle_03_${side}` as BoneName, along: 1, reach: 0.04 },
  { bone: `ring_02_${side}` as BoneName, along: 0.5, reach: 0.034 },
  { bone: `pinky_02_${side}` as BoneName, along: 0.5, reach: 0.038 },
  { bone: `thumb_02_${side}` as BoneName, along: 0.5, reach: 0.042 },
  { bone: `thumb_03_${side}` as BoneName, along: 1, reach: 0.032 },
];

const pointOf = (bone: BoneName, along: number): Vector3 =>
  along >= 1 ? evaluation.tail(bone, new Vector3()) : evaluation.head(bone, new Vector3());

describe.each([
  ['Dumbbell Bicep Curl', bicepCurl],
  ['Dumbbell Shoulder Press', shoulderPress],
])('%s grip', (_name, exercise) => {
  const clip = generateClip(skeleton, exercise);
  // Bottom, midpoint and top of the movement, plus the frames between them.
  const times = Array.from({ length: 13 }, (_, index) => (index / 12) * clip.duration);

  it('keeps each handle wrapped by the fingers and thumb', () => {
    for (const time of times) {
      const frame = resolveFrame(skeleton, evaluation, clip, time);
      evaluation.apply(frame.pose);

      for (const side of ['l', 'r'] as const) {
        const dumbbell = frame.equipment.get(`dumbbell_${side}`);
        expect(dumbbell, `dumbbell_${side}`).toBeDefined();
        const handle = dumbbell!.position;
        // The bar of a dumbbell runs along its own +Z.
        const axis = new Vector3(0, 0, 1).applyQuaternion(dumbbell!.quaternion).normalize();
        const up = new Vector3(0, 1, 0).addScaledVector(axis, -axis.y).normalize();
        const across = new Vector3().crossVectors(up, axis);

        const angles: number[] = [];
        for (const { bone, along, reach } of gripPoints(side)) {
          const offset = pointOf(bone, along).sub(handle);
          // Distance from the bar's own centre line: a hand that has let go, or
          // one holding a handle buried in its palm, fails here.
          offset.addScaledVector(axis, -offset.dot(axis));
          expect(offset.length(), `${bone} at ${time.toFixed(2)}s`).toBeLessThan(reach);
          angles.push(Math.atan2(offset.dot(up), offset.dot(across)));
        }

        // The fingers must come round the handle rather than lying against one
        // side of it: sort the contact angles and check no gap is wide enough
        // for the handle to fall out.
        angles.sort((a, b) => a - b);
        let widest = angles[0] + Math.PI * 2 - angles[angles.length - 1];
        for (let index = 1; index < angles.length; index += 1) {
          widest = Math.max(widest, angles[index] - angles[index - 1]);
        }
        expect((widest * 180) / Math.PI, `${side} hand at ${time.toFixed(2)}s`).toBeLessThan(170);
      }
    }
  });

  it('holds the handle at the anatomical grip point in the hand', () => {
    for (const time of times) {
      const frame = resolveFrame(skeleton, evaluation, clip, time);
      evaluation.apply(frame.pose);
      for (const side of ['l', 'r'] as const) {
        const expected = evaluation.localToWorld(
          `hand_${side}`,
          anatomicalGripOffset(side),
          new Vector3(),
        );
        // Rigidly attached: the handle is exactly where the hand puts it, with
        // no drift of its own at any point in the repetition.
        expect(frame.equipment.get(`dumbbell_${side}`)!.position.distanceTo(expected)).toBeLessThan(
          1e-9,
        );
      }
    }
  });

  it('turns the dumbbell with the hand rather than sliding in it', () => {
    const first = resolveFrame(skeleton, evaluation, clip, 0);
    evaluation.apply(first.pose);
    const reference = new Map<Side, Vector3>();
    for (const side of ['l', 'r'] as const) {
      const dumbbell = first.equipment.get(`dumbbell_${side}`)!;
      // The bar axis, expressed in the hand's own frame.
      reference.set(
        side,
        evaluation
          .worldToLocal(
            `hand_${side}`,
            new Vector3(0, 0, 1).applyQuaternion(dumbbell.quaternion).add(dumbbell.position),
            new Vector3(),
          )
          .sub(evaluation.worldToLocal(`hand_${side}`, dumbbell.position.clone(), new Vector3()))
          .normalize(),
      );
    }

    for (const time of times) {
      const frame = resolveFrame(skeleton, evaluation, clip, time);
      evaluation.apply(frame.pose);
      for (const side of ['l', 'r'] as const) {
        const dumbbell = frame.equipment.get(`dumbbell_${side}`)!;
        const axis = evaluation
          .worldToLocal(
            `hand_${side}`,
            new Vector3(0, 0, 1).applyQuaternion(dumbbell.quaternion).add(dumbbell.position),
            new Vector3(),
          )
          .sub(evaluation.worldToLocal(`hand_${side}`, dumbbell.position.clone(), new Vector3()))
          .normalize();
        expect(axis.angleTo(reference.get(side)!), `${side} at ${time.toFixed(2)}s`).toBeLessThan(
          1e-6,
        );
      }
    }
  });
});
