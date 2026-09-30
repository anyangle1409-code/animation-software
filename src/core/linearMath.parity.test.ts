import { describe, expect, it } from 'vitest';
import { Euler, Matrix4, Quaternion, Vector3 } from 'three';
import { HgMat4, HgQuat, HgVec3 } from './linearMath';

const EPS = 1e-12;

function expectVecParity(hg: HgVec3, three: Vector3, epsilon = EPS) {
  expect(Math.abs(hg.x - three.x)).toBeLessThan(epsilon);
  expect(Math.abs(hg.y - three.y)).toBeLessThan(epsilon);
  expect(Math.abs(hg.z - three.z)).toBeLessThan(epsilon);
}

function expectQuatParity(hg: HgQuat, three: Quaternion, epsilon = EPS) {
  const dot = Math.abs(hg.x * three.x + hg.y * three.y + hg.z * three.z + hg.w * three.w);
  expect(Math.abs(1 - dot)).toBeLessThan(epsilon);
}

function expectMatrixParity(hg: HgMat4, three: Matrix4, epsilon = EPS) {
  hg.elements.forEach((value, index) => {
    expect(Math.abs(value - three.elements[index]), `matrix element ${index}`).toBeLessThan(epsilon);
  });
}

const ANGLES = [
  [0, 0, 0],
  [0.2, 0, -0.3],
  [-0.7, 0.4, 0.8],
  [1.1, -0.5, -0.9],
  [Math.PI / 2 - 0.01, 0.2, 0.6],
] as const;

