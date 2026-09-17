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
  CharacterPoseContext,
  CharacterSource,
  DeformationSampler,
  DeformationStack,
  Side,
} from './types';
import { RetargetContactResolver } from './retargetContact';
import { solvedGripFor } from './solvedGrip';
import { anatomicalGripOffset } from '../equipment/attach';
import { importedElbowDeformation } from './importedDeformation';
import type { ImportedElbowRuntimeTuning } from './importedDeformation';
import { importedMuscleDeformation } from './muscleDeformation';
import type { MuscleRuntimeTuning } from './muscleDeformation';

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
 *   and face details stay in the source hierarchy. Connected helpers ride
 *   their parents; detached Rigify detail branches receive rigid attachment
 *   transforms. Their weights are never redistributed.
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
  /** Per-hand grip-frame calibration in studio metres, after basis transfer. */
  gripFrameOffsets?: Partial<Record<Side, { x: number; y: number; z: number }>>;
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
  /** Bones without canonical joint targets, including attached detail branches. */
  passive: number;
}

export interface RetargetedCharacterSource extends CharacterSource {
  /** How the last build read the file. Null until it is built. */
  lastReport: ImportReport | null;
}

export function retargetedCharacterSource(
  options: RetargetedCharacterOptions,
): RetargetedCharacterSource {
  const elbowTuning: ImportedElbowRuntimeTuning = { outerSmooth: 0, defaultOuterSmooth: 0 };
  let elbowTuningInitialised = false;
  const muscleTuning: MuscleRuntimeTuning = { amount: 1, defaultAmount: 1 };

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
      const embeddedGripOffsets = readGripOffsets(scene.userData?.homeGymPT?.gripFrameOffsets);
      const gripOffsets = options.gripFrameOffsets ?? embeddedGripOffsets;
      // Where a handle sits inside this character's closed fist, measured on
      // its own wrapping fingers. Separate from the grip *frame* above, which
      // is the palm contact point; stacking the canonical constant on that
      // frame put the handle outside the fist.
      const handleOffsets = readGripOffsets(scene.userData?.homeGymPT?.handleGripOffsets);
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

      const handMatrix = (side: Side, target: Matrix4): Matrix4 | null => {
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
        target.compose(scratch.position, scratch.rotation, scratch.unit);
        const offset = gripOffsets?.[side];
        if (offset) target.multiply(new Matrix4().makeTranslation(offset.x, offset.y, offset.z));
        return target;
      };

      // The solved handle centre, applied here so the renderer, the exporter
      // and the diagnostics all read one corrected offset and cannot diverge.
      const solutionId = scene.userData?.homeGymPT?.gripSolutionId
        ? String(scene.userData.homeGymPT.gripSolutionId)
        : handleOffsets
          ? 'homeGymPTMale'
          : undefined;
      const centre = solvedGripFor(solutionId, 'dumbbell')?.handleCentre;
      const gripOffset = handleOffsets
        ? (side: Side) => {
            const embedded = handleOffsets[side] ?? anatomicalGripOffset(side);
            if (!centre) return embedded;
            return {
              x: embedded.x + (side === 'l' ? centre.x : -centre.x),
              y: embedded.y + centre.y,
              z: embedded.z + centre.z,
            };
          }
        : undefined;

      const contacts = new RetargetContactResolver(binding, boneByName, handMatrix);
      const drive = (pose: Pose, context?: CharacterPoseContext) => {
        if (!context?.contacts?.length) {
          applyRetarget(binding, pose);
          return;
        }
        const rootOffset = new Vector3();
        // A shorter imported limb can be unable to reach a fixed contact. Move
        // this character's body by the shared residual, then let each source
        // limb solve the remaining error. A few bounded passes converge the
        // four-point push-up support as well as the suspended pull-up body.
        for (let pass = 0; pass < 8; pass += 1) {
          applyRetarget(binding, pose, rootOffset);
          const residual = contacts.apply(context.contacts);
          if (!residual || residual.length() <= 0.001) break;
          rootOffset.add(contacts.rootOffset(residual));
        }
      };

      const elbowOptions = scene.userData?.homeGymPT?.elbowCorrective;
      if (elbowOptions?.enabled && !elbowTuningInitialised) {
        const authored = Number(elbowOptions.outerSmooth ?? 0);
        const bounded = Number.isFinite(authored) ? Math.min(1, Math.max(0, authored)) : 0;
        elbowTuning.outerSmooth = bounded;
        elbowTuning.defaultOuterSmooth = bounded;
        elbowTuningInitialised = true;
      }
      const elbow = importedElbowDeformation(
        character.meshes as SkinnedMesh[],
        boneByName,
        rig,
        elbowOptions,
        elbowOptions?.enabled ? elbowTuning : undefined,
      );
      // Built after the elbow correctives, because the muscle layer supplies
      // morph normals and three.js indexes those by position-morph slot — it
      // has to see every target the geometry already carries.
      const muscle = importedMuscleDeformation(
        character.meshes as SkinnedMesh[],
        boneByName,
        rig,
        scene.userData?.homeGymPT?.muscleDeformation,
        muscleTuning,
      );
      const deformation = composeDeformation(elbow, muscle);

      const build: CharacterBuild = {
        source: source.id,
        root,
        bones,
        boneByName,
        skeleton: character.meshes[0].skeleton,
        object: scene,
        meshes: character.meshes as SkinnedMesh[],
        deformation,
        capabilities: source.capabilities,

        driver: drive,

        handMatrix,
        ...(gripOffset ? { gripOffset } : {}),
        // Which solved grip this character may use. A solved grip is measured
        // on one body's fingers, so it is only offered to a character that
        // also carries its own handle offsets — those were measured on the
        // same hand. A different body sets its own id in the GLB and is
        // solved in its own right rather than inheriting this one.
        ...(solutionId ? { gripSolutionId: solutionId } : {}),

        sampler: () => combineSamplers(retargetSampler(binding, drive), deformation?.sampler?.() ?? null),

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
 * Run several deformation layers as one stack.
 *
 * `CharacterBuild` carries a single stack, and the layers are independent —
 * each owns its own morph targets — so updating both in order and concatenating
 * their controls is the whole composition.
 */
function composeDeformation(
  ...layers: (DeformationStack | null)[]
): DeformationStack | null {
  const present = layers.filter((layer): layer is DeformationStack => layer !== null);
  if (present.length <= 1) return present[0] ?? null;
  const controls = present.flatMap((layer) => layer.controls ?? []);
  return {
    ...(controls.length ? { controls } : {}),
    update(context) {
      for (const layer of present) layer.update(context);
    },
    sampler: () =>
      present.reduce<DeformationSampler | null>(
        (combined, layer) => {
          const next = layer.sampler?.() ?? null;
          if (!combined) return next;
          return next ? combineSamplers(combined, next) : combined;
        },
        null,
      ),
  };
}

function combineSamplers(
  primary: DeformationSampler,
  secondary: DeformationSampler | null,
): DeformationSampler {
  if (!secondary) return primary;
  return {
    sample(pose, context) {
      primary.sample(pose, context);
      secondary.sample(pose, context);
    },
    tracks(times) {
      return [...primary.tracks(times), ...secondary.tracks(times)];
    },
  };
}

/**
 * The retargeted animation, on the character's own skeleton.
 *
 * The exported file has to carry the character it shows, so its tracks name
 * the source bones and hold the rotations and translations produced — the same
 * ones the viewport applies, sampled from the same poses.
 */
export function retargetSampler(
  binding: RetargetBinding,
  drive: (pose: Pose, context?: CharacterPoseContext) => void = (pose) => applyRetarget(binding, pose),
): DeformationSampler {
  const bones = [...binding.character.bones.values()];
  const rotations = new Map(bones.map(bone => [bone.name, [] as number[]]));
  const positions = new Map(bones.map(bone => [bone.name, [] as number[]]));

  return {
    sample(pose: Pose, context?: CharacterPoseContext) {
      drive(pose, context);
      for (const bone of bones) {
        rotations.get(bone.name)!.push(...bone.quaternion.toArray());
        positions.get(bone.name)!.push(...bone.position.toArray());
      }
    },
    tracks(times: number[]): KeyframeTrack[] {
      const built: KeyframeTrack[] = [];
      const loopTimes = [times[0], times[times.length - 1]];
      for (const bone of bones) {
        const rotation = compressTrack(rotations.get(bone.name)!, 4,
          binding.character.restLocal.get(bone.name)!.toArray());
        if (rotation) built.push(new QuaternionKeyframeTrack(
          `${bone.name}.quaternion`, rotation.constant ? loopTimes : times, rotation.values,
        ));
        const position = compressTrack(positions.get(bone.name)!, 3,
          binding.character.restPosition.get(bone.name)!.toArray());
        if (position) built.push(new VectorKeyframeTrack(
          `${bone.name}.position`, position.constant ? loopTimes : times, position.values, InterpolateLinear,
        ));
      }
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


function readGripOffsets(value: unknown): Partial<Record<Side, { x: number; y: number; z: number }>> | undefined {
  if (!value || typeof value !== 'object') return undefined;
  const result: Partial<Record<Side, { x: number; y: number; z: number }>> = {};
  for (const side of ['l', 'r'] as const) {
    const raw = (value as Record<string, unknown>)[side];
    if (!Array.isArray(raw) || raw.length !== 3 || !raw.every(Number.isFinite)) continue;
    result[side] = { x: Number(raw[0]), y: Number(raw[1]), z: Number(raw[2]) };
  }
  return result.l || result.r ? result : undefined;
}
