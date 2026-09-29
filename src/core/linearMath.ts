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

  copy(v: { x: number; y: number; z: number }): this {
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

  addScaledVector(v: { x: number; y: number; z: number }, scale: number): this {
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

  angleTo(v: HgVec3): number {
    const denominator = Math.sqrt(this.lengthSq() * v.lengthSq());
    if (denominator === 0) return Math.PI / 2;
    const cosine = this.dot(v) / denominator;
    return Math.acos(Math.max(-1, Math.min(1, cosine)));
  }

  cross(v: HgVec3): this {
    const ax = this.x, ay = this.y, az = this.z;
    const bx = v.x, by = v.y, bz = v.z;
    return this.set(
      ay * bz - az * by,
      az * bx - ax * bz,
      ax * by - ay * bx,
    );
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

  distanceTo(v: { x: number; y: number; z: number }): number {
    return Math.hypot(this.x - v.x, this.y - v.y, this.z - v.z);
  }

  distanceToSquared(v: { x: number; y: number; z: number }): number {
    const dx = this.x - v.x;
    const dy = this.y - v.y;
    const dz = this.z - v.z;
    return dx * dx + dy * dy + dz * dz;
  }

  setLength(length: number): this {
    return this.normalize().multiplyScalar(length);
  }

  lerp(v: HgVec3, t: number): this {
    this.x += (v.x - this.x) * t;
    this.y += (v.y - this.y) * t;
    this.z += (v.z - this.z) * t;
    return this;
  }

  applyQuaternion(q: { x: number; y: number; z: number; w: number }): this {
    const vx = this.x, vy = this.y, vz = this.z;
    const tx = 2 * (q.y * vz - q.z * vy);
    const ty = 2 * (q.z * vx - q.x * vz);
    const tz = 2 * (q.x * vy - q.y * vx);
    this.x = vx + q.w * tx + (q.y * tz - q.z * ty);
    this.y = vy + q.w * ty + (q.z * tx - q.x * tz);
    this.z = vz + q.w * tz + (q.x * ty - q.y * tx);
    return this;
  }

  applyMatrix4(matrix: { readonly elements: ArrayLike<number> }): this {
    const e = matrix.elements;
    const x = this.x, y = this.y, z = this.z;
    const wDenominator = e[3] * x + e[7] * y + e[11] * z + e[15];
    const w = wDenominator === 0 ? 1 : 1 / wDenominator;
    this.x = (e[0] * x + e[4] * y + e[8] * z + e[12]) * w;
    this.y = (e[1] * x + e[5] * y + e[9] * z + e[13]) * w;
    this.z = (e[2] * x + e[6] * y + e[10] * z + e[14]) * w;
    return this;
  }

  setFromMatrixPosition(matrix: { readonly elements: ArrayLike<number> }): this {
    const e = matrix.elements;
    return this.set(e[12], e[13], e[14]);
  }

  toArray(target: number[] = [], offset = 0): number[] {
    target[offset] = this.x;
    target[offset + 1] = this.y;
    target[offset + 2] = this.z;
    return target;
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

  copy(q: { x: number; y: number; z: number; w: number }): this {
    return this.set(q.x, q.y, q.z, q.w);
  }

  clone(): HgQuat {
    return new HgQuat(this.x, this.y, this.z, this.w);
  }

  dot(q: { x: number; y: number; z: number; w: number }): number {
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
    return this.multiplyQuaternions(this, q);
  }

  premultiply(q: HgQuat): this {
    return this.multiplyQuaternions(q, this);
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

  setFromAxisAngle(axis: { x: number; y: number; z: number }, angle: number): this {
    const unit = new HgVec3(axis.x, axis.y, axis.z).normalize();
    const half = angle / 2;
    const s = Math.sin(half);
    return this.set(unit.x * s, unit.y * s, unit.z * s, Math.cos(half));
  }

  /** Match Three's shortest-arc rotation between two unit directions. */
  setFromUnitVectors(
    from: { x: number; y: number; z: number },
    to: { x: number; y: number; z: number },
  ): this {
    let r = from.x * to.x + from.y * to.y + from.z * to.z + 1;
    if (r < Number.EPSILON) {
      r = 0;
      if (Math.abs(from.x) > Math.abs(from.z)) {
        this.set(-from.y, from.x, 0, r);
      } else {
        this.set(0, -from.z, from.y, r);
      }
    } else {
      this.set(
        from.y * to.z - from.z * to.y,
        from.z * to.x - from.x * to.z,
        from.x * to.y - from.y * to.x,
        r,
      );
    }
    return this.normalize();
  }

  /** Standard XYZ Euler order used by authored equipment-part transforms. Angles are radians. */
  setFromEulerXYZ(x: number, y: number, z: number): this {
    const c1 = Math.cos(x / 2), c2 = Math.cos(y / 2), c3 = Math.cos(z / 2);
    const s1 = Math.sin(x / 2), s2 = Math.sin(y / 2), s3 = Math.sin(z / 2);
    return this.set(
      s1 * c2 * c3 + c1 * s2 * s3,
      c1 * s2 * c3 - s1 * c2 * s3,
      c1 * c2 * s3 + s1 * s2 * c3,
      c1 * c2 * c3 - s1 * s2 * s3,
    );
  }

  /** Project-wide Euler order XZY. Angles are radians. */
  setFromEulerXZY(x: number, y: number, z: number): this {
    const c1 = Math.cos(x / 2), c2 = Math.cos(y / 2), c3 = Math.cos(z / 2);
    const s1 = Math.sin(x / 2), s2 = Math.sin(y / 2), s3 = Math.sin(z / 2);
    // The closed-form Euler conversion is already unit length. Three's
    // reference implementation also leaves it unnormalised; avoiding a
    // redundant hypot/sqrt here matters because FK executes this per bone.
    return this.set(
      s1 * c2 * c3 - c1 * s2 * s3,
      c1 * s2 * c3 - s1 * c2 * s3,
      c1 * c2 * s3 + s1 * s2 * c3,
      c1 * c2 * c3 + s1 * s2 * s3,
    );
  }

  /** Convert this rotation to the project-wide XZY Euler order. */
  toEulerXZY(target = new HgVec3()): HgVec3 {
    // Same rotation-matrix branch semantics as Three.Euler.setFromQuaternion
    // for XZY, including the gimbal-lock fallback.
    const x = this.x, y = this.y, z = this.z, w = this.w;
    const x2 = x + x, y2 = y + y, z2 = z + z;
    const xx = x * x2, xy = x * y2, xz = x * z2;
    const yy = y * y2, yz = y * z2, zz = z * z2;
    const wx = w * x2, wy = w * y2, wz = w * z2;

    const m11 = 1 - (yy + zz);
    const m12 = xy - wz;
    const m13 = xz + wy;
    const m22 = 1 - (xx + zz);
    const m23 = yz - wx;
    const m32 = yz + wx;
    const m33 = 1 - (xx + yy);

    const clamp = (value: number) => Math.max(-1, Math.min(1, value));
    const rz = Math.asin(-clamp(m12));
    if (Math.abs(m12) < 0.9999999) {
      return target.set(
        Math.atan2(m32, m22),
        Math.atan2(m13, m11),
        rz,
      );
    }
    return target.set(
      Math.atan2(-m23, m33),
      0,
      rz,
    );
  }

  setFromRotationMatrix(matrix: { readonly elements: ArrayLike<number> }): this {
    // Rotation matrices reaching this path are orthonormal/unit-scale. Match
    // the Three reference semantics and avoid normalising every FK bone.
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
      );
    }

    if (m11 >= m22 && m11 >= m33) {
      const s = 2 * Math.sqrt(Math.max(0, 1 + m11 - m22 - m33));
      return this.set(
        s / 4,
        (m12 + m21) / s,
        (m13 + m31) / s,
        (m32 - m23) / s,
      );
    }

    if (m22 >= m33) {
      const s = 2 * Math.sqrt(Math.max(0, 1 + m22 - m11 - m33));
      return this.set(
        (m12 + m21) / s,
        s / 4,
        (m23 + m32) / s,
        (m13 - m31) / s,
      );
    }

    const s = 2 * Math.sqrt(Math.max(0, 1 + m33 - m11 - m22));
    return this.set(
      (m13 + m31) / s,
      (m23 + m32) / s,
      s / 4,
      (m21 - m12) / s,
    );
  }

  toArray(target: number[] = [], offset = 0): number[] {
    target[offset] = this.x;
    target[offset + 1] = this.y;
    target[offset + 2] = this.z;
    target[offset + 3] = this.w;
    return target;
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

  copy(matrix: { readonly elements: ArrayLike<number> }): this {
    for (let index = 0; index < 16; index += 1) this.elements[index] = matrix.elements[index];
    return this;
  }

  fromArray(values: ArrayLike<number>, offset = 0): this {
    for (let index = 0; index < 16; index += 1) this.elements[index] = values[offset + index];
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

  makeTranslation(x: number, y: number, z: number): this {
    this.identity();
    this.elements[12] = x;
    this.elements[13] = y;
    this.elements[14] = z;
    return this;
  }

  extractRotation(matrix: { readonly elements: ArrayLike<number> }): this {
    const me = matrix.elements;
    const sx = 1 / Math.hypot(me[0], me[1], me[2]);
    const sy = 1 / Math.hypot(me[4], me[5], me[6]);
    const sz = 1 / Math.hypot(me[8], me[9], me[10]);
    const te = this.elements;
    te[0] = me[0] * sx; te[1] = me[1] * sx; te[2] = me[2] * sx; te[3] = 0;
    te[4] = me[4] * sy; te[5] = me[5] * sy; te[6] = me[6] * sy; te[7] = 0;
    te[8] = me[8] * sz; te[9] = me[9] * sz; te[10] = me[10] * sz; te[11] = 0;
    te[12] = 0; te[13] = 0; te[14] = 0; te[15] = 1;
    return this;
  }

  decompose(position: HgVec3, quaternion: HgQuat, scale: HgVec3): this {
    const te = this.elements;
    let sx = Math.hypot(te[0], te[1], te[2]);
    const sy = Math.hypot(te[4], te[5], te[6]);
    const sz = Math.hypot(te[8], te[9], te[10]);
    const determinant =
      te[0] * (te[5] * te[10] - te[6] * te[9]) -
      te[4] * (te[1] * te[10] - te[2] * te[9]) +
      te[8] * (te[1] * te[6] - te[2] * te[5]);
    if (determinant < 0) sx = -sx;

    position.set(te[12], te[13], te[14]);
    const rotation = this.clone();
    const re = rotation.elements;
    const invSx = sx === 0 ? 0 : 1 / sx;
    const invSy = sy === 0 ? 0 : 1 / sy;
    const invSz = sz === 0 ? 0 : 1 / sz;
    re[0] *= invSx; re[1] *= invSx; re[2] *= invSx;
    re[4] *= invSy; re[5] *= invSy; re[6] *= invSy;
    re[8] *= invSz; re[9] *= invSz; re[10] *= invSz;
    quaternion.setFromRotationMatrix(rotation);
    scale.set(sx, sy, sz);
    return this;
  }

  toArray(target: number[] = [], offset = 0): number[] {
    for (let index = 0; index < 16; index += 1) target[offset + index] = this.elements[index];
    return target;
  }

  multiply(matrix: { readonly elements: ArrayLike<number> }): this {
    return this.multiplyMatrices(this, matrix);
  }

  premultiply(matrix: { readonly elements: ArrayLike<number> }): this {
    return this.multiplyMatrices(matrix, this);
  }

  multiplyMatrices(
    a: { readonly elements: ArrayLike<number> },
    b: { readonly elements: ArrayLike<number> },
  ): this {
    const ae = a.elements, be = b.elements, te = this.elements;

    // Cache both inputs before writing so this method remains correct when
    // `this` aliases either operand. This is the FK hot path, so avoiding a
    // temporary Float64Array per bone is materially important.
    const a11 = ae[0], a12 = ae[4], a13 = ae[8], a14 = ae[12];
    const a21 = ae[1], a22 = ae[5], a23 = ae[9], a24 = ae[13];
    const a31 = ae[2], a32 = ae[6], a33 = ae[10], a34 = ae[14];
    const a41 = ae[3], a42 = ae[7], a43 = ae[11], a44 = ae[15];

    const b11 = be[0], b12 = be[4], b13 = be[8], b14 = be[12];
    const b21 = be[1], b22 = be[5], b23 = be[9], b24 = be[13];
    const b31 = be[2], b32 = be[6], b33 = be[10], b34 = be[14];
    const b41 = be[3], b42 = be[7], b43 = be[11], b44 = be[15];

    te[0] = a11 * b11 + a12 * b21 + a13 * b31 + a14 * b41;
    te[4] = a11 * b12 + a12 * b22 + a13 * b32 + a14 * b42;
    te[8] = a11 * b13 + a12 * b23 + a13 * b33 + a14 * b43;
    te[12] = a11 * b14 + a12 * b24 + a13 * b34 + a14 * b44;

    te[1] = a21 * b11 + a22 * b21 + a23 * b31 + a24 * b41;
    te[5] = a21 * b12 + a22 * b22 + a23 * b32 + a24 * b42;
    te[9] = a21 * b13 + a22 * b23 + a23 * b33 + a24 * b43;
    te[13] = a21 * b14 + a22 * b24 + a23 * b34 + a24 * b44;

    te[2] = a31 * b11 + a32 * b21 + a33 * b31 + a34 * b41;
    te[6] = a31 * b12 + a32 * b22 + a33 * b32 + a34 * b42;
    te[10] = a31 * b13 + a32 * b23 + a33 * b33 + a34 * b43;
    te[14] = a31 * b14 + a32 * b24 + a33 * b34 + a34 * b44;

    te[3] = a41 * b11 + a42 * b21 + a43 * b31 + a44 * b41;
    te[7] = a41 * b12 + a42 * b22 + a43 * b32 + a44 * b42;
    te[11] = a41 * b13 + a42 * b23 + a43 * b33 + a44 * b43;
    te[15] = a41 * b14 + a42 * b24 + a43 * b34 + a44 * b44;

    return this;
  }

  /**
   * Allocation-free general 4x4 inverse.
   *
   * This is the same cofactor expansion used by the Three reference path. The
   * previous Gauss-Jordan implementation was intentionally simple for parity
   * preparation, but production containment/IK calls worldToLocal thousands of
   * times and cannot afford nested arrays on every inverse.
   */
  invert(): this {
    const te = this.elements;

    const n11 = te[0], n21 = te[1], n31 = te[2], n41 = te[3];
    const n12 = te[4], n22 = te[5], n32 = te[6], n42 = te[7];
    const n13 = te[8], n23 = te[9], n33 = te[10], n43 = te[11];
    const n14 = te[12], n24 = te[13], n34 = te[14], n44 = te[15];

    const t11 =
      n23 * n34 * n42 - n24 * n33 * n42 +
      n24 * n32 * n43 - n22 * n34 * n43 -
      n23 * n32 * n44 + n22 * n33 * n44;
    const t12 =
      n14 * n33 * n42 - n13 * n34 * n42 -
      n14 * n32 * n43 + n12 * n34 * n43 +
      n13 * n32 * n44 - n12 * n33 * n44;
    const t13 =
      n13 * n24 * n42 - n14 * n23 * n42 +
      n14 * n22 * n43 - n12 * n24 * n43 -
      n13 * n22 * n44 + n12 * n23 * n44;
    const t14 =
      n14 * n23 * n32 - n13 * n24 * n32 -
      n14 * n22 * n33 + n12 * n24 * n33 +
      n13 * n22 * n34 - n12 * n23 * n34;

    const determinant = n11 * t11 + n21 * t12 + n31 * t13 + n41 * t14;
    if (Math.abs(determinant) < 1e-15) {
      throw new Error('Cannot invert singular matrix');
    }
    const detInv = 1 / determinant;

    te[0] = t11 * detInv;
    te[1] = (
      n24 * n33 * n41 - n23 * n34 * n41 -
      n24 * n31 * n43 + n21 * n34 * n43 +
      n23 * n31 * n44 - n21 * n33 * n44
    ) * detInv;
    te[2] = (
      n22 * n34 * n41 - n24 * n32 * n41 +
      n24 * n31 * n42 - n21 * n34 * n42 -
      n22 * n31 * n44 + n21 * n32 * n44
    ) * detInv;
    te[3] = (
      n23 * n32 * n41 - n22 * n33 * n41 -
      n23 * n31 * n42 + n21 * n33 * n42 +
      n22 * n31 * n43 - n21 * n32 * n43
    ) * detInv;

    te[4] = t12 * detInv;
    te[5] = (
      n13 * n34 * n41 - n14 * n33 * n41 +
      n14 * n31 * n43 - n11 * n34 * n43 -
      n13 * n31 * n44 + n11 * n33 * n44
    ) * detInv;
    te[6] = (
      n14 * n32 * n41 - n12 * n34 * n41 -
      n14 * n31 * n42 + n11 * n34 * n42 +
      n12 * n31 * n44 - n11 * n32 * n44
    ) * detInv;
    te[7] = (
      n12 * n33 * n41 - n13 * n32 * n41 +
      n13 * n31 * n42 - n11 * n33 * n42 -
      n12 * n31 * n43 + n11 * n32 * n43
    ) * detInv;

    te[8] = t13 * detInv;
    te[9] = (
      n14 * n23 * n41 - n13 * n24 * n41 -
      n14 * n21 * n43 + n11 * n24 * n43 +
      n13 * n21 * n44 - n11 * n23 * n44
    ) * detInv;
    te[10] = (
      n12 * n24 * n41 - n14 * n22 * n41 +
      n14 * n21 * n42 - n11 * n24 * n42 -
      n12 * n21 * n44 + n11 * n22 * n44
    ) * detInv;
    te[11] = (
      n13 * n22 * n41 - n12 * n23 * n41 -
      n13 * n21 * n42 + n11 * n23 * n42 +
      n12 * n21 * n43 - n11 * n22 * n43
    ) * detInv;

    te[12] = t14 * detInv;
    te[13] = (
      n13 * n24 * n31 - n14 * n23 * n31 +
      n14 * n21 * n33 - n11 * n24 * n33 -
      n13 * n21 * n34 + n11 * n23 * n34
    ) * detInv;
    te[14] = (
      n14 * n22 * n31 - n12 * n24 * n31 -
      n14 * n21 * n32 + n11 * n24 * n32 +
      n12 * n21 * n34 - n11 * n22 * n34
    ) * detInv;
    te[15] = (
      n12 * n23 * n31 - n13 * n22 * n31 +
      n13 * n21 * n32 - n11 * n23 * n32 -
      n12 * n21 * n33 + n11 * n22 * n33
    ) * detInv;

    return this;
  }
}

export const HG_UNIT_SCALE = new HgVec3(1, 1, 1);
