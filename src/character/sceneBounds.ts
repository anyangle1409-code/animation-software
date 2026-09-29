import { HgMat4, HgVec3 } from '../core/linearMath';

interface AttributeLike {
  readonly count: number;
  getX(index: number): number;
  getY(index: number): number;
  getZ(index: number): number;
  getW?(index: number): number;
  getComponent?(index: number, component: number): number;
}

interface GeometryLike {
  getAttribute(name: string): AttributeLike | undefined;
  readonly morphAttributes?: {
    readonly position?: readonly AttributeLike[];
  };
  readonly morphTargetsRelative?: boolean;
}

interface MatrixLike {
  readonly elements: ArrayLike<number>;
}

interface BoneLike {
  readonly matrixWorld: MatrixLike;
}

interface SkeletonLike {
  readonly bones: readonly BoneLike[];
  readonly boneInverses: readonly MatrixLike[];
}

interface SceneNodeLike {
  readonly children: readonly SceneNodeLike[];
  readonly matrixWorld: MatrixLike;
  readonly geometry?: GeometryLike;
  readonly isSkinnedMesh?: boolean;
  readonly skeleton?: SkeletonLike;
  readonly bindMatrix?: MatrixLike;
  readonly bindMatrixInverse?: MatrixLike;
  readonly morphTargetInfluences?: readonly number[] | null;
  updateMatrixWorld(force: boolean): void;
}

const component = (attribute: AttributeLike, index: number, slot: number): number => {
  if (attribute.getComponent) return attribute.getComponent(index, slot);
  switch (slot) {
    case 0: return attribute.getX(index);
    case 1: return attribute.getY(index);
    case 2: return attribute.getZ(index);
    case 3: return attribute.getW?.(index) ?? 0;
    default: return 0;
  }
};

const morphedPosition = (
  geometry: GeometryLike,
  influences: readonly number[] | null | undefined,
  index: number,
  target: HgVec3,
): HgVec3 => {
  const position = geometry.getAttribute('position');
  if (!position) return target.set(0, 0, 0);
  target.set(position.getX(index), position.getY(index), position.getZ(index));

  const morphs = geometry.morphAttributes?.position ?? [];
  if (!morphs.length || !influences?.length) return target;

  const baseX = target.x;
  const baseY = target.y;
  const baseZ = target.z;
  for (let morphIndex = 0; morphIndex < morphs.length; morphIndex += 1) {
    const influence = influences[morphIndex] ?? 0;
    if (influence === 0) continue;
    const morph = morphs[morphIndex];
    if (geometry.morphTargetsRelative) {
      target.x += morph.getX(index) * influence;
      target.y += morph.getY(index) * influence;
      target.z += morph.getZ(index) * influence;
    } else {
      target.x += (morph.getX(index) - baseX) * influence;
      target.y += (morph.getY(index) - baseY) * influence;
      target.z += (morph.getZ(index) - baseZ) * influence;
    }
  }
  return target;
};

const skinnedPosition = (
  node: SceneNodeLike,
  geometry: GeometryLike,
  index: number,
  target: HgVec3,
): HgVec3 => {
  morphedPosition(geometry, node.morphTargetInfluences, index, target);
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const skeleton = node.skeleton;
  const bindMatrix = node.bindMatrix;
  const bindMatrixInverse = node.bindMatrixInverse;
  if (!node.isSkinnedMesh || !skinIndex || !skinWeight || !skeleton || !bindMatrix || !bindMatrixInverse) {
    return target;
  }

  const base = target.clone().applyMatrix4(bindMatrix);
  target.set(0, 0, 0);
  const transformed = new HgVec3();
  const boneMatrix = new HgMat4();

  for (let slot = 0; slot < 4; slot += 1) {
    const weight = component(skinWeight, index, slot);
    if (weight === 0) continue;
    const boneIndex = Math.round(component(skinIndex, index, slot));
    const bone = skeleton.bones[boneIndex];
    const inverse = skeleton.boneInverses[boneIndex];
    if (!bone || !inverse) continue;

    boneMatrix.copy(bone.matrixWorld).multiply(inverse);
    transformed.copy(base).applyMatrix4(boneMatrix);
    target.x += transformed.x * weight;
    target.y += transformed.y * weight;
    target.z += transformed.z * weight;
  }

  return target.applyMatrix4(bindMatrixInverse);
};

const visit = (node: SceneNodeLike, callback: (node: SceneNodeLike) => void): void => {
  callback(node);
  for (const child of node.children) visit(child, callback);
};

/**
 * Measure a character scene without renderer bounds helpers.
 *
 * The routine evaluates authored morphs and skin weights from the current bone
 * world matrices, then applies the object's world transform. This keeps import
 * scaling independent of Three's Box3 implementation.
 */
export function measureSceneHeight(root: SceneNodeLike): number {
  root.updateMatrixWorld(true);

  let minimum = Infinity;
  let maximum = -Infinity;
  const point = new HgVec3();

  visit(root, (node) => {
    const geometry = node.geometry;
    const position = geometry?.getAttribute('position');
    if (!geometry || !position) return;

    for (let index = 0; index < position.count; index += 1) {
      skinnedPosition(node, geometry, index, point).applyMatrix4(node.matrixWorld);
      if (!Number.isFinite(point.y)) continue;
      minimum = Math.min(minimum, point.y);
      maximum = Math.max(maximum, point.y);
    }
  });

  if (!Number.isFinite(minimum) || !Number.isFinite(maximum)) return 0.5;
  return Math.max(0.5, maximum - minimum);
}
