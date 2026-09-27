/**
 * Home Gym PT first-party linear algebra.
 *
 * Deliberately has no third-party imports. It is initially kept beside the live
 * Three.js implementation so parity can be proved before any biomechanics path
 * is switched over.
 *
 * Matrices are 4x4 column-major, matching WebGL memory layout.
 */

export class HgVec3 {
  constructor(public x = 0, public y = 0, public z = 0) {}

  set(x: number, y: number, z: number): this {
    this.x = x; this.y = y; this.z = z; return this;
  }

  copy(v: HgVec3): this {
    return this.set(v.x, v.y, v.z);
  }

  clone(): HgVec3 {
    return new HgVec3(this.x, this.y, this.z);
  }

  add(v: HgVec3): this {
    this.x += v.x; this.y += v.y; this.z += v.z; return this;
  }

  sub(v: HgVec3): this {
    this.x -= v.x; this.y -= v.y; this.z -= v.z; return this;
  }

  subVectors(a: HgVec3, b: HgVec3): this {
    return this.set(a.x - b.x, a.y - b.y, a.z - b.z);
  }

  addScaledVector(v: HgVec3, scale: number): this {
    this.x += v.x * scale;
    this.y += v.y * scale;
    this.z += v.z * scale;
    return this;
  }

  multiplyScalar(scale: number): this {
    this.x *= scale; this.y *= scale; this.z *= scale; return this;
  }

  dot(v: HgVec3): number {
    return this.x * v.x + this.y * v.y + this.z * v.z;
  }

  cross(v: HgVec3): this {
    return this.crossVectors(this.clone(), v);
  }

  crossVectors(a: HgVec3, b: HgVec3): this {
    const ax = a.x, ay = a.y, az = a.z;
    const bx = b.x, by = b.y, bz = b.z;
    return this.set(
      ay * bz - az * by,
      az * bx - ax * bz,
      ax * by - ay * bx,
    );
  }

  lengthSq(): number {
    return this.dot(this);
  }

  length(): number {
    return Math.sqrt(this.lengthSq());
  }

  normalize(): this {
    const length = this.length();
    return length > 0 ? this.multiplyScalar(1 / length) : this.set(0, 0, 0);
  }

  distanceTo(v: HgVec3): number {
    return Math.hypot(this.x - v.x, this.y - v.y, this.z - v.z);
  }

  lerp(v: HgVec3, t: number): this {
    this.x += (v.x - this.x) * t;
    this.y += (v.y - this.y) * t;
    this.z += (v.z - this.z) * t;
    return this;
  }

  applyQuaternion(q: HgQuat): this {
    const vx = this.x, vy = this.y, vz = this.z;
    const tx = 2 * (q.y * vz - q.z * vy);
    const ty = 2 * (q.z * vx - q.x * vz);
    const tz = 2 * (q.x * vy - q.y * vx);
    this.x = vx + q.w * tx + (q.y * tz - q.z * ty);
    this.y = vy + q.w * ty + (q.z * tx - q.x * tz);
    this.z = vz + q.w * tz + (q.x * ty - q.y * tx);
    return this;
  }

  applyMatrix4(matrix: HgMat4): this {
    const e = matrix.elements;
    const x = this.x, y = this.y, z = this.z;
    const wDenominator = e[3] * x + e[7] * y + e[11] * z + e[15];
    const w = wDenominator === 0 ? 1 : 1 / wDenominator;
    this.x = (e[0] * x + e[4] * y + e[8] * z + e[12]) * w;
    this.y = (e[1] * x + e[5] * y + e[9] * z + e[13]) * w;
    this.z = (e[2] * x + e[6] * y + e[10] * z + e[14]) * w;
    return this;
  }

  setFromMatrixPosition(matrix: HgMat4): this {
    const e = matrix.elements;
    return this.set(e[12], e[13], e[14]);
  }
}

export class HgQuat {
  constructor(public x = 0, public y = 0, public z = 0, public w = 1) {}

  set(x: number, y: number, z: number, w: number): this {
    this.x = x; this.y = y; this.z = z; this.w = w; return this;
  }

  identity(): this {
    return this.set(0, 0, 0, 1);
  }

  copy(q: HgQuat): this {
    return this.set(q.x, q.y, q.z, q.w);
  }

  clone(): HgQuat {
    return new HgQuat(this.x, this.y, this.z, this.w);
  }

  dot(q: HgQuat): number {
    return this.x * q.x + this.y * q.y + this.z * q.z + this.w * q.w;
  }

