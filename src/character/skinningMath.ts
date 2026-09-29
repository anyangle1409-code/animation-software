import { HgMat4, HgVec3 } from '../core/linearMath';

export interface HgAttributeLike {
  readonly count: number;
  getX(index: number): number;
  getY(index: number): number;
  getZ(index: number): number;
  getW?(index: number): number;
  getComponent?(index: number, component: number): number;
}

export interface HgGeometryLike {
  getAttribute(name: string): HgAttributeLike | undefined;
  readonly morphAttributes?: {
    readonly position?: readonly HgAttributeLike[];
  };
  readonly morphTargetsRelative?: boolean;
}

export interface HgMatrixLike {
  readonly elements: ArrayLike<number>;
}

export interface HgDeformableMeshLike {
  readonly geometry: HgGeometryLike;
  readonly matrixWorld: HgMatrixLike;
  readonly isSkinnedMesh?: boolean;
  readonly skeleton?: {
    readonly bones: readonly { readonly matrixWorld: HgMatrixLike }[];
    readonly boneInverses: readonly HgMatrixLike[];
  };
  readonly bindMatrix?: HgMatrixLike;
  readonly bindMatrixInverse?: HgMatrixLike;
  readonly morphTargetInfluences?: readonly number[] | null;
}

const component = (
  attribute: HgAttributeLike,
  index: number,
  slot: number,
): number => {
  if (attribute.getComponent) return attribute.getComponent(index, slot);
  switch (slot) {
    case 0: return attribute.getX(index);
    case 1: return attribute.getY(index);
    case 2: return attribute.getZ(index);
    case 3: return attribute.getW?.(index) ?? 0;
    default: return 0;
  }
};

export function morphedLocalVertex(
  mesh: HgDeformableMeshLike,
  index: number,
  out: HgVec3,
): HgVec3 {
  const position = mesh.geometry.getAttribute('position');
  if (!position) return out.set(0, 0, 0);
  out.set(position.getX(index), position.getY(index), position.getZ(index));

  const morphs = mesh.geometry.morphAttributes?.position ?? [];
  const influences = mesh.morphTargetInfluences ?? [];
  if (!morphs.length || !influences.length) return out;

  const baseX = out.x;
  const baseY = out.y;
  const baseZ = out.z;
  for (let slot = 0; slot < morphs.length; slot += 1) {
    const influence = influences[slot] ?? 0;
    if (influence === 0) continue;
    const morph = morphs[slot];
    if (mesh.geometry.morphTargetsRelative) {
      out.x += morph.getX(index) * influence;
      out.y += morph.getY(index) * influence;
      out.z += morph.getZ(index) * influence;
    } else {
      out.x += (morph.getX(index) - baseX) * influence;
      out.y += (morph.getY(index) - baseY) * influence;
      out.z += (morph.getZ(index) - baseZ) * influence;
    }
  }
  return out;
}

const baseScratch = new HgVec3();
const transformedScratch = new HgVec3();
const boneMatrixScratch = new HgMat4();

const applySkin = (
  mesh: HgDeformableMeshLike,
  index: number,
  out: HgVec3,
): HgVec3 => {
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  const skeleton = mesh.skeleton;
  const bindMatrix = mesh.bindMatrix;
  const bindMatrixInverse = mesh.bindMatrixInverse;

  if (
    !mesh.isSkinnedMesh ||
    !skinIndex ||
    !skinWeight ||
    !skeleton ||
    !bindMatrix ||
    !bindMatrixInverse
  ) {
    return out;
  }

  baseScratch.copy(out).applyMatrix4(bindMatrix);
  out.set(0, 0, 0);

  for (let slot = 0; slot < 4; slot += 1) {
    const weight = component(skinWeight, index, slot);
    if (weight === 0) continue;

    const boneIndex = Math.round(component(skinIndex, index, slot));
    const bone = skeleton.bones[boneIndex];
    const inverse = skeleton.boneInverses[boneIndex];
    if (!bone || !inverse) continue;

    boneMatrixScratch.copy(bone.matrixWorld).multiply(inverse);
    transformedScratch.copy(baseScratch).applyMatrix4(boneMatrixScratch);
    out.addScaledVector(transformedScratch, weight);
  }

  return out.applyMatrix4(bindMatrixInverse);
};

/** Current morphed + skinned vertex in mesh-local space. */
export function posedLocalVertex(
  mesh: HgDeformableMeshLike,
  index: number,
  out: HgVec3,
): HgVec3 {
  morphedLocalVertex(mesh, index, out);
  return applySkin(mesh, index, out);
}

/** Bind-position vertex skinned by the current bone matrices, without morphs. */
export function skinnedBindLocalVertex(
  mesh: HgDeformableMeshLike,
  index: number,
  out: HgVec3,
): HgVec3 {
  const position = mesh.geometry.getAttribute('position');
  if (!position) return out.set(0, 0, 0);
  out.set(position.getX(index), position.getY(index), position.getZ(index));
  return applySkin(mesh, index, out);
}
