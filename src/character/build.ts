import { SkinnedMesh } from 'three';
import type { BufferGeometry, Material } from 'three';
import type { Skeleton } from '../rig/skeleton';
import { buildCanonicalBones } from './bones';
import type { CharacterBuild, CharacterCapabilities, DeformationStack } from './types';

export interface Surface {
  geometry: BufferGeometry;
  material: Material;
  name: string;
}

export interface AssembleOptions {
  source: string;
  rig: Skeleton;
  surfaces: Surface[];
  capabilities: CharacterCapabilities;
  /** Built after the meshes exist, because a stack works on their geometry. */
  deformation?: (meshes: SkinnedMesh[]) => DeformationStack | null;
}

/**
 * Bind one or more surfaces to a fresh canonical bone hierarchy.
 *
 * This is the single place a character becomes a scene object, so the studio
 * and the exporter cannot drift apart: both call a source's `build`, and every
 * source ends here.
 */
export function assembleCharacter(options: AssembleOptions): CharacterBuild {
  const { root, bones, boneByName, skeleton } = buildCanonicalBones(options.rig);
  // Poses are written straight into `bone.matrix` each frame, so three must not
  // recompose them from position/quaternion behind our back.
  for (const bone of bones) bone.matrixAutoUpdate = false;

  const meshes = options.surfaces.map((surface) => {
    const mesh = new SkinnedMesh(surface.geometry, surface.material);
    mesh.name = surface.name;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    return mesh;
  });
  if (meshes.length === 0) throw new Error(`Character "${options.source}" produced no surface.`);

  // The bones hang off the first mesh, which is what the GLB exporter expects
  // to find when it writes the skin.
  meshes[0].add(root);
  for (const mesh of meshes) mesh.bind(skeleton);
  for (let index = 1; index < meshes.length; index += 1) meshes[0].add(meshes[index]);

  return {
    source: options.source,
    root,
    bones,
    boneByName,
    skeleton,
    object: meshes[0],
    meshes,
    deformation: options.deformation?.(meshes) ?? null,
    capabilities: options.capabilities,
    dispose() {
      for (const mesh of meshes) {
        mesh.geometry.dispose();
        const material = mesh.material;
        if (Array.isArray(material)) material.forEach((entry) => entry.dispose());
        else material.dispose();
      }
    },
  };
}
