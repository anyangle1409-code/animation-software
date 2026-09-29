import { describe, expect, it } from 'vitest';
import { Euler, Matrix4, Quaternion, Vector3 } from 'three';
import { PoseEvaluation, canonicalSkeleton } from '../rig/skeleton';
import { restPose } from '../rig/pose';
import type { EquipmentInstance } from './types';
import { cableMatrix, resolveEquipment, socketWorldPoint } from './attach';

const expectMatrixParity = (
  actual: { elements: ArrayLike<number> },
  expected: Matrix4,
  precision = 11,
) => {
  for (let index = 0; index < 16; index += 1) {
    expect(actual.elements[index]).toBeCloseTo(expected.elements[index], precision);
  }
};

describe('first-party equipment attachment parity', () => {
  it('matches Three static XZY placement', () => {
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
    const expected = new Matrix4().compose(
      new Vector3(0.35, 0.12, -0.42),
      new Quaternion().setFromEuler(
        new Euler(
          (17 * Math.PI) / 180,
          (-31 * Math.PI) / 180,
          (9 * Math.PI) / 180,
          'XZY',
        ),
      ),
      new Vector3(1, 1, 1),
    );
    expectMatrixParity(actual.matrix, expected);
  });

  it('matches Three cable orientation, scale and matrix', () => {
    const from = new Vector3(-0.2, 1.7, 0.4);
    const to = new Vector3(0.55, 0.82, -0.31);
    const actual = cableMatrix(from, to);
    const along = to.clone().sub(from);
    const length = along.length();
    const quaternion = new Quaternion().setFromUnitVectors(
      new Vector3(0, 1, 0),
      along.clone().divideScalar(length),
    );
    const scale = new Vector3(1, length, 1);
    const expected = new Matrix4().compose(from, quaternion, scale);
    expect(actual.position.x).toBeCloseTo(from.x, 12);
    expect(actual.position.y).toBeCloseTo(from.y, 12);
    expect(actual.position.z).toBeCloseTo(from.z, 12);
    expect(actual.scale.y).toBeCloseTo(length, 12);
    expectMatrixParity(actual.matrix, expected);
  });

  it('accepts a Three placement at the socket compatibility boundary', () => {
    const instance: EquipmentInstance = {
      id: 'socket',
      kind: 'dumbbell',
      position: { x: 0, y: 0, z: 0 },
      rotation: { x: 0, y: 0, z: 0 },
      attachment: { mode: 'static' },
      visible: true,
    };
    const placement = new Matrix4().compose(
      new Vector3(0.4, 1.2, -0.3),
      new Quaternion().setFromEuler(new Euler(0.2, -0.15, 0.1, 'XZY')),
      new Vector3(1, 1, 1),
    );
    const actual = socketWorldPoint(instance, 'grip', placement);
    expect(actual).not.toBeNull();
    if (!actual) return;
    const socket = new Vector3(0, 0, 0).applyMatrix4(placement);
    expect(actual.x).toBeCloseTo(socket.x, 12);
    expect(actual.y).toBeCloseTo(socket.y, 12);
    expect(actual.z).toBeCloseTo(socket.z, 12);
  });
});