describe('first-party math migration parity against Three.js', () => {
  it('matches vector angles used by the foot aim residual, including zero vectors', () => {
    const pairs = [
      [[0, 1, 0], [0.2, 0.8, 0.4]],
      [[0, 0, 1], [-0.4, 0.1, 0.2]],
      [[1, 0, 0], [-1, 0, 0]],
      [[0, 0, 0], [0, 1, 0]],
    ] as const;
    for (const [[ax, ay, az], [bx, by, bz]] of pairs) {
      const actual = new HgVec3(ax, ay, az).angleTo(new HgVec3(bx, by, bz));
      const expected = new Vector3(ax, ay, az).angleTo(new Vector3(bx, by, bz));
      expect(Math.abs(actual - expected)).toBeLessThan(EPS);
    }
  });

  it('matches XYZ Euler to quaternion conversion used by equipment parts', () => {
    for (const [x, y, z] of ANGLES) {
      const hg = new HgQuat().setFromEulerXYZ(x, y, z);
      const three = new Quaternion().setFromEuler(new Euler(x, y, z, 'XYZ'));
      expectQuatParity(hg, three);
    }
  });

  it('matches XZY Euler to quaternion conversion', () => {
    for (const [x, y, z] of ANGLES) {
      const hg = new HgQuat().setFromEulerXZY(x, y, z);
      const three = new Quaternion().setFromEuler(new Euler(x, y, z, 'XZY'));
      expectQuatParity(hg, three);
    }
  });

  it('preserves quaternion multiply and premultiply parity when the output aliases an input', () => {
    const hgA = new HgQuat().setFromEulerXZY(0.3, -0.2, 0.4);
    const hgB = new HgQuat().setFromEulerXZY(-0.5, 0.15, -0.1);
    const threeA = new Quaternion().setFromEuler(new Euler(0.3, -0.2, 0.4, 'XZY'));
    const threeB = new Quaternion().setFromEuler(new Euler(-0.5, 0.15, -0.1, 'XZY'));

    expectQuatParity(hgA.clone().multiply(hgB), threeA.clone().multiply(threeB));
    expectQuatParity(hgB.clone().premultiply(hgA), threeB.clone().premultiply(threeA));
  });

  it('matches quaternion vector transforms', () => {
    const vectors = [
      [1, 0, 0],
      [0, 1, 0],
      [0.3, -0.8, 1.1],
      [-2, 0.25, 0.4],
    ] as const;

    for (const [x, y, z] of ANGLES) {
      const hgQ = new HgQuat().setFromEulerXZY(x, y, z);
      const threeQ = new Quaternion().setFromEuler(new Euler(x, y, z, 'XZY'));
      for (const [vx, vy, vz] of vectors) {
        const hg = new HgVec3(vx, vy, vz).applyQuaternion(hgQ);
        const three = new Vector3(vx, vy, vz).applyQuaternion(threeQ);
        expectVecParity(hg, three);
      }
    }
  });

  it('matches affine compose', () => {
    const positions = [
      [0, 0, 0],
      [0.4, 1.2, -0.7],
      [-2.1, 0.03, 4.2],
    ] as const;
    const scales = [
      [1, 1, 1],
      [1.2, 0.7, 1.05],
    ] as const;

    for (const [x, y, z] of ANGLES.slice(0, 4)) {
      const hgQ = new HgQuat().setFromEulerXZY(x, y, z);
      const threeQ = new Quaternion().setFromEuler(new Euler(x, y, z, 'XZY'));
      for (const [px, py, pz] of positions) {
        for (const [sx, sy, sz] of scales) {
          const hg = new HgMat4().compose(
            new HgVec3(px, py, pz),
            hgQ,
            new HgVec3(sx, sy, sz),
          );
          const three = new Matrix4().compose(
            new Vector3(px, py, pz),
            threeQ,
            new Vector3(sx, sy, sz),
          );
          expectMatrixParity(hg, three);
        }
      }
    }
  });

  it('matches matrix multiplication and inversion', () => {
    const hgA = new HgMat4().compose(
      new HgVec3(0.4, 1.3, -0.5),
      new HgQuat().setFromEulerXZY(0.2, -0.4, 0.6),
      new HgVec3(1, 1, 1),
    );
    const hgB = new HgMat4().compose(
      new HgVec3(-0.2, 0.8, 0.9),
      new HgQuat().setFromEulerXZY(-0.3, 0.1, -0.2),
      new HgVec3(1, 1, 1),
    );

    const threeA = new Matrix4().compose(
      new Vector3(0.4, 1.3, -0.5),
      new Quaternion().setFromEuler(new Euler(0.2, -0.4, 0.6, 'XZY')),
      new Vector3(1, 1, 1),
    );
    const threeB = new Matrix4().compose(
      new Vector3(-0.2, 0.8, 0.9),
      new Quaternion().setFromEuler(new Euler(-0.3, 0.1, -0.2, 'XZY')),
      new Vector3(1, 1, 1),
    );

    expectMatrixParity(new HgMat4().multiplyMatrices(hgA, hgB), new Matrix4().multiplyMatrices(threeA, threeB));
    expectMatrixParity(hgA.clone().multiply(hgB), threeA.clone().multiply(threeB));
    expectMatrixParity(hgB.clone().premultiply(hgA), threeB.clone().premultiply(threeA));
    expectMatrixParity(hgA.clone().invert(), threeA.clone().invert(), 1e-11);
  });

  it('matches bone-frame basis construction for representative bone directions', () => {
    const directions = [
      [0, 1, 0],
      [0.2, -0.95, 0.1],
      [-0.8, 0.2, 0.4],
      [0.01, 0.02, 1],
    ] as const;

    const hgForward = new HgVec3(0, 0, 1);
    const hgUp = new HgVec3(0, 1, 0);
    const threeForward = new Vector3(0, 0, 1);
    const threeUp = new Vector3(0, 1, 0);

    for (const [dx, dy, dz] of directions) {
      const hgY = new HgVec3(dx, dy, dz).normalize();
      const hgReference = Math.abs(hgY.dot(hgForward)) > 0.985 ? hgUp : hgForward;
      const hgZ = hgReference.clone().addScaledVector(hgY, -hgY.dot(hgReference)).normalize();
      const hgX = new HgVec3().crossVectors(hgY, hgZ).normalize();
      const hgQ = new HgQuat().setFromRotationMatrix(new HgMat4().makeBasis(hgX, hgY, hgZ));

      const threeY = new Vector3(dx, dy, dz).normalize();
      const threeReference = Math.abs(threeY.dot(threeForward)) > 0.985 ? threeUp : threeForward;
      const threeZ = threeReference.clone().addScaledVector(threeY, -threeY.dot(threeReference)).normalize();
      const threeX = new Vector3().crossVectors(threeY, threeZ).normalize();
      const threeQ = new Quaternion().setFromRotationMatrix(new Matrix4().makeBasis(threeX, threeY, threeZ));

      expectQuatParity(hgQ, threeQ, 1e-11);
    }
  });
  it('matches shortest-arc unit-vector quaternion construction', () => {
    const pairs = [
      [[0, 0, 1], [0.2, 0.8, 0.4]],
      [[1, 0, 0], [-1, 0, 0]],
      [[0, 1, 0], [0, -1, 0]],
      [[0.3, -0.4, 0.5], [-0.2, 0.9, 0.1]],
    ] as const;
    for (const [fromRaw, toRaw] of pairs) {
      const hgFrom = new HgVec3(...fromRaw).normalize();
      const hgTo = new HgVec3(...toRaw).normalize();
      const threeFrom = new Vector3(...fromRaw).normalize();
      const threeTo = new Vector3(...toRaw).normalize();
      expectQuatParity(
        new HgQuat().setFromUnitVectors(hgFrom, hgTo),
        new Quaternion().setFromUnitVectors(threeFrom, threeTo),
        1e-11,
      );
    }
  });

  it('matches translation, rotation extraction and affine decomposition', () => {
    const cases = [
      {
        position: [0.2, 1.1, -0.4] as const,
        rotation: [0.3, -0.2, 0.5] as const,
        scale: [1, 1, 1] as const,
      },
      {
        position: [-0.7, 0.4, 2.1] as const,
        rotation: [-0.4, 0.6, -0.2] as const,
        scale: [1.3, 0.8, 1.1] as const,
      },
    ];

    for (const entry of cases) {
      const [px, py, pz] = entry.position;
      const [rx, ry, rz] = entry.rotation;
      const [sx, sy, sz] = entry.scale;
      const hg = new HgMat4().compose(
        new HgVec3(px, py, pz),
        new HgQuat().setFromEulerXZY(rx, ry, rz),
        new HgVec3(sx, sy, sz),
      );
      const three = new Matrix4().compose(
        new Vector3(px, py, pz),
        new Quaternion().setFromEuler(new Euler(rx, ry, rz, 'XZY')),
        new Vector3(sx, sy, sz),
      );

      expectMatrixParity(new HgMat4().extractRotation(hg), new Matrix4().extractRotation(three), 1e-11);
      expectMatrixParity(
        new HgMat4().makeTranslation(px, py, pz),
        new Matrix4().makeTranslation(px, py, pz),
      );

      const hgP = new HgVec3(), hgQ = new HgQuat(), hgS = new HgVec3();
      const threeP = new Vector3(), threeQ = new Quaternion(), threeS = new Vector3();
      hg.clone().decompose(hgP, hgQ, hgS);
      three.clone().decompose(threeP, threeQ, threeS);
      expectVecParity(hgP, threeP, 1e-11);
      expectQuatParity(hgQ, threeQ, 1e-11);
      expectVecParity(hgS, threeS, 1e-11);
    }
  });

  it('round-trips vectors, quaternions and matrices through plain arrays', () => {
    const v = new HgVec3(0.2, -0.3, 1.4);
    const q = new HgQuat().setFromEulerXZY(0.2, 0.1, -0.4);
    const m = new HgMat4().compose(v, q, new HgVec3(1.1, 0.9, 1.2));
    expect(v.toArray()).toEqual([0.2, -0.3, 1.4]);
    expect(q.toArray()).toHaveLength(4);
    expectMatrixParity(new HgMat4().fromArray(m.toArray()), new Matrix4().fromArray(m.toArray()));
  });

  it('matches vector distance-squared and set-length operations used by retarget contact IK', () => {
    const hg = new HgVec3(0.3, -0.4, 0.5);
    const three = new Vector3(0.3, -0.4, 0.5);
    const hgOther = new HgVec3(-0.2, 0.1, 0.9);
    const threeOther = new Vector3(-0.2, 0.1, 0.9);
    expect(Math.abs(hg.distanceToSquared(hgOther) - three.distanceToSquared(threeOther))).toBeLessThan(EPS);
    expectVecParity(hg.clone().setLength(0.25), three.clone().setLength(0.25), 1e-12);
  });

  it('matches XZY quaternion-to-Euler conversion used by editor gizmos', () => {
    const cases = [
      ...ANGLES,
      [0.3, -0.2, Math.PI / 2 - 1e-8],
      [-0.5, 0.4, -Math.PI / 2 + 1e-8],
    ] as const;
    for (const [x, y, z] of cases) {
      const hgQ = new HgQuat().setFromEulerXZY(x, y, z);
      const threeQ = new Quaternion().setFromEuler(new Euler(x, y, z, 'XZY'));
      const hg = hgQ.toEulerXZY();
      const three = new Euler().setFromQuaternion(threeQ, 'XZY');
      expect(Math.abs(hg.x - three.x)).toBeLessThan(1e-10);
      expect(Math.abs(hg.y - three.y)).toBeLessThan(1e-10);
      expect(Math.abs(hg.z - three.z)).toBeLessThan(1e-10);
    }
  });

  it('matches vector setScalar and quaternion angleTo compatibility operations', () => {
    expectVecParity(
      new HgVec3().setScalar(0.37),
      new Vector3().setScalar(0.37),
      1e-12,
    );
    const hgA = new HgQuat().setFromEulerXYZ(0.2, -0.4, 0.1);
    const hgB = new HgQuat().setFromEulerXYZ(-0.3, 0.15, 0.5);
    const threeA = new Quaternion().setFromEuler(new Euler(0.2, -0.4, 0.1, 'XYZ'));
    const threeB = new Quaternion().setFromEuler(new Euler(-0.3, 0.15, 0.5, 'XYZ'));
    expect(Math.abs(hgA.angleTo(hgB) - threeA.angleTo(threeB))).toBeLessThan(1e-12);
  });

});
