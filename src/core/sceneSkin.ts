import { HgMat4, HgVec3 } from './linearMath';
import { HgBone, HgObject3D } from './sceneGraph';

export type HgAttributeArray = Float32Array | Uint16Array | Uint32Array;

export class HgBufferAttribute {
  name = '';
  needsUpdate = false;
  readonly count: number;

  constructor(
    public readonly array: HgAttributeArray,
    public readonly itemSize: number,
  ) {
    if (!Number.isInteger(itemSize) || itemSize <= 0) {
      throw new Error('Buffer attribute itemSize must be a positive integer');
    }
    if (array.length % itemSize !== 0) {
      throw new Error('Buffer attribute length must be divisible by itemSize');
    }
    this.count = array.length / itemSize;
  }

  getComponent(index: number, component: number): number {
    return this.array[index * this.itemSize + component] ?? 0;
  }
  getX(index: number): number { return this.getComponent(index, 0); }
  getY(index: number): number { return this.getComponent(index, 1); }
  getZ(index: number): number { return this.getComponent(index, 2); }
  getW(index: number): number { return this.getComponent(index, 3); }

  setComponent(index: number, component: number, value: number): this {
    this.array[index * this.itemSize + component] = value;
    return this;
  }

  setXYZ(index: number, x: number, y: number, z: number): this {
    this.setComponent(index, 0, x);
    this.setComponent(index, 1, y);
    this.setComponent(index, 2, z);
    return this;
  }

  setXYZW(index: number, x: number, y: number, z: number, w: number): this {
    this.setXYZ(index, x, y, z);
    this.setComponent(index, 3, w);
    return this;
  }

  clone(): HgBufferAttribute {
    const copy = new (this.array.constructor as typeof Float32Array)(this.array) as HgAttributeArray;
    const result = new HgBufferAttribute(copy, this.itemSize);
    result.name = this.name;
    result.needsUpdate = this.needsUpdate;
    return result;
  }
}

export interface HgBoundingBox {
  min: HgVec3;
  max: HgVec3;
}

export interface HgBoundingSphere {
  center: HgVec3;
  radius: number;
}

export class HgBufferGeometry {
  readonly attributes: Record<string, HgBufferAttribute> = {};
  morphAttributes: {
    position?: HgBufferAttribute[];
    normal?: HgBufferAttribute[];
    [name: string]: HgBufferAttribute[] | undefined;
  } = {};
  morphTargetsRelative = false;
  boundingBox: HgBoundingBox | null = null;
  boundingSphere: HgBoundingSphere | null = null;
  private index: HgBufferAttribute | null = null;
  private disposed = false;

  setAttribute(name: string, attribute: HgBufferAttribute): this {
    this.attributes[name] = attribute;
    return this;
  }

  getAttribute(name: string): HgBufferAttribute | undefined {
    return this.attributes[name];
  }

  deleteAttribute(name: string): this {
    delete this.attributes[name];
    return this;
  }

  setIndex(index: HgBufferAttribute | readonly number[] | null): this {
    if (index === null) {
      this.index = null;
      return this;
    }
    if (index instanceof HgBufferAttribute) {
      this.index = index;
      return this;
    }
    const maximum = index.reduce((max, value) => Math.max(max, value), 0);
    const values = maximum <= 65535
      ? new Uint16Array(index)
      : new Uint32Array(index);
    this.index = new HgBufferAttribute(values, 1);
    return this;
  }

  getIndex(): HgBufferAttribute | null {
    return this.index;
  }