  normalize(): this {
    const length = Math.hypot(this.x, this.y, this.z, this.w);
    return length > 0
      ? this.set(this.x / length, this.y / length, this.z / length, this.w / length)
      : this.identity();
  }

  conjugate(): this {
    this.x = -this.x; this.y = -this.y; this.z = -this.z; return this;
  }

  invert(): this {
    const normSq = this.dot(this);
    if (normSq <= 1e-30) return this.identity();
    this.conjugate();
    this.x /= normSq; this.y /= normSq; this.z /= normSq; this.w /= normSq;
    return this;
  }

  multiply(q: HgQuat): this {
    return this.multiplyQuaternions(this.clone(), q);
  }

  premultiply(q: HgQuat): this {
    return this.multiplyQuaternions(q, this.clone());
  }

  multiplyQuaternions(a: HgQuat, b: HgQuat): this {
    const ax = a.x, ay = a.y, az = a.z, aw = a.w;
    const bx = b.x, by = b.y, bz = b.z, bw = b.w;
    return this.set(
      aw * bx + ax * bw + ay * bz - az * by,
      aw * by - ax * bz + ay * bw + az * bx,
      aw * bz + ax * by - ay * bx + az * bw,
      aw * bw - ax * bx - ay * by - az * bz,
    );
  }

  setFromAxisAngle(axis: HgVec3, angle: number): this {
    const unit = axis.clone().normalize();
    const half = angle / 2;
    const s = Math.sin(half);
    return this.set(unit.x * s, unit.y * s, unit.z * s, Math.cos(half));
  }

  /** Project-wide Euler order XZY. Angles are radians. */
  setFromEulerXZY(x: number, y: number, z: number): this {
    const c1 = Math.cos(x / 2), c2 = Math.cos(y / 2), c3 = Math.cos(z / 2);
    const s1 = Math.sin(x / 2), s2 = Math.sin(y / 2), s3 = Math.sin(z / 2);
    return this.set(
      s1 * c2 * c3 - c1 * s2 * s3,
      c1 * s2 * c3 - s1 * c2 * s3,
      c1 * c2 * s3 + s1 * s2 * c3,
      c1 * c2 * c3 + s1 * s2 * s3,
    ).normalize();
  }

  setFromRotationMatrix(matrix: HgMat4): this {
    const e = matrix.elements;
    const m11 = e[0], m12 = e[4], m13 = e[8];
    const m21 = e[1], m22 = e[5], m23 = e[9];
    const m31 = e[2], m32 = e[6], m33 = e[10];
    const trace = m11 + m22 + m33;

    if (trace > 0) {
      const s = 2 * Math.sqrt(trace + 1);
      return this.set(
        (m32 - m23) / s,
        (m13 - m31) / s,
        (m21 - m12) / s,
        s / 4,
      ).normalize();
    }

    if (m11 >= m22 && m11 >= m33) {
      const s = 2 * Math.sqrt(Math.max(0, 1 + m11 - m22 - m33));
      return this.set(
        s / 4,
        (m12 + m21) / s,
        (m13 + m31) / s,
        (m32 - m23) / s,
      ).normalize();
    }

    if (m22 >= m33) {
      const s = 2 * Math.sqrt(Math.max(0, 1 + m22 - m11 - m33));
      return this.set(
        (m12 + m21) / s,
        s / 4,
        (m23 + m32) / s,
        (m13 - m31) / s,
      ).normalize();
    }

    const s = 2 * Math.sqrt(Math.max(0, 1 + m33 - m11 - m22));
    return this.set(
      (m13 + m31) / s,
      (m23 + m32) / s,
      s / 4,
      (m21 - m12) / s,
    ).normalize();
  }

  slerp(target: HgQuat, t: number): this {
    if (t <= 0) return this;
    if (t >= 1) return this.copy(target);

    let bx = target.x, by = target.y, bz = target.z, bw = target.w;
    let cos = this.x * bx + this.y * by + this.z * bz + this.w * bw;
    if (cos < 0) {
      cos = -cos;
      bx = -bx; by = -by; bz = -bz; bw = -bw;
    }

    if (cos > 0.9995) {
      this.x += (bx - this.x) * t;
      this.y += (by - this.y) * t;
      this.z += (bz - this.z) * t;
      this.w += (bw - this.w) * t;
      return this.normalize();
    }

    const theta = Math.acos(Math.max(-1, Math.min(1, cos)));
    const sinTheta = Math.sin(theta);
    const a = Math.sin((1 - t) * theta) / sinTheta;
    const b = Math.sin(t * theta) / sinTheta;
    return this.set(
      this.x * a + bx * b,
      this.y * a + by * b,
      this.z * a + bz * b,
      this.w * a + bw * b,
    ).normalize();
  }
}

