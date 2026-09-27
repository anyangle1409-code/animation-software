import { describe, expect, it } from 'vitest';
import { HgMat4, HgQuat, HgVec3 } from './linearMath';

const close = (actual: number, expected: number, epsilon = 1e-10) => {
  expect(Math.abs(actual - expected)).toBeLessThan(epsilon);
};

const closeVec = (actual: HgVec3, expected: HgVec3, epsilon = 1e-10) => {
  close(actual.x, expected.x, epsilon);
  close(actual.y, expected.y, epsilon);
  close(actual.z, expected.z, epsilon);
};

describe('first-party linear algebra', () => {
  it('implements right-handed vector cross products', () => {
    const x = new HgVec3(1, 0, 0);
    const y = new HgVec3(0, 1, 0);
    closeVec(new HgVec3().crossVectors(x, y), new HgVec3(0, 0, 1));
  });

  it('uses the project XZY Euler convention used by the rig', () => {
    const flexion = 0.37;
    const abduction = -0.28;
    const q = new HgQuat().setFromEulerXZY(flexion, 0, abduction);
    const direction = new HgVec3(0, 1, 0).applyQuaternion(q);

    // This is the analytical identity already used by ik/orient.ts:
    // d = (-sin z, cos x cos z, sin x cos z).
    close(direction.x, -Math.sin(abduction));
    close(direction.y, Math.cos(flexion) * Math.cos(abduction));
    close(direction.z, Math.sin(flexion) * Math.cos(abduction));
  });

  it('round-trips a composed affine transform through its inverse', () => {
    const position = new HgVec3(0.7, 1.2, -0.4);
    const rotation = new HgQuat().setFromEulerXZY(0.2, -0.15, 0.31);
    const scale = new HgVec3(1.2, 0.8, 1.05);
    const matrix = new HgMat4().compose(position, rotation, scale);
    const inverse = matrix.clone().invert();

    const point = new HgVec3(-0.2, 0.5, 0.9);
    const roundTrip = point.clone().applyMatrix4(matrix).applyMatrix4(inverse);
    closeVec(roundTrip, point, 1e-9);
  });

  it('preserves parent/local multiplication order', () => {
    const parent = new HgMat4().compose(
      new HgVec3(1, 0, 0),
      new HgQuat().setFromAxisAngle(new HgVec3(0, 0, 1), Math.PI / 2),
      new HgVec3(1, 1, 1),
    );
    const local = new HgMat4().compose(
      new HgVec3(0, 2, 0),
      new HgQuat(),
      new HgVec3(1, 1, 1),
    );
    const world = new HgMat4().multiplyMatrices(parent, local);
    closeVec(new HgVec3().setFromMatrixPosition(world), new HgVec3(-1, 0, 0), 1e-10);
  });

  it('recovers a quaternion from an orthonormal basis', () => {
    const source = new HgQuat().setFromEulerXZY(0.4, -0.2, 0.3);
    const x = new HgVec3(1, 0, 0).applyQuaternion(source);
    const y = new HgVec3(0, 1, 0).applyQuaternion(source);
    const z = new HgVec3(0, 0, 1).applyQuaternion(source);
    const matrix = new HgMat4().makeBasis(x, y, z);
    const recovered = new HgQuat().setFromRotationMatrix(matrix);

    // q and -q encode the same rotation.
    close(Math.abs(recovered.dot(source)), 1, 1e-10);
  });

  it('slerps on the shortest quaternion arc', () => {
    const start = new HgQuat();
    const end = new HgQuat().setFromAxisAngle(new HgVec3(0, 0, 1), Math.PI);
    const half = start.clone().slerp(end, 0.5);
    closeVec(
      new HgVec3(1, 0, 0).applyQuaternion(half),
      new HgVec3(0, 1, 0),
      1e-9,
    );
  });
});
