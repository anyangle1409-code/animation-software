import { HgVec3 } from '../core/linearMath';
import {
  posedLocalVertex as firstPartyPosedLocalVertex,
  skinnedBindLocalVertex,
  type HgAttributeLike,
  type HgDeformableMeshLike,
  type HgGeometryLike,
  type HgMatrixLike,
} from './skinningMath';

interface PointTarget<T> {
  set(x: number, y: number, z: number): T;
}

export interface PosedCharacterMeshLike extends HgDeformableMeshLike {
  readonly name?: string;
  readonly geometry: HgGeometryLike & {
    getAttribute(name: string): HgAttributeLike | undefined;
    getIndex(): { readonly count: number; getX(index: number): number } | null;
  };
  readonly matrixWorld: HgMatrixLike;
  readonly skeleton: {
    readonly bones: ReadonlyArray<{
      readonly name: string;
      readonly matrixWorld: HgMatrixLike;
    }>;
    readonly boneInverses: readonly HgMatrixLike[];
  };
}

/**
 * Where a vertex of a posed skinned mesh actually is, in world space.
 *
 * Morphing and skinning are first-party. The mesh contract is deliberately
 * structural so legacy Three fixtures can remain independent parity inputs
 * without making production construct renderer objects.
 */
export function posedVertex<T extends PointTarget<T>>(
  mesh: PosedCharacterMeshLike,
  index: number,
  out: T,
): T {
  const point = posedVertexPoint(mesh, index, posedWorldScratch);
  return out.set(point.x, point.y, point.z);
}

const posedWorldScratch = new HgVec3();

/** Current morphed + skinned vertex in world space. */
export function posedVertexPoint(
  mesh: PosedCharacterMeshLike,
  index: number,
  out: HgVec3,
): HgVec3 {
  return firstPartyPosedLocalVertex(mesh, index, out).applyMatrix4(mesh.matrixWorld);
}

/** Skin one bind-position vertex into world space without applying morphs. */
export function skinnedBindVertexPoint(
  mesh: PosedCharacterMeshLike,
  index: number,
  out: HgVec3,
): HgVec3 {
  return skinnedBindLocalVertex(mesh, index, out).applyMatrix4(mesh.matrixWorld);
}

/** Current morphed + skinned vertex in mesh-local space. */
export function posedLocalVertexPoint(
  mesh: PosedCharacterMeshLike,
  index: number,
  out: HgVec3,
): HgVec3 {
  return firstPartyPosedLocalVertex(mesh, index, out);
}

/** Bone carrying the largest share of one vertex, as a normalized plain name. */
export function dominantBone(mesh: PosedCharacterMeshLike, index: number): string {
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  if (!skinIndex || !skinWeight) return '';
  let best = -1;
  let name = '';
  for (let lane = 0; lane < 4; lane += 1) {
    const weight = skinWeight.getComponent?.(index, lane) ??
      [skinWeight.getX(index), skinWeight.getY(index), skinWeight.getZ(index), skinWeight.getW?.(index) ?? 0][lane];
    if (weight > best) {
      best = weight;
      const boneIndex = skinIndex.getComponent?.(index, lane) ??
        [skinIndex.getX(index), skinIndex.getY(index), skinIndex.getZ(index), skinIndex.getW?.(index) ?? 0][lane];
      name = mesh.skeleton.bones[Math.round(boneIndex)]?.name ?? '';
    }
  }
  return name.replace(/^DEF-?/, '');
}
