import { describe, expect, it } from 'vitest';
import { HgMat4, HgQuat, HgVec3 } from './linearMath';

const EPS = 1e-11;
const IDENTITY = [
  1, 0, 0, 0,
  0, 1, 0, 0,
  0, 0, 1, 0,
  0, 0, 0, 1,
];

const ANGLES = [
  [0, 0, 0],
  [0.2, 0, -0.3],
  [-0.7, 0.4, 0.8],
  [1.1, -0.5, -0.9],
  [Math.PI / 2 - 0.01, 0.2, 0.6],
] as const;

const closeArray = (
  actual: ArrayLike<number>,
  expected: ArrayLike<number>,
  epsilon = EPS,
) => {
  expect(actual.length).toBe(expected.length);
  for (let index = 0; index < actual.length; index += 1) {
    expect(Math.abs(Number(actual[index]) - Number(expected[index])), String(index))
      .toBeLessThan(epsilon);
  }
};

const quaternionAgreement = (
  a: { x: number; y: number; z: number; w: number },
  b: { x: number; y: number; z: number; w: number },
) => Math.abs(a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w);

const manualEulerXYZ = (x: number, y: number, z: number) => {
  const c1 = Math.cos(x / 2), c2 = Math.cos(y / 2), c3 = Math.cos(z / 2);
  const s1 = Math.sin(x / 2), s2 = Math.sin(y / 2), s3 = Math.sin(z / 2);
  return [
    s1 * c2 * c3 + c1 * s2 * s3,
    c1 * s2 * c3 - s1 * c2 * s3,
    c1 * c2 * s3 + s1 * s2 * c3,
    c1 * c2 * c3 - s1 * s2 * s3,
  ];
};

const manualEulerXZY = (x: number, y: number, z: number) => {
  const c1 = Math.cos(x / 2), c2 = Math.cos(y / 2), c3 = Math.cos(z / 2);
  const s1 = Math.sin(x / 2), s2 = Math.sin(y / 2), s3 = Math.sin(z / 2);
  return [
    s1 * c2 * c3 - c1 * s2 * s3,
    c1 * s2 * c3 - s1 * c2 * s3,
    c1 * c2 * s3 + s1 * s2 * c3,
    c1 * c2 * c3 + s1 * s2 * s3,
  ];
};

const manualHamilton = (
  a: readonly number[],
  b: readonly number[],
): [number, number, number, number] => {
  const [ax, ay, az, aw] = a;
  const [bx, by, bz, bw] = b;
  return [
    aw * bx + ax * bw + ay * bz - az * by,
    aw * by - ax * bz + ay * bw + az * bx,
    aw * bz + ax * by - ay * bx + az * bw,
    aw * bw - ax * bx - ay * by - az * bz,
  ];
};

const manualCompose = (
  position: readonly [number, number, number],
  q: readonly [number, number, number, number],
  scale: readonly [number, number, number],
): number[] => {
  const [x, y, z, w] = q;
  const [sx, sy, sz] = scale;
  const x2 = x + x, y2 = y + y, z2 = z + z;
  const xx = x * x2, xy = x * y2, xz = x * z2;
  const yy = y * y2, yz = y * z2, zz = z * z2;
  const wx = w * x2, wy = w * y2, wz = w * z2;
  return [
    (1 - (yy + zz)) * sx,
    (xy + wz) * sx,
    (xz - wy) * sx,
    0,
    (xy - wz) * sy,
    (1 - (xx + zz)) * sy,
    (yz + wx) * sy,
    0,
    (xz + wy) * sz,
    (yz - wx) * sz,
    (1 - (xx + yy)) * sz,
    0,
    position[0],
    position[1],
    position[2],
    1,
  ];
};

const manualMultiply = (a: ArrayLike<number>, b: ArrayLike<number>): number[] => {
  const out = Array(16).fill(0) as number[];
  for (let column = 0; column < 4; column += 1) {
    for (let row = 0; row < 4; row += 1) {
      let value = 0;
      for (let k = 0; k < 4; k += 1) {
        value += Number(a[k * 4 + row]) * Number(b[column * 4 + k]);
      }
      out[column * 4 + row] = value;
    }
  }
  return out;
};

const rotateVector = (
  q: { x: number; y: number; z: number; w: number },
  v: readonly [number, number, number],
): [number, number, number] => {
  const [vx, vy, vz] = v;
  const tx = 2 * (q.y * vz - q.z * vy);
  const ty = 2 * (q.z * vx - q.x * vz);
  const tz = 2 * (q.x * vy - q.y * vx);
  return [
    vx + q.w * tx + (q.y * tz - q.z * ty),
    vy + q.w * ty + (q.z * tx - q.x * tz),
    vz + q.w * tz + (q.x * ty - q.y * tx),
  ];
};