  computeVertexNormals(): void {
    const position = this.getAttribute('position');
    if (!position) return;
    const normals = new Float32Array(position.count * 3);
    const normal = new HgBufferAttribute(normals, 3);
    const a = new HgVec3();
    const b = new HgVec3();
    const c = new HgVec3();
    const ab = new HgVec3();
    const ac = new HgVec3();
    const face = new HgVec3();

    const accumulate = (ia: number, ib: number, ic: number) => {
      a.set(position.getX(ia), position.getY(ia), position.getZ(ia));
      b.set(position.getX(ib), position.getY(ib), position.getZ(ib));
      c.set(position.getX(ic), position.getY(ic), position.getZ(ic));
      ab.copy(b).sub(a);
      ac.copy(c).sub(a);
      face.crossVectors(ab, ac);
      for (const index of [ia, ib, ic]) {
        normals[index * 3] += face.x;
        normals[index * 3 + 1] += face.y;
        normals[index * 3 + 2] += face.z;
      }
    };

    if (this.index) {
      for (let offset = 0; offset + 2 < this.index.count; offset += 3) {
        accumulate(
          Math.round(this.index.getX(offset)),
          Math.round(this.index.getX(offset + 1)),
          Math.round(this.index.getX(offset + 2)),
        );
      }
    } else {
      for (let offset = 0; offset + 2 < position.count; offset += 3) {
        accumulate(offset, offset + 1, offset + 2);
      }
    }

    const value = new HgVec3();
    for (let index = 0; index < position.count; index += 1) {
      value.set(
        normals[index * 3],
        normals[index * 3 + 1],
        normals[index * 3 + 2],
      );
      if (value.lengthSq() > 1e-20) value.normalize();
      normal.setXYZ(index, value.x, value.y, value.z);
    }
    this.setAttribute('normal', normal);
  }

  computeBoundingBox(): void {
    const position = this.getAttribute('position');
    if (!position || !position.count) {
      this.boundingBox = null;
      return;
    }
    const min = new HgVec3(Infinity, Infinity, Infinity);
    const max = new HgVec3(-Infinity, -Infinity, -Infinity);
    for (let index = 0; index < position.count; index += 1) {
      const x = position.getX(index);
      const y = position.getY(index);
      const z = position.getZ(index);
      min.x = Math.min(min.x, x); min.y = Math.min(min.y, y); min.z = Math.min(min.z, z);
      max.x = Math.max(max.x, x); max.y = Math.max(max.y, y); max.z = Math.max(max.z, z);
    }
    this.boundingBox = { min, max };
  }

  computeBoundingSphere(): void {
    const position = this.getAttribute('position');
    if (!position || !position.count) {
      this.boundingSphere = null;
      return;
    }
    if (!this.boundingBox) this.computeBoundingBox();
    const box = this.boundingBox!;
    const center = box.min.clone().add(box.max).multiplyScalar(0.5);
    let radiusSq = 0;
    const point = new HgVec3();
    for (let index = 0; index < position.count; index += 1) {
      point.set(position.getX(index), position.getY(index), position.getZ(index));
      radiusSq = Math.max(radiusSq, point.distanceToSquared(center));
    }
    this.boundingSphere = { center, radius: Math.sqrt(radiusSq) };
  }

  dispose(): void {
    this.disposed = true;
  }

  get isDisposed(): boolean {
    return this.disposed;
  }
}

const hexChannel = (hex: string): number => Number.parseInt(hex, 16) / 255;

export class HgColour {
  constructor(public r = 1, public g = 1, public b = 1) {}

  set(value: string | number): this {
    if (typeof value === 'number') {
      this.r = ((value >> 16) & 255) / 255;
      this.g = ((value >> 8) & 255) / 255;
      this.b = (value & 255) / 255;
      return this;
    }
    const colour = value.trim();
    if (/^#[0-9a-f]{3}$/i.test(colour)) {
      this.r = hexChannel(colour[1] + colour[1]);
      this.g = hexChannel(colour[2] + colour[2]);
      this.b = hexChannel(colour[3] + colour[3]);
      return this;
    }
    if (/^#[0-9a-f]{6}$/i.test(colour)) {
      this.r = hexChannel(colour.slice(1, 3));
      this.g = hexChannel(colour.slice(3, 5));
      this.b = hexChannel(colour.slice(5, 7));
      return this;
    }
    throw new Error('Unsupported colour value: ' + value);
  }

  setRGB(r: number, g: number, b: number): this {
    this.r = r; this.g = g; this.b = b;
    return this;
  }

  copy(value: { r: number; g: number; b: number }): this {
    return this.setRGB(value.r, value.g, value.b);
  }
}

