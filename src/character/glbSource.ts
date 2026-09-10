import { Box3, Object3D } from 'three';
import type { Material, SkinnedMesh } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { createMapping, guessMapping, reportMapping } from '../retargeting/boneMap';
import type { BoneMapping, MappingReport } from '../retargeting/boneMap';
import { assembleCharacter } from './build';
import { rebindToCanonical } from './rebind';
import type { RebindReport } from './rebind';
import type { CharacterSource } from './types';

/**
 * A character loaded from a GLB.
 *
 * This is the route a higher-quality mesh arrives by. The file supplies the
 * geometry, the UVs and the materials — including their maps, which are kept
 * exactly as authored — and the studio supplies the skeleton: the surface is
 * rebound by bone name onto the canonical rig, so the existing animation, IK,
 * grip and equipment all drive it without a single change.
 */

export interface GlbCharacterOptions {
  id: string;
  label: string;
  note?: string;
  /** Where to fetch it from, for a bundled or hosted asset. */
  url?: string;
  /** Already-read bytes, for an imported file. */
  data?: ArrayBuffer;
  /**
   * A bone mapping to use instead of guessing — from the character panel, or
   * saved from a previous import of the same rig.
   */
  mapping?: BoneMapping;
}

export interface GlbCharacterSource extends CharacterSource {
  /** How the last build mapped and rebound the file. Null until it is built. */
  lastReport: { mapping: MappingReport; rebind: RebindReport[] } | null;
}

export function glbCharacterSource(options: GlbCharacterOptions): GlbCharacterSource {
  const source: GlbCharacterSource = {
    id: options.id,
    label: options.label,
    note: options.note,
    // A textured import has no écorché mapping — its colours are in its maps,
    // not in vertex attributes the anatomy shader can read.
    capabilities: { anatomy: false, textured: true },
    lastReport: null,

    async build(rig: Skeleton = canonicalSkeleton) {
      const scene = await loadScene(options);
      scene.updateMatrixWorld(true);

      const meshes: SkinnedMesh[] = [];
      const boneNames: string[] = [];
      scene.traverse((object) => {
        if ((object as SkinnedMesh).isSkinnedMesh) meshes.push(object as SkinnedMesh);
        if ((object as { isBone?: boolean }).isBone) boneNames.push(object.name);
      });
      if (meshes.length === 0) {
        throw new Error(
          `"${options.label}" has no skinned mesh. Export the character with its rig and skin weights included.`,
        );
      }

      const mapping = options.mapping ?? guessedMapping(options.label, scene, boneNames);
      const rebind = meshes.map((mesh) => {
        const report = rebindToCanonical(mesh, mapping, rig);
        mesh.geometry.userData.rebind = report;
        return report;
      });
      source.lastReport = { mapping: reportMapping(mapping), rebind };

      return assembleCharacter({
        source: source.id,
        rig,
        capabilities: source.capabilities,
        surfaces: meshes.map((mesh, index) => ({
          geometry: mesh.geometry,
          material: mesh.material as Material,
          name: mesh.name || `${options.id}_${index}`,
        })),
      });
    },
  };

  return source;
}

async function loadScene(options: GlbCharacterOptions): Promise<Object3D> {
  const loader = new GLTFLoader();
  if (options.data) {
    const gltf = await loader.parseAsync(options.data, '');
    return gltf.scene as Object3D;
  }
  if (options.url) {
    const gltf = await loader.loadAsync(options.url);
    return gltf.scene as Object3D;
  }
  throw new Error(`Character "${options.label}" has neither a URL nor file data to load.`);
}

function guessedMapping(label: string, scene: Object3D, boneNames: string[]): BoneMapping {
  const mapping = createMapping(label, `${label} (${boneNames.length} bones)`);
  mapping.bones = guessMapping(boneNames);
  const box = new Box3().setFromObject(scene);
  mapping.characterHeight = Math.max(0.5, box.max.y - box.min.y);
  return mapping;
}