describe('first-party linear algebra invariants', () => {
  it('computes vector angles from the scalar definition, including zero vectors', () => {
    const pairs = [
      [[0, 1, 0], [0.2, 0.8, 0.4]],
      [[0, 0, 1], [-0.4, 0.1, 0.2]],
      [[1, 0, 0], [-1, 0, 0]],
      [[0, 0, 0], [0, 1, 0]],
    ] as const;
    for (const [a, b] of pairs) {
      const va = new HgVec3(...a);
      const vb = new HgVec3(...b);
      const denominator = Math.sqrt(va.lengthSq() * vb.lengthSq());
      const expected = denominator === 0
        ? Math.PI / 2
        : Math.acos(Math.max(-1, Math.min(1, va.dot(vb) / denominator)));
      expect(Math.abs(va.angleTo(vb) - expected)).toBeLessThan(EPS);
    }
  });

  it('matches the closed-form XYZ and XZY Euler quaternion equations', () => {
    for (const [x, y, z] of ANGLES) {
      closeArray(new HgQuat().setFromEulerXYZ(x, y, z).toArray(), manualEulerXYZ(x, y, z));
      closeArray(new HgQuat().setFromEulerXZY(x, y, z).toArray(), manualEulerXZY(x, y, z));
    }
  });

  it('preserves Hamilton multiply and premultiply when the output aliases an input', () => {
    const a = new HgQuat().setFromEulerXZY(0.3, -0.2, 0.4);
    const b = new HgQuat().setFromEulerXZY(-0.5, 0.15, -0.1);
    closeArray(
      a.clone().multiply(b).toArray(),
      manualHamilton(a.toArray(), b.toArray()),
    );
    closeArray(
      b.clone().premultiply(a).toArray(),
      manualHamilton(a.toArray(), b.toArray()),
    );
  });

  it('rotates vectors according to the quaternion-vector identity', () => {
    const vectors = [
      [1, 0, 0],
      [0, 1, 0],
      [0.3, -0.8, 1.1],
      [-2, 0.25, 0.4],
    ] as const;
    for (const [x, y, z] of ANGLES) {
      const q = new HgQuat().setFromEulerXZY(x, y, z);
      for (const vector of vectors) {
        closeArray(
          new HgVec3(...vector).applyQuaternion(q).toArray(),
          rotateVector(q, vector),
        );
      }
    }
  });

  it('composes affine transforms from the explicit quaternion matrix formula', () => {
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
      const q = new HgQuat().setFromEulerXZY(x, y, z);
      for (const position of positions) {
        for (const scale of scales) {
          closeArray(
            new HgMat4().compose(
              new HgVec3(...position),
              q,
              new HgVec3(...scale),
            ).elements,
            manualCompose(position, q.toArray() as [number, number, number, number], scale),
          );
        }
      }
    }
  });

  it('multiplies matrices independently and inverts back to identity', () => {
    const a = new HgMat4().compose(
      new HgVec3(0.4, 1.3, -0.5),
      new HgQuat().setFromEulerXZY(0.2, -0.4, 0.6),
      new HgVec3(1, 1, 1),
    );
    const b = new HgMat4().compose(
      new HgVec3(-0.2, 0.8, 0.9),
      new HgQuat().setFromEulerXZY(-0.3, 0.1, -0.2),
      new HgVec3(1, 1, 1),
    );
    closeArray(
      new HgMat4().multiplyMatrices(a, b).elements,
      manualMultiply(a.elements, b.elements),
    );
    closeArray(a.clone().multiply(b).elements, manualMultiply(a.elements, b.elements));
    closeArray(b.clone().premultiply(a).elements, manualMultiply(a.elements, b.elements));
    closeArray(a.clone().multiply(a.clone().invert()).elements, IDENTITY, 1e-10);
  });

  it('constructs orthonormal bone-frame bases', () => {
    const directions = [
      [0, 1, 0],
      [0.2, -0.95, 0.1],
      [-0.8, 0.2, 0.4],
      [0.01, 0.02, 1],
    ] as const;
    const forward = new HgVec3(0, 0, 1);
    const up = new HgVec3(0, 1, 0);
    for (const direction of directions) {
      const y = new HgVec3(...direction).normalize();
      const reference = Math.abs(y.dot(forward)) > 0.985 ? up : forward;
      const z = reference.clone().addScaledVector(y, -y.dot(reference)).normalize();
      const x = new HgVec3().crossVectors(y, z).normalize();
      const matrix = new HgMat4().makeBasis(x, y, z);
      const q = new HgQuat().setFromRotationMatrix(matrix);
      expect(Math.abs(Math.hypot(q.x, q.y, q.z, q.w) - 1)).toBeLessThan(EPS);
      const reconstructed = new HgMat4().compose(new HgVec3(), q, new HgVec3(1, 1, 1));
      closeArray(reconstructed.elements.slice(0, 12), matrix.elements.slice(0, 12), 1e-10);
    }
  });

  it('creates shortest-arc unit-vector rotations, including opposite directions', () => {
    const pairs = [
      [[0, 0, 1], [0.2, 0.8, 0.4]],
      [[1, 0, 0], [-1, 0, 0]],
      [[0, 1, 0], [0, -1, 0]],
      [[0.3, -0.4, 0.5], [-0.2, 0.9, 0.1]],
    ] as const;
    for (const [fromRaw, toRaw] of pairs) {
      const from = new HgVec3(...fromRaw).normalize();
      const to = new HgVec3(...toRaw).normalize();
      const q = new HgQuat().setFromUnitVectors(from, to);
      const rotated = from.clone().applyQuaternion(q);
      expect(rotated.distanceTo(to)).toBeLessThan(1e-10);
      expect(Math.abs(Math.hypot(q.x, q.y, q.z, q.w) - 1)).toBeLessThan(EPS);
    }
  });

  it('extracts translation/rotation and decomposes affine transforms losslessly', () => {
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
      const matrix = new HgMat4().compose(
        new HgVec3(...entry.position),
        new HgQuat().setFromEulerXZY(...entry.rotation),
        new HgVec3(...entry.scale),
      );
      closeArray(
        new HgMat4().makeTranslation(...entry.position).elements,
        [
          1, 0, 0, 0,
          0, 1, 0, 0,
          0, 0, 1, 0,
          ...entry.position, 1,
        ],
      );

      const rotation = new HgMat4().extractRotation(matrix);
      const rotationColumns = [
        new HgVec3(rotation.elements[0], rotation.elements[1], rotation.elements[2]),
        new HgVec3(rotation.elements[4], rotation.elements[5], rotation.elements[6]),
        new HgVec3(rotation.elements[8], rotation.elements[9], rotation.elements[10]),
      ];
      rotationColumns.forEach((column) =>
        expect(Math.abs(column.length() - 1)).toBeLessThan(EPS));
      expect(Math.abs(rotationColumns[0].dot(rotationColumns[1]))).toBeLessThan(EPS);
      expect(Math.abs(rotationColumns[0].dot(rotationColumns[2]))).toBeLessThan(EPS);
      expect(Math.abs(rotationColumns[1].dot(rotationColumns[2]))).toBeLessThan(EPS);

      const p = new HgVec3(), q = new HgQuat(), s = new HgVec3();
      matrix.clone().decompose(p, q, s);
      expect(p.distanceTo(new HgVec3(...entry.position))).toBeLessThan(EPS);
      closeArray(s.toArray(), entry.scale);
      closeArray(new HgMat4().compose(p, q, s).elements, matrix.elements, 1e-10);
    }
  });

  it('round-trips vectors, quaternions and matrices through plain arrays', () => {
    const v = new HgVec3(0.2, -0.3, 1.4);
    const q = new HgQuat().setFromEulerXZY(0.2, 0.1, -0.4);
    const m = new HgMat4().compose(v, q, new HgVec3(1.1, 0.9, 1.2));
    expect(v.toArray()).toEqual([0.2, -0.3, 1.4]);
    expect(q.toArray()).toHaveLength(4);
    closeArray(new HgMat4().fromArray(m.toArray()).elements, m.elements);
  });

  it('implements vector distance/set-length and quaternion angle directly', () => {
    const a = new HgVec3(0.3, -0.4, 0.5);
    const b = new HgVec3(-0.2, 0.1, 0.9);
    expect(a.distanceToSquared(b)).toBeCloseTo(
      (0.3 + 0.2) ** 2 + (-0.4 - 0.1) ** 2 + (0.5 - 0.9) ** 2,
      14,
    );
    expect(Math.abs(a.clone().setLength(0.25).length() - 0.25)).toBeLessThan(EPS);
    closeArray(new HgVec3().setScalar(0.37).toArray(), [0.37, 0.37, 0.37]);

    const qa = new HgQuat().setFromEulerXYZ(0.2, -0.4, 0.1);
    const qb = new HgQuat().setFromEulerXYZ(-0.3, 0.15, 0.5);
    const expectedAngle = 2 * Math.acos(Math.min(1, Math.abs(qa.dot(qb))));
    expect(Math.abs(qa.angleTo(qb) - expectedAngle)).toBeLessThan(EPS);
  });

  it('round-trips XZY Euler rotations, including near gimbal lock', () => {
    const cases = [
      ...ANGLES,
      [0.3, -0.2, Math.PI / 2 - 1e-8],
      [-0.5, 0.4, -Math.PI / 2 + 1e-8],
    ] as const;
    for (const angles of cases) {
      const original = new HgQuat().setFromEulerXZY(...angles).normalize();
      const recovered = original.toEulerXZY();
      const rebuilt = new HgQuat().setFromEulerXZY(
        recovered.x,
        recovered.y,
        recovered.z,
      ).normalize();
      expect(Math.abs(1 - quaternionAgreement(original, rebuilt))).toBeLessThan(1e-10);
    }
  });
});
