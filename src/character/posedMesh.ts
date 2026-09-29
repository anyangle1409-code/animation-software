import type { CharacterSkinnedMesh } from './bones';
import { HgVec3 } from '../core/linearMath';
import {
  posedLocalVertex as firstPartyPosedLocalVertex,
  skinnedBindLocalVertex,
} from './skinningMath';

interface PointTarget<T> {
  set(x: number, y: number, z: number): T;
}

/**
 * Where a vertex of a posed skinned mesh actually is, in world space.
 *
 * Morphing and skinning are first-party. The generic output keeps older tests
 * and diagnostics free to pass their own vector object without making the
 * production character layer construct renderer vectors.
 */
export function posedVertex<T extends PointTarget<T>>(
  mesh: CharacterSkinnedMesh,
  index: number,
  out: T,
): T {
  const point = posedVertexPoint(mesh, index, posedWorldScratch);
  return out.set(point.x, point.y, point.z);
}

const posedWorldScratch = new HgVec3();

/** Current morphed + skinned vertex in world space. */
export function posedVertexPoint(
  mesh: CharacterSkinnedMesh,
  index: number,
  out: HgVec3,
): HgVec3 {
  return firstPartyPosedLocalVertex(mesh, index, out).applyMatrix4(mesh.matrixWorld);
}

/** Skin one bind-position vertex into world space without applying morphs. */
export function skinnedBindVertexPoint(
  mesh: CharacterSkinnedMesh,
  index: number,
  out: HgVec3,
): HgVec3 {
  return skinnedBindLocalVertex(mesh, index, out).applyMatrix4(mesh.matrixWorld);
}

/** Current morphed + skinned vertex in mesh-local space. */
export function posedLocalVertexPoint(
  mesh: CharacterSkinnedMesh,
  index: number,
  out: HgVec3,
): HgVec3 {
  return firstPartyPosedLocalVertex(mesh, index, out);
}

/**
 * The bone with the largest share of a vertex, as a plain name.
 *
 * Imported rigs prefix their deform bones (`DEF-upper_arm.L`), so the prefix is
 * stripped and callers can match one pattern against both the canonical rig and
 * an import. This is a label for grouping and reporting — "which part of the
 * body is this" — not a claim that the vertex belongs to one bone; at a joint it
 * is blended across several by design.
 */
export function dominantBone(mesh: CharacterSkinnedMesh, index: number): string {
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  let best = -1;
  let name = '';
  for (let lane = 0; lane < 4; lane += 1) {
    const weight = skinWeight.getComponent(index, lane);
    if (weight > best) {
      best = weight;
      name = mesh.skeleton.bones[skinIndex.getComponent(index, lane)]?.name ?? '';
    }
  }
  return name.replace(/^DEF-?/, '');
}
