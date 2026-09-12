import {
  Box3,
  InterpolateLinear,
  Matrix4,
  Object3D,
  Quaternion,
  QuaternionKeyframeTrack,
  Vector3,
  VectorKeyframeTrack,
} from 'three';
import type { Bone, KeyframeTrack, SkinnedMesh } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { RIG_HEIGHT } from '../rig/humanoid';
import type { Pose } from '../rig/types';
import { createMapping, guessMapping, reportMapping } from '../retargeting/boneMap';
import type { BoneMapping, MappingReport } from '../retargeting/boneMap';
import { applyRetarget, bindRetarget, readCharacter, resetCharacter } from '../retargeting/retarget';
import type { RetargetBinding } from '../retargeting/retarget';
import { compressTrack } from '../export/tracks';
import type {
  CharacterBuild,
  CharacterSource,
  DeformationSampler,
  Side,
} from './types';

/**
 * An imported character, preserved.
 *
 * The studio's rig is a *driver*, not a skin skeleton. A character authored
 * elsewhere already has a skeleton, a bind pose and weights that somebody
 * spent real effort on, and the way to use it is to drive that skeleton —
 * not to rebuild the surface onto ours.
 *
 * So nothing here touches the mesh. The file's vertices, its bones, its
 * inverse bind matrices and its weights are exactly as authored; the only
 * change to the character is a uniform scale on its root, so a model of any
 * height stands at the rig's scale in the studio's world. Canonical joint
 * angles are transferred onto the mapped source bones each frame, through the
 * change of basis `bindRetarget` works out once.
 *
 * What that buys, compared with rebinding the surface onto the canonical
 * bones:
 *
 * - **Rest geometry survives.** Rebinding re-placed every vertex through a
 *   blend of per-bone transforms, which on a 160-bone Rigify character moved
 *   21.7% of edges by more than half their length before a single frame was
 *   played. Here the measured change is zero beyond the uniform scale.
 * - **Bones the rig does not have keep working.** Twist bones, helper bones
 *   and a whole face rig stay in the source hierarchy at their rest pose and
 *   ride their parents, which is what they were authored to do. They are not
 *   "unmapped weight" to be redistributed — they are simply not driven.
 * - **Proportions stay the model's own.** A longer forearm stays longer.
 *
 * The cost is that the character's hands are no longer where the canonical
 * rig's hands are, so anything the hands carry has to follow the character
 * rather than the rig. `handMatrix` is that: the source hand's world
 * transform, restated in the canonical hand's frame, so the same grip offsets
 * the rig uses apply unchanged.
 */

export interface RetargetedCharacterOptions {
  id: string;
  label: string;
  note?: string;
  /** Where to fetch it from, for a bundled or hosted asset. */
  url?: string;
  /** Already-read bytes, for an imported file. */
  data?: ArrayBuffer;
  /** A mapping to use instead of guessing — from the panel, or saved earlier. */
  mapping?: BoneMapping;
}

export interface ImportReport {
  mapping: MappingReport;
  /** The model's own height, metres, and the uniform scale applied to it. */
  height: number;
  scale: number;
  bones: number;
  vertices: number;
  /** Source bones the canonical rig drives. */
  driven: number;
  /** Source bones left at rest, riding their parents: twists, helpers, the face. */
  passive: number;
}

export interface RetargetedCharacterSource extends CharacterSource {
  /** How the last build read the file. Null until it is built. */
  lastReport: ImportReport | null;
}

