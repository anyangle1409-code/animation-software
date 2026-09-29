import { HgMat4, HgQuat, HgVec3 } from './linearMath';

export class HgEuler {
  constructor(
    public x = 0,
    public y = 0,
    public z = 0,
    public order: 'XYZ' = 'XYZ',
    private readonly changed: () => void = () => {},
  ) {}

  set(x: number, y: number, z: number, order: 'XYZ' = this.order): this {
    this.x = x;
    this.y = y;
    this.z = z;
    this.order = order;
    this.changed();
    return this;
  }
}

let nextSceneNodeId = 1;

/**
 * First-party scene-graph node.
 *
 * This intentionally mirrors only the object-transform/hierarchy contract the
 * Home Gym PT runtime needs. Rendering, geometry and materials are separate.
 */
export class HgObject3D {
  readonly id = nextSceneNodeId++;
  name = '';
  readonly type: string = 'Object3D';
  parent: HgObject3D | null = null;
  readonly children: HgObject3D[] = [];
  readonly position = new HgVec3();
  readonly quaternion = new HgQuat();
  readonly scale = new HgVec3(1, 1, 1);
  readonly rotation: HgEuler;
  readonly matrix = new HgMat4();
  readonly matrixWorld = new HgMat4();
  matrixAutoUpdate = true;
  matrixWorldNeedsUpdate = false;
  visible = true;
  readonly userData: Record<string, unknown> = {};

  constructor() {
    this.rotation = new HgEuler(0, 0, 0, 'XYZ', () => {
      this.quaternion.setFromEulerXYZ(
        this.rotation.x,
        this.rotation.y,
        this.rotation.z,
      );
      this.matrixWorldNeedsUpdate = true;
    });
  }

  add(...objects: HgObject3D[]): this {
    for (const object of objects) {
      if (object === this) throw new Error('A scene node cannot parent itself');
      object.parent?.remove(object);
      object.parent = this;
      this.children.push(object);
      object.matrixWorldNeedsUpdate = true;
    }
    return this;
  }

  remove(...objects: HgObject3D[]): this {
    for (const object of objects) {
      const index = this.children.indexOf(object);
      if (index < 0) continue;
      this.children.splice(index, 1);
      object.parent = null;
      object.matrixWorldNeedsUpdate = true;
    }
    return this;
  }

  clear(): this {
    for (const child of this.children) child.parent = null;
    this.children.length = 0;
    return this;
  }

  traverse(callback: (object: HgObject3D) => void): void {
    callback(this);
    for (const child of this.children) child.traverse(callback);
  }

  updateMatrix(): void {
    this.matrix.compose(this.position, this.quaternion, this.scale);
    this.matrixWorldNeedsUpdate = true;
  }

  updateMatrixWorld(force = false): void {
    if (this.matrixAutoUpdate) this.updateMatrix();
    const dirty = force || this.matrixWorldNeedsUpdate;
    if (dirty) {
      if (this.parent) this.matrixWorld.multiplyMatrices(this.parent.matrixWorld, this.matrix);
      else this.matrixWorld.copy(this.matrix);
      this.matrixWorldNeedsUpdate = false;
      force = true;
    }
    for (const child of this.children) child.updateMatrixWorld(force);
  }

  updateWorldMatrix(updateParents: boolean, updateChildren: boolean): void {
    if (updateParents && this.parent) this.parent.updateWorldMatrix(true, false);
    if (this.matrixAutoUpdate) this.updateMatrix();
    if (this.parent) this.matrixWorld.multiplyMatrices(this.parent.matrixWorld, this.matrix);
    else this.matrixWorld.copy(this.matrix);
    this.matrixWorldNeedsUpdate = false;
    if (updateChildren) {
      for (const child of this.children) child.updateWorldMatrix(false, true);
    }
  }

  localToWorld(vector: HgVec3): HgVec3 {
    this.updateWorldMatrix(true, false);
    return vector.applyMatrix4(this.matrixWorld);
  }