export class HgMat4 {
  readonly elements = new Float64Array(16);

  constructor() {
    this.identity();
  }

  identity(): this {
    const e = this.elements;
    e.fill(0);
    e[0] = e[5] = e[10] = e[15] = 1;
    return this;
  }

  copy(matrix: HgMat4): this {
    this.elements.set(matrix.elements);
    return this;
  }

  clone(): HgMat4 {
    return new HgMat4().copy(this);
  }

  makeBasis(x: HgVec3, y: HgVec3, z: HgVec3): this {
    const e = this.elements;
    e[0] = x.x; e[1] = x.y; e[2] = x.z; e[3] = 0;
    e[4] = y.x; e[5] = y.y; e[6] = y.z; e[7] = 0;
    e[8] = z.x; e[9] = z.y; e[10] = z.z; e[11] = 0;
    e[12] = 0; e[13] = 0; e[14] = 0; e[15] = 1;
    return this;
  }

  compose(position: HgVec3, q: HgQuat, scale: HgVec3): this {
    const e = this.elements;
    const x = q.x, y = q.y, z = q.z, w = q.w;
    const x2 = x + x, y2 = y + y, z2 = z + z;
    const xx = x * x2, xy = x * y2, xz = x * z2;
    const yy = y * y2, yz = y * z2, zz = z * z2;
    const wx = w * x2, wy = w * y2, wz = w * z2;
    const sx = scale.x, sy = scale.y, sz = scale.z;

    e[0] = (1 - (yy + zz)) * sx;
    e[1] = (xy + wz) * sx;
    e[2] = (xz - wy) * sx;
    e[3] = 0;

    e[4] = (xy - wz) * sy;
    e[5] = (1 - (xx + zz)) * sy;
    e[6] = (yz + wx) * sy;
    e[7] = 0;

    e[8] = (xz + wy) * sz;
    e[9] = (yz - wx) * sz;
    e[10] = (1 - (xx + yy)) * sz;
    e[11] = 0;

    e[12] = position.x;
    e[13] = position.y;
    e[14] = position.z;
    e[15] = 1;
    return this;
  }

  multiply(matrix: HgMat4): this {
    return this.multiplyMatrices(this.clone(), matrix);
  }

  premultiply(matrix: HgMat4): this {
    return this.multiplyMatrices(matrix, this.clone());
  }

  multiplyMatrices(a: HgMat4, b: HgMat4): this {
    const ae = a.elements, be = b.elements, out = this.elements;
    const result = new Float64Array(16);

    for (let column = 0; column < 4; column += 1) {
      for (let row = 0; row < 4; row += 1) {
        let sum = 0;
        for (let k = 0; k < 4; k += 1) {
          sum += ae[k * 4 + row] * be[column * 4 + k];
        }
        result[column * 4 + row] = sum;
      }
    }

    out.set(result);
    return this;
  }

  /**
   * General inverse via Gauss-Jordan elimination.
   * It is intentionally straightforward first-party code; optimise only after
   * parity and profiling prove this operation is a hot path.
   */
  invert(): this {
    const augmented = Array.from({ length: 4 }, (_, row) => {
      const values = Array.from({ length: 4 }, (_, column) => this.elements[column * 4 + row]);
      return [...values, ...Array.from({ length: 4 }, (_, column) => (row === column ? 1 : 0))];
    });

    for (let column = 0; column < 4; column += 1) {
      let pivot = column;
      for (let row = column + 1; row < 4; row += 1) {
        if (Math.abs(augmented[row][column]) > Math.abs(augmented[pivot][column])) pivot = row;
      }

      if (Math.abs(augmented[pivot][column]) < 1e-15) {
        throw new Error('Cannot invert singular matrix');
      }

      if (pivot !== column) {
        const swap = augmented[column];
        augmented[column] = augmented[pivot];
        augmented[pivot] = swap;
      }

      const divisor = augmented[column][column];
      for (let c = 0; c < 8; c += 1) augmented[column][c] /= divisor;

      for (let row = 0; row < 4; row += 1) {
        if (row === column) continue;
        const factor = augmented[row][column];
        if (factor === 0) continue;
        for (let c = 0; c < 8; c += 1) {
          augmented[row][c] -= factor * augmented[column][c];
        }
      }
    }

    for (let row = 0; row < 4; row += 1) {
      for (let column = 0; column < 4; column += 1) {
        this.elements[column * 4 + row] = augmented[row][column + 4];
      }
    }
    return this;
  }
}

export const HG_UNIT_SCALE = new HgVec3(1, 1, 1);