export interface HgStandardMaterialParameters {
  color?: string | number;
  vertexColors?: boolean;
  roughness?: number;
  metalness?: number;
  opacity?: number;
  transparent?: boolean;
  depthWrite?: boolean;
}

export class HgMaterial {
  name = '';
  opacity = 1;
  transparent = false;
  depthWrite = true;
  needsUpdate = false;
  private disposed = false;

  dispose(): void { this.disposed = true; }
  get isDisposed(): boolean { return this.disposed; }
}

export class HgStandardMaterial extends HgMaterial {
  readonly color = new HgColour(1, 1, 1);
  readonly emissive = new HgColour(0, 0, 0);
  metalness = 0;
  roughness = 1;
  vertexColors = false;
  side = 0;
  map: unknown = null;
  metalnessMap: unknown = null;
  roughnessMap: unknown = null;
  normalMap: unknown = null;
  aoMap: unknown = null;
  emissiveMap: unknown = null;
  aoMapIntensity = 1;
  readonly normalScale = {
    x: 1,
    y: 1,
    setScalar: (value: number) => {
      this.normalScale.x = value;
      this.normalScale.y = value;
      return this.normalScale;
    },
  };

  constructor(parameters: HgStandardMaterialParameters = {}) {
    super();
    if (parameters.color !== undefined) this.color.set(parameters.color);
    if (parameters.vertexColors !== undefined) this.vertexColors = parameters.vertexColors;
    if (parameters.roughness !== undefined) this.roughness = parameters.roughness;
    if (parameters.metalness !== undefined) this.metalness = parameters.metalness;
    if (parameters.opacity !== undefined) this.opacity = parameters.opacity;
    if (parameters.transparent !== undefined) this.transparent = parameters.transparent;
    if (parameters.depthWrite !== undefined) this.depthWrite = parameters.depthWrite;
  }
}

export class HgSkeleton {
  readonly boneInverses: HgMat4[];

  constructor(
    public readonly bones: HgBone[],
    inverses?: readonly { readonly elements: ArrayLike<number> }[],
  ) {
    for (const bone of bones) bone.updateWorldMatrix(true, false);
    this.boneInverses = inverses
      ? inverses.map((matrix) => new HgMat4().copy(matrix))
      : bones.map((bone) => new HgMat4().copy(bone.matrixWorld).invert());
  }

  update(): void {
    // Bone world matrices are authoritative in the first-party skinning path.
  }
}

export class HgMesh extends HgObject3D {
  override readonly type = 'Mesh';
  castShadow = false;
  receiveShadow = false;

  constructor(
    public geometry: HgBufferGeometry,
    public material: HgMaterial | HgMaterial[],
  ) {
    super();
  }
}

export class HgSkinnedMesh extends HgMesh {
  override readonly type = 'SkinnedMesh';
  readonly isSkinnedMesh = true;
  skeleton = new HgSkeleton([]);
  readonly bindMatrix = new HgMat4();
  readonly bindMatrixInverse = new HgMat4();
  morphTargetInfluences: number[] | null = null;
  morphTargetDictionary: Record<string, number> | null = null;

  bind(skeleton: HgSkeleton, bindMatrix?: { readonly elements: ArrayLike<number> }): void {
    this.skeleton = skeleton;
    this.updateWorldMatrix(true, false);
    this.bindMatrix.copy(bindMatrix ?? this.matrixWorld);
    this.bindMatrixInverse.copy(this.bindMatrix).invert();
  }

  updateMorphTargets(): void {
    const positions = this.geometry.morphAttributes.position ?? [];
    const normals = this.geometry.morphAttributes.normal ?? [];
    const count = Math.max(positions.length, normals.length);
    const previous = this.morphTargetInfluences ?? [];
    const dictionary: Record<string, number> = {};
    for (let index = 0; index < count; index += 1) {
      const name = positions[index]?.name || normals[index]?.name || String(index);
      dictionary[name] = index;
    }
    this.morphTargetDictionary = dictionary;
    this.morphTargetInfluences = Array.from(
      { length: count },
      (_, index) => previous[index] ?? 0,
    );
  }
}
