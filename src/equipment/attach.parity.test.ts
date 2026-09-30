import { describe, expect, it } from 'vitest';
import { HgMat4, HgQuat, HgVec3 } from '../core/linearMath';
import { PoseEvaluation, Skeleton, canonicalSkeleton } from '../rig/skeleton';
import { HGPT_CANONICAL_V4_ORIGINAL_BONES } from '../rig/canonicalV4Original';
import { restPose } from '../rig/pose';
import type { EquipmentInstance } from './types';
import {
  anatomicalGripOffset,
  cableMatrix,
  handAttachmentLocalMatrix,
  resolveEquipment,
  socketWorldPoint,
} from './attach';

const expectMatrixParity = (
  actual: { elements: ArrayLike<number> },
  expected: { elements: ArrayLike<number> },
  precision = 11,
) => {
  for (let index = 0; index < 16; index += 1) {
    expect(actual.elements[index]).toBeCloseTo(expected.elements[index], precision);
  }
};

const degreesXzy = (value: { x: number; y: number; z: number }) =>
  new HgQuat().setFromEulerXZY(
    (value.x * Math.PI) / 180,
    (value.y * Math.PI) / 180,
    (value.z * Math.PI) / 180,
  );

describe('first-party equipment attachment', () => {
  it('matches the explicit static XZY placement composition', () => {
    const instance: EquipmentInstance = {
      id: 'static',
      kind: 'flat_bench',
      position: { x: 0.35, y: 0.12, z: -0.42 },
      rotation: { x: 17, y: -31, z: 9 },
      attachment: { mode: 'static' },
      visible: true,
    };
    const evaluation = new PoseEvaluation(canonicalSkeleton).apply(restPose());
    const actual = resolveEquipment(evaluation, [instance]).get(instance.id)!;
    const expected = new HgMat4().compose(
      new HgVec3(0.35, 0.12, -0.42),
      degreesXzy(instance.rotation),
      new HgVec3(1, 1, 1),
    );
    expectMatrixParity(actual.matrix, expected);
  });

  it('matches the explicit hand-local grip and socket composition', () => {
    const grip = { x: -0.021, y: 0.083, z: 0.006 };
    const socket = { x: 0.012, y: -0.004, z: 0.031 };
    const gripRotation = { x: 13, y: -8, z: 17 };
    const socketRotation = { x: -11, y: 6, z: 9 };
    const actual = handAttachmentLocalMatrix(grip, socket, { gripRotation, socketRotation });

    const expected = new HgMat4()
      .compose(new HgVec3(grip.x, grip.y, grip.z), degreesXzy(gripRotation), new HgVec3(1, 1, 1))
      .multiply(
        new HgMat4()
          .compose(new HgVec3(socket.x, socket.y, socket.z), degreesXzy(socketRotation), new HgVec3(1, 1, 1))
          .invert(),
      );
    expectMatrixParity(actual, expected);
  });

  it('preserves the accepted v3 generic grip point and scales it to v4 hand length', () => {
    expect(anatomicalGripOffset('l')).toEqual({ x: -0.025, y: 0.085, z: 0 });
    expect(anatomicalGripOffset('r')).toEqual({ x: 0.025, y: 0.085, z: 0 });

    const v4 = new Skeleton(HGPT_CANONICAL_V4_ORIGINAL_BONES);
    const scale = v4.bone('hand_l').length / canonicalSkeleton.bone('hand_l').length;
    const left = anatomicalGripOffset('l', v4.bone('hand_l').length);
    expect(left.x).toBeCloseTo(-0.025 * scale, 12);
    expect(left.y).toBeCloseTo(0.085 * scale, 12);
    expect(left.z).toBe(0);
  });

  it('places a v4 fallback hand-held item at the v4-scaled grip point', () => {
    const skeleton = new Skeleton(HGPT_CANONICAL_V4_ORIGINAL_BONES);
    const evaluation = new PoseEvaluation(skeleton).apply(restPose());
    const instance: EquipmentInstance = {
      id: 'v4_dumbbell',
      kind: 'dumbbell',
      position: { x: 0, y: 0, z: 0 },
      rotation: { x: 0, y: 0, z: 0 },
      attachment: { mode: 'hand', side: 'l', socket: 'grip' },
      visible: true,
    };
    const transform = resolveEquipment(evaluation, [instance]).get(instance.id)!;
    const expected = evaluation.localToWorld(
      'hand_l',
      anatomicalGripOffset('l', skeleton.bone('hand_l').length),
      new HgVec3(),
    );
    expect(transform.position.distanceTo(expected)).toBeLessThan(1e-9);
  });

  it('matches an explicit cable orientation, scale and matrix composition', () => {
    const from = new HgVec3(-0.2, 1.7, 0.4);
    const to = new HgVec3(0.55, 0.82, -0.31);
    const actual = cableMatrix(from, to);
    const along = to.clone().sub(from);
    const length = along.length();
    const quaternion = new HgQuat().setFromUnitVectors(
      new HgVec3(0, 1, 0),
      along.clone().normalize(),
    );
    const scale = new HgVec3(1, length, 1);
    const expected = new HgMat4().compose(from, quaternion, scale);
    expect(actual.position.x).toBeCloseTo(from.x, 12);
    expect(actual.position.y).toBeCloseTo(from.y, 12);
    expect(actual.position.z).toBeCloseTo(from.z, 12);
    expect(actual.scale.y).toBeCloseTo(length, 12);
    expectMatrixParity(actual.matrix, expected);
  });

  it('accepts a first-party placement at the socket boundary', () => {
    const instance: EquipmentInstance = {
      id: 'socket',
      kind: 'dumbbell',
      position: { x: 0, y: 0, z: 0 },
      rotation: { x: 0, y: 0, z: 0 },
      attachment: { mode: 'static' },
      visible: true,
    };
    const placement = new HgMat4().compose(
      new HgVec3(0.4, 1.2, -0.3),
      new HgQuat().setFromEulerXZY(0.2, -0.15, 0.1),
      new HgVec3(1, 1, 1),
    );
    const actual = socketWorldPoint(instance, 'grip', placement);
    expect(actual).not.toBeNull();
    if (!actual) return;
    const socket = new HgVec3(0, 0, 0).applyMatrix4(placement);
    expect(actual.x).toBeCloseTo(socket.x, 12);
    expect(actual.y).toBeCloseTo(socket.y, 12);
    expect(actual.z).toBeCloseTo(socket.z, 12);
  });
});
