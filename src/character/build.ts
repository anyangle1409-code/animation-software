import type { Skeleton } from '../rig/skeleton';
import {
  buildCanonicalBones,
  createCharacterBufferAttribute,
  createCharacterBufferGeometry,
  createCharacterSkinnedMeshObject,
  createCharacterStandardMaterialObject,
  createCharacterUint16BufferAttribute,
  isCharacterStandardMaterial,
  type CharacterBufferGeometry,
  type CharacterMaterial,
  type CharacterSkinnedMesh,
  type CharacterStandardMaterial,
  type CharacterStandardMaterialParameters,
} from './bones';
import type { CharacterBuild, CharacterCapabilities, DeformationStack } from './types';

export interface Surface {
  geometry: CharacterBufferGeometry;
  material: CharacterMaterial;
  name: string;
}

export interface AssembleOptions {
  source: string;
  rig: Skeleton;
  surfaces: Surface[];
  capabilities: CharacterCapabilities;
  /** Built after the meshes exist, because a stack works on their geometry. */
  deformation?: (meshes: CharacterSkinnedMesh[]) => DeformationStack | null;
}

/**
 * Bind one or more surfaces to a fresh canonical bone hierarchy.
 *
 * This is the single place a character becomes a scene object, so the studio
 * and the exporter cannot drift apart: both call a source's `build`, and every
 * source ends here.
 */
export function createCharacterSkinnedGeometry(data: {
  positions: readonly number[];
  indices: readonly number[];
  skinIndices: readonly number[];
  skinWeights: readonly number[];
  colours: readonly number[];
}): CharacterBufferGeometry {
  const geometry = createCharacterBufferGeometry();
  geometry.setAttribute('position', createCharacterBufferAttribute(new Float32Array(data.positions), 3));
  geometry.setAttribute('skinIndex', createCharacterUint16BufferAttribute(new Uint16Array(data.skinIndices), 4));
  geometry.setAttribute('skinWeight', createCharacterBufferAttribute(new Float32Array(data.skinWeights), 4));
  geometry.setAttribute('color', createCharacterBufferAttribute(new Float32Array(data.colours), 3));
  geometry.setIndex([...data.indices]);
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return geometry;
}

export function createCharacterSkinnedMesh(
  geometry: Surface['geometry'],
  material: Surface['material'],
): CharacterSkinnedMesh {
  return createCharacterSkinnedMeshObject(geometry, material);
}

export function createCharacterStandardMaterial(
  parameters?: CharacterStandardMaterialParameters,
): CharacterStandardMaterial {
  return createCharacterStandardMaterialObject(parameters);
}

export function configureCharacterPresentation(
  build: CharacterBuild,
  colour: string,
  opacity: number,
  depthWrite: boolean,
): void {
  for (const mesh of build.meshes) {
    const material = mesh.material;
    if (!isCharacterStandardMaterial(material)) continue;
    material.color.set(colour);
    material.opacity = opacity;
    material.transparent = opacity < 1;
    material.depthWrite = depthWrite;
    material.needsUpdate = true;
  }
}

export function assembleCharacter(options: AssembleOptions): CharacterBuild {
  const { root, bones, boneByName, skeleton } = buildCanonicalBones(options.rig);
  // Poses are written straight into `bone.matrix` each frame, so three must not
  // recompose them from position/quaternion behind our back.
  for (const bone of bones) bone.matrixAutoUpdate = false;

  const meshes = options.surfaces.map((surface) => {
    const mesh = createCharacterSkinnedMeshObject(surface.geometry, surface.material);
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
