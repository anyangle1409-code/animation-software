import { MeshStandardMaterial, SkinnedMesh } from 'three';
import type { Bone, BufferGeometry, Material, Skeleton as ThreeSkeleton } from 'three';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { buildCanonicalBones } from '../character/bones';
import { buildBodyGeometry, BODY_MATERIAL } from './mesh';

export interface BuiltRig {
  root: Bone;
  bones: Bone[];
  boneByName: Map<BoneName, Bone>;
  mesh: SkinnedMesh;
  skeleton: ThreeSkeleton;
}

export const MANNEQUIN_NAME = 'HGPT_Mannequin';

/**
 * A different surface on the same bones — the anatomy view swaps both, and
 * nothing else does. Omitting them gives the character the exporter writes.
 */
export interface SkinnedRigOptions {
  geometry?: BufferGeometry;
  material?: Material;
}

/**
 * Build the built-in character: the canonical bone hierarchy with one skinned
 * body bound to it.
 *
 * The general path is `characterSource(id).build(rig)` in `src/character`,
 * which is what the studio and the exporter use. This remains as the direct
 * route to the built-in surface for tests and tools that want it without the
 * registry.
 */
export function buildSkinnedRig(
  rig: Skeleton = canonicalSkeleton,
  options: SkinnedRigOptions = {},
): BuiltRig {
  const { root, bones, boneByName, skeleton } = buildCanonicalBones(rig);

  const geometry = options.geometry ?? buildBodyGeometry(rig).geometry;
  const material = options.material ?? new MeshStandardMaterial({ ...BODY_MATERIAL });
  const mesh = new SkinnedMesh(geometry, material);
  mesh.name = MANNEQUIN_NAME;
  mesh.castShadow = true;
  mesh.receiveShadow = true;

  mesh.add(root);
  mesh.bind(skeleton);

  return { root, bones, boneByName, mesh, skeleton };
}