  worldToLocal(vector: HgVec3): HgVec3 {
    this.updateWorldMatrix(true, false);
    return vector.applyMatrix4(this.matrixWorld.clone().invert());
  }

  lookAt(x: number, y: number, z: number): void {
    const target = new HgVec3(x, y, z);
    const worldPosition = new HgVec3().setFromMatrixPosition(this.matrixWorld);
    if (!this.parent) worldPosition.copy(this.position);

    const zAxis = worldPosition.clone().sub(target);
    if (zAxis.lengthSq() < 1e-12) zAxis.z = 1;
    zAxis.normalize();

    const up = new HgVec3(0, 1, 0);
    const xAxis = new HgVec3().crossVectors(up, zAxis);
    if (xAxis.lengthSq() < 1e-12) {
      zAxis.x += 1e-6;
      zAxis.normalize();
      xAxis.crossVectors(up, zAxis);
    }
    xAxis.normalize();
    const yAxis = new HgVec3().crossVectors(zAxis, xAxis);

    const rotation = new HgMat4();
    const e = rotation.elements;
    e[0] = xAxis.x; e[1] = xAxis.y; e[2] = xAxis.z; e[3] = 0;
    e[4] = yAxis.x; e[5] = yAxis.y; e[6] = yAxis.z; e[7] = 0;
    e[8] = zAxis.x; e[9] = zAxis.y; e[10] = zAxis.z; e[11] = 0;
    e[12] = 0; e[13] = 0; e[14] = 0; e[15] = 1;

    const worldQuaternion = new HgQuat().setFromRotationMatrix(rotation);
    if (this.parent) {
      const parentRotation = new HgQuat().setFromRotationMatrix(
        new HgMat4().extractRotation(this.parent.matrixWorld),
      );
      this.quaternion.copy(parentRotation.invert().multiply(worldQuaternion));
    } else {
      this.quaternion.copy(worldQuaternion);
    }
    this.matrixWorldNeedsUpdate = true;
  }
}

export class HgGroup extends HgObject3D {
  override readonly type = 'Group';
}

export class HgScene extends HgObject3D {
  override readonly type = 'Scene';
  background: unknown = null;
}

export class HgBone extends HgObject3D {
  override readonly type = 'Bone';
}

export class HgPerspectiveCamera extends HgObject3D {
  override readonly type = 'PerspectiveCamera';
  readonly projectionMatrix = new HgMat4();
  readonly matrixWorldInverse = new HgMat4();

  constructor(
    public fov = 50,
    public aspect = 1,
    public near = 0.1,
    public far = 2000,
  ) {
    super();
    this.updateProjectionMatrix();
  }

  updateProjectionMatrix(): void {
    const top = this.near * Math.tan((Math.PI / 180) * 0.5 * this.fov);
    const height = 2 * top;
    const width = this.aspect * height;
    const left = -0.5 * width;
    const right = left + width;
    const bottom = top - height;

    const x = 2 * this.near / (right - left);
    const y = 2 * this.near / (top - bottom);
    const a = (right + left) / (right - left);
    const b = (top + bottom) / (top - bottom);
    const c = -(this.far + this.near) / (this.far - this.near);
    const d = -2 * this.far * this.near / (this.far - this.near);
    const e = this.projectionMatrix.elements;
    e[0] = x; e[4] = 0; e[8] = a; e[12] = 0;
    e[1] = 0; e[5] = y; e[9] = b; e[13] = 0;
    e[2] = 0; e[6] = 0; e[10] = c; e[14] = d;
    e[3] = 0; e[7] = 0; e[11] = -1; e[15] = 0;
  }

  override updateMatrixWorld(force = false): void {
    super.updateMatrixWorld(force);
    this.matrixWorldInverse.copy(this.matrixWorld).invert();
  }

  override updateWorldMatrix(updateParents: boolean, updateChildren: boolean): void {
    super.updateWorldMatrix(updateParents, updateChildren);
    this.matrixWorldInverse.copy(this.matrixWorld).invert();
  }
}