export function retargetedCharacterSource(
  options: RetargetedCharacterOptions,
): RetargetedCharacterSource {
  const source: RetargetedCharacterSource = {
    id: options.id,
    label: options.label,
    note: options.note,
    // An imported surface carries its own colours or maps, which the écorché
    // mapping knows nothing about.
    capabilities: { anatomy: false, textured: true },
    lastReport: null,

    async build(rig: Skeleton = canonicalSkeleton) {
      const scene = await loadScene(options);
      scene.updateMatrixWorld(true);

      const character = readCharacter(scene);
      if (character.bones.size === 0) {
        throw new Error(
          `"${options.label}" has no skeleton. Export the character from Blender with its rig included.`,
        );
      }
      if (character.meshes.length === 0) {
        throw new Error(`"${options.label}" has no skinned mesh — nothing to drive.`);
      }

      const mapping = options.mapping ?? guessedMapping(options.label, scene, character.boneNames);
      const binding = bindRetarget(character, mapping, rig);

      // The one change made to the character: a uniform scale so a model of
      // any height stands at the rig's scale. `applyRetarget` already scales
      // root motion by the model's height, so the two cancel and a step is a
      // step wherever the character came from.
      const scale = RIG_HEIGHT / character.height;
      scene.scale.setScalar(scale);
      scene.position.set(0, 0, 0);
      scene.quaternion.identity();
      scene.updateMatrixWorld(true);

      const boneByName = new Map<BoneName, Bone>();
      const correction = new Map<BoneName, Quaternion>();
      for (const bound of binding.bones) {
        boneByName.set(bound.canonical, bound.bone);
        correction.set(bound.canonical, bound.correction);
      }

      const bones = [...character.bones.values()];
      const root = topmost(bones);
      const vertices = character.meshes.reduce(
        (total, mesh) => total + mesh.geometry.getAttribute('position').count,
        0,
      );

      source.lastReport = {
        mapping: reportMapping(mapping),
        height: character.height,
        scale,
        bones: bones.length,
        vertices,
        driven: binding.bones.length,
        passive: bones.length - binding.bones.length,
      };

      const scratch = {
        matrix: new Matrix4(),
        basis: new Matrix4(),
        rotation: new Quaternion(),
        position: new Vector3(),
        unit: new Vector3(1, 1, 1),
      };

      const build: CharacterBuild = {
        source: source.id,
        root,
        bones,
        boneByName,
        skeleton: character.meshes[0].skeleton,
        object: scene,
        meshes: character.meshes as SkinnedMesh[],
        deformation: null,
        capabilities: source.capabilities,

        driver: (pose: Pose) => applyRetarget(binding, pose),

        handMatrix: (side: Side, target: Matrix4) => {
          const name = (side === 'l' ? 'hand_l' : 'hand_r') as BoneName;
          const bone = boneByName.get(name);
          const change = correction.get(name);
          if (!bone || !change) return null;
          // The bone's world placement, with its own basis rotated into the
          // canonical hand's, so grip offsets written against the rig apply
          // unchanged. Scale is dropped: the dumbbell is a real dumbbell.
          scratch.matrix.copy(bone.matrixWorld);
          scratch.position.setFromMatrixPosition(scratch.matrix);
          scratch.basis.extractRotation(scratch.matrix);
          scratch.rotation.setFromRotationMatrix(scratch.basis).multiply(change);
          return target.compose(scratch.position, scratch.rotation, scratch.unit);
        },

        sampler: () => retargetSampler(binding),

        dispose() {
          for (const mesh of character.meshes) {
            mesh.geometry.dispose();
            const material = mesh.material;
            if (Array.isArray(material)) material.forEach((entry) => entry.dispose());
            else material.dispose();
          }
        },
      };

      return build;
    },
  };

  return source;
}

/**
 * The retargeted animation, on the character's own skeleton.
 *
 * The exported file has to carry the character it shows, so its tracks name
 * the source bones and hold the rotations the transfer produced — the same
 * ones the viewport applies, sampled from the same poses.
 */
export function retargetSampler(binding: RetargetBinding): DeformationSampler {
  const rotations = new Map<string, number[]>();
  const hips: number[] = [];
  for (const bound of binding.bones) rotations.set(bound.bone.name, []);

  return {
    sample(pose: Pose) {
      applyRetarget(binding, pose);
      for (const bound of binding.bones) {
        const { x, y, z, w } = bound.bone.quaternion;
        rotations.get(bound.bone.name)!.push(x, y, z, w);
      }
      if (binding.hips) {
        hips.push(binding.hips.position.x, binding.hips.position.y, binding.hips.position.z);
      }
    },

    tracks(times: number[]): KeyframeTrack[] {
      const built: KeyframeTrack[] = [];
      const loopTimes = [times[0], times[times.length - 1]];

      for (const bound of binding.bones) {
        const values = rotations.get(bound.bone.name)!;
        const rest = [bound.restLocal.x, bound.restLocal.y, bound.restLocal.z, bound.restLocal.w];
        const compressed = compressTrack(values, 4, rest);
        if (!compressed) continue;
        built.push(
          new QuaternionKeyframeTrack(
            `${bound.bone.name}.quaternion`,
            compressed.constant ? loopTimes : times,
            compressed.values,
          ),
        );
      }

      if (binding.hips && hips.length >= 3) {
        const rest = [binding.hipsRest.x, binding.hipsRest.y, binding.hipsRest.z];
        const compressed = compressTrack(hips, 3, rest);
        if (compressed) {
          built.push(
            new VectorKeyframeTrack(
              `${binding.hips.name}.position`,
              compressed.constant ? loopTimes : times,
              compressed.values,
              InterpolateLinear,
            ),
          );
        }
      }

      // Baking moved the character; leave it as the file had it, so what is
      // written out is the bind pose plus an animation, not a frozen frame.
      resetCharacter(binding.character);
      return built;
    },
  };
}

async function loadScene(options: RetargetedCharacterOptions): Promise<Object3D> {
  const loader = new GLTFLoader();
  if (options.data) return (await loader.parseAsync(options.data, '')).scene as Object3D;
  if (options.url) return (await loader.loadAsync(options.url)).scene as Object3D;
  throw new Error(`Character "${options.label}" has neither a URL nor file data to load.`);
}

function guessedMapping(label: string, scene: Object3D, boneNames: string[]): BoneMapping {
  const mapping = createMapping(label, `${label} (${boneNames.length} bones)`);
  mapping.bones = guessMapping(boneNames);
  const box = new Box3().setFromObject(scene);
  mapping.characterHeight = Math.max(0.5, box.max.y - box.min.y);
  return mapping;
}

/** The bone nothing else in the character hangs above. */
function topmost(bones: Bone[]): Bone {
  let best = bones[0];
  let shallowest = Infinity;
  for (const bone of bones) {
    let depth = 0;
    let walk: Object3D | null = bone;
    while (walk) {
      depth += 1;
      walk = walk.parent;
    }
    if (depth < shallowest) {
      shallowest = depth;
      best = bone;
    }
  }
  return best;
}
