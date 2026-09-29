import type { CharacterBuild, DeformationTrackData } from '../character/types';
import { characterPrimitiveSource } from '../character/primitiveSource';
import { parseHgGlb } from '../core/glbContainer';
import { HgGltfBuilder } from '../core/gltfBuilder';
import { addHgGltfAnimation, type HgAnimationTrackInput } from '../core/gltfAnimation';
import { hgRuntimeNodeNames } from '../core/gltfRuntimeNames';
import { readHgGltfScene } from '../core/gltfScene';
import { HgMat4 } from '../core/linearMath';
import { anatomicalGripOffset, handAttachmentLocalMatrix } from '../equipment/attach';
import { equipmentSocketForInstance } from '../equipment/library';
import { reflectBakedTrack } from '../equipment/mirror';
import type { EquipmentInstance } from '../equipment/types';
import type { ExerciseDefinition } from '../exercises/types';
import type { BakedClipData } from './clipData';
import { appendFirstPartyEquipment } from './firstPartyEquipment';

type JsonObject = Record<string, unknown>;

interface Attribute3Like {
  readonly count: number;
  readonly name?: string;
  getX(index: number): number;
  getY(index: number): number;
  getZ(index: number): number;
}

interface MorphBinding {
  readonly nodeIndex: number;
  readonly targetNames: string[];
  readonly defaults: number[];
}

type PreservedCharacter = Pick<
  CharacterBuild,
  'preservedGlb' | 'sourceScale' | 'meshes'
> & Partial<Pick<
  CharacterBuild,
  'boneByName' | 'handFrameLocalMatrix' | 'gripOffset' | 'mirrored'
>>;

type PreservedBake = Pick<
  BakedClipData,
  'name' | 'times' | 'deformationTracks'
>;

function objects(value: unknown, label: string): JsonObject[] {
  if (!Array.isArray(value)) throw new Error(label + ' must be an array');
  return value.map((entry, index) => {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) {
      throw new Error(label + '[' + index + '] must be an object');
    }
    return entry as JsonObject;
  });
}

function vec3Values(
  attribute: Attribute3Like,
  base: Attribute3Like,
  relative: boolean,
): number[] {
  if (attribute.count !== base.count) throw new Error('Morph target vertex count changed');
  const values: number[] = [];
  for (let index = 0; index < attribute.count; index += 1) {
    values.push(
      attribute.getX(index) - (relative ? 0 : base.getX(index)),
      attribute.getY(index) - (relative ? 0 : base.getY(index)),
      attribute.getZ(index) - (relative ? 0 : base.getZ(index)),
    );
  }
  return values;
}

function sameNumbers(one: readonly number[], two: readonly number[], epsilon = 1e-8): boolean {
  return one.length === two.length &&
    one.every((value, index) => Math.abs(value - two[index]) <= epsilon);
}

function runtimeTargetNames(
  mesh: CharacterBuild['meshes'][number],
  count: number,
  originalNames: readonly string[],
  positions: readonly Attribute3Like[],
  normals: readonly Attribute3Like[],
): string[] {
  const names = Array.from({ length: count }, (_, index) =>
    originalNames[index] ??
    positions[index]?.name ??
    normals[index]?.name ??
    String(index),
  );
  for (const [name, rawIndex] of Object.entries(mesh.morphTargetDictionary ?? {})) {
    if (Number.isInteger(rawIndex) && rawIndex >= 0 && rawIndex < count) names[rawIndex] = name;
  }
  return names;
}

function setTargetNames(mesh: JsonObject, names: readonly string[]): void {
  if (!names.length) return;
  const extras = mesh.extras;
  if (extras !== undefined && extras !== null &&
      (typeof extras !== 'object' || Array.isArray(extras))) {
    throw new Error('Cannot add morph target names to non-object mesh extras');
  }
  mesh.extras = {
    ...((extras as JsonObject | null | undefined) ?? {}),
    targetNames: [...names],
  };
}

function appendRuntimeMorphs(
  builder: HgGltfBuilder,
  character: PreservedCharacter,
): Map<string, MorphBinding> {
  const jsonMeshes = objects(builder.json.meshes, 'meshes');
  const jsonNodes = objects(builder.json.nodes, 'nodes');
  const bindings = new Map<string, MorphBinding>();
  const meshDefaults = new Map<number, number[]>();

  for (const mesh of character.meshes) {
    const source = characterPrimitiveSource(mesh);
    if (!source) throw new Error('Imported mesh has no preserved GLB primitive identity');

    const jsonMesh = jsonMeshes[source.meshIndex];
    const jsonNode = jsonNodes[source.nodeIndex];
    if (!jsonMesh || !jsonNode) throw new Error('Imported mesh references missing preserved GLB data');
    const primitives = objects(jsonMesh.primitives, 'mesh primitives');
    const primitive = primitives[source.primitiveIndex];
    if (!primitive) throw new Error('Imported mesh references missing preserved GLB primitive');

    const geometry = mesh.geometry;
    const basePosition = geometry.getAttribute('position') as unknown as Attribute3Like;
    const baseNormal = geometry.getAttribute('normal') as unknown as Attribute3Like | undefined;
    const morphPositions =
      (geometry.morphAttributes.position ?? []) as unknown as Attribute3Like[];
    const morphNormals =
      (geometry.morphAttributes.normal ?? []) as unknown as Attribute3Like[];
    const existingTargets = Array.isArray(primitive.targets)
      ? [...primitive.targets as JsonObject[]]
      : [];
    const runtimeCount = Math.max(
      existingTargets.length,
      morphPositions.length,
      morphNormals.length,
    );
    if (runtimeCount < existingTargets.length) {
      throw new Error('Runtime character lost authored morph targets');
    }

    const relative = geometry.morphTargetsRelative === true;
    for (let index = existingTargets.length; index < runtimeCount; index += 1) {
      const target: JsonObject = {};
      const position = morphPositions[index];
      const normal = morphNormals[index];
      if (position) {
        target.POSITION = builder.addAccessor(
          vec3Values(position, basePosition, relative),
          { type: 'VEC3', componentType: 5126, target: 34962 },
        );
      }
      if (normal) {
        if (!baseNormal) throw new Error('Morph normal exists without a base NORMAL attribute');
        target.NORMAL = builder.addAccessor(
          vec3Values(normal, baseNormal, relative),
          { type: 'VEC3', componentType: 5126, target: 34962 },
        );
      }
      if (!Object.keys(target).length) {
        throw new Error('Runtime morph target has no POSITION or NORMAL data');
      }
      existingTargets.push(target);
    }
    if (runtimeCount) primitive.targets = existingTargets;

    const names = runtimeTargetNames(
      mesh,
      runtimeCount,
      source.targetNames,
      morphPositions,
      morphNormals,
    );
    setTargetNames(jsonMesh, names);

    const defaults = Array.from(
      { length: runtimeCount },
      (_, index) => mesh.morphTargetInfluences?.[index] ?? 0,
    );
    if (Array.isArray(jsonNode.weights)) {
      jsonNode.weights = defaults;
    } else if (runtimeCount) {
      const previous = meshDefaults.get(source.meshIndex);
      if (previous && !sameNumbers(previous, defaults)) {
        throw new Error('Shared preserved mesh has inconsistent runtime morph defaults');
      }
      meshDefaults.set(source.meshIndex, defaults);
      jsonMesh.weights = defaults;
    }

    if (bindings.has(mesh.name)) {
      throw new Error('Imported runtime mesh name is ambiguous: ' + mesh.name);
    }
    bindings.set(mesh.name, {
      nodeIndex: source.nodeIndex,
      targetNames: names,
      defaults,
    });
  }

  return bindings;
}

function scalarAt(track: DeformationTrackData, time: number): number {
  if (track.property !== 'morphTargetInfluence') {
    throw new Error('Only scalar morph tracks can be sampled as weights');
  }
  if (track.times.length !== track.values.length || !track.times.length) {
    throw new Error('Morph track sample count is invalid');
  }
  if (time <= track.times[0]) return track.values[0];
  const last = track.times.length - 1;
  if (time >= track.times[last]) return track.values[last];

  for (let index = 1; index < track.times.length; index += 1) {
    if (time > track.times[index]) continue;
    const fromTime = track.times[index - 1];
    const toTime = track.times[index];
    const alpha = (time - fromTime) / (toTime - fromTime);
    return track.values[index - 1] +
      (track.values[index] - track.values[index - 1]) * alpha;
  }
  return track.values[last];
}

function animationTracks(
  decoded: ReturnType<typeof readHgGltfScene>,
  morphBindings: ReadonlyMap<string, MorphBinding>,
  baked: PreservedBake,
): HgAnimationTrackInput[] {
  const runtimeNames = hgRuntimeNodeNames(decoded.nodes.map((node) => node.name));
  const nodeByName = new Map(runtimeNames.map((name, index) => [name, index]));
  const result: HgAnimationTrackInput[] = [];
  const morphGroups = new Map<
    number,
    { defaults: number[]; tracks: Map<number, DeformationTrackData> }
  >();

  for (const track of baked.deformationTracks) {
    if (track.property === 'quaternion' || track.property === 'position') {
      const node = nodeByName.get(track.target);
      if (node === undefined) {
        throw new Error('Animation track references unknown imported node "' + track.target + '"');
      }
      result.push({
        node,
        path: track.property === 'quaternion' ? 'rotation' : 'translation',
        times: track.times,
        values: track.values,
      });
      continue;
    }

    const binding = morphBindings.get(track.target);
    if (!binding) {
      throw new Error('Morph track references unknown imported mesh "' + track.target + '"');
    }
    const morphIndex = binding.targetNames.indexOf(track.morphTarget);
    if (morphIndex < 0) {
      throw new Error('Morph track references unknown target "' + track.morphTarget + '"');
    }

    let group = morphGroups.get(binding.nodeIndex);
    if (!group) {
      group = { defaults: [...binding.defaults], tracks: new Map() };
      morphGroups.set(binding.nodeIndex, group);
    } else if (!sameNumbers(group.defaults, binding.defaults)) {
      throw new Error('Imported primitives disagree on morph target defaults');
    }
    const existing = group.tracks.get(morphIndex);
    if (existing) {
      if (!sameNumbers(existing.times, track.times) ||
          !sameNumbers(existing.values, track.values)) {
        throw new Error('Imported primitives disagree on a shared morph animation');
      }
    } else {
      group.tracks.set(morphIndex, track);
    }
  }

  for (const [node, group] of morphGroups) {
    const values: number[] = [];
    for (const time of baked.times) {
      const frame = [...group.defaults];
      for (const [index, track] of group.tracks) frame[index] = scalarAt(track, time);
      values.push(...frame);
    }
    result.push({
      node,
      path: 'weights',
      times: baked.times,
      values,
    });
  }

  return result;
}

function topLevelNodes(decoded: ReturnType<typeof readHgGltfScene>): number[] {
  const children = new Set(decoded.nodes.flatMap((node) => node.children));
  return decoded.nodes
    .filter((node) => !children.has(node.index))
    .map((node) => node.index);
}

function matrixFromValues(values: readonly number[]): HgMat4 {
  if (values.length !== 16 || values.some((value) => !Number.isFinite(value))) {
    throw new Error('Imported hand grip frame must be a finite 4x4 matrix');
  }
  const matrix = new HgMat4();
  for (let index = 0; index < 16; index += 1) matrix.elements[index] = values[index];
  return matrix;
}

function equipmentBake(
  baked: BakedClipData,
  instances: readonly EquipmentInstance[],
  mirrored: boolean,
): BakedClipData {
  const byId = new Map(instances.map((instance) => [instance.id, instance]));
  const equipmentTracks = new Map(
    [...baked.equipmentTracks].map(([id, track]) => {
      const copy = {
        position: [...track.position],
        quaternion: [...track.quaternion],
        ...(track.scale ? { scale: [...track.scale] } : {}),
      };
      const instance = byId.get(id);
      if (mirrored && instance && instance.attachment.mode !== 'hand') {
        reflectBakedTrack(copy);
      }
      return [id, copy] as const;
    }),
  );
  return { ...baked, equipmentTracks };
}

function handEquipmentPlacement(
  character: PreservedCharacter,
  decoded: ReturnType<typeof readHgGltfScene>,
): (instance: EquipmentInstance) => { parentNode: number; matrix: number[] } | null {
  const runtimeNames = hgRuntimeNodeNames(decoded.nodes.map((node) => node.name));
  const nodeByName = new Map(runtimeNames.map((name, index) => [name, index]));

  return (instance) => {
    if (instance.attachment.mode !== 'hand') return null;
    const side = instance.attachment.side;
    const canonicalHand = side === 'l' ? 'hand_l' : 'hand_r';
    const hand = character.boneByName?.get(canonicalHand);
    if (!hand) throw new Error('Preserved character has no ' + canonicalHand + ' bone');
    const parentNode = nodeByName.get(hand.name);
    if (parentNode === undefined) {
      throw new Error('Preserved character hand is missing from source GLB: ' + hand.name);
    }

    const frame = character.handFrameLocalMatrix?.(side);
    if (!frame) {
      throw new Error('Preserved character has no first-party hand grip frame for ' + side);
    }
    const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
    const grip =
      instance.attachment.gripOffset ??
      character.gripOffset?.(side) ??
      anatomicalGripOffset(side);
    const attachment = handAttachmentLocalMatrix(
      grip,
      socket?.position ?? { x: 0, y: 0, z: 0 },
      {
        gripRotation: instance.attachment.gripRotation,
        socketRotation: socket?.rotation,
      },
    );
    const local = matrixFromValues(frame).multiply(attachment);
    return { parentNode, matrix: Array.from(local.elements) };
  };
}


/**
 * First-party writer for a preserved imported character.
 *
 * It starts from the exact original GLB, appends runtime-created morph targets,
 * Home Gym PT animation and project-authored equipment, and adds wrapper nodes
 * for studio scale and clip metadata. Authored mesh, skin, materials, textures
 * and helper bones stay in their original GLB representation.
 */
export function exportFirstPartyPreservedCharacterGlb(
  character: PreservedCharacter,
  baked: BakedClipData,
  exercise: Pick<ExerciseDefinition, 'clipName' | 'travel'>,
  equipment: readonly EquipmentInstance[] = [],
): Blob {
  if (!character.preservedGlb) {
    throw new Error('Character has no preserved source GLB');
  }

  const source = parseHgGlb(character.preservedGlb);
  const decoded = readHgGltfScene(source);
  const builder = HgGltfBuilder.fromDocument(source);
  const morphBindings = appendRuntimeMorphs(builder, character);
  const tracks = animationTracks(decoded, morphBindings, baked);

  const nodes = objects(builder.json.nodes, 'nodes');
  const sourceScene = decoded.defaultScene === null
    ? decoded.scenes[0] ?? null
    : decoded.scenes[decoded.defaultScene] ?? null;
  const characterRoot = nodes.length;
  nodes.push({
    name: sourceScene?.name || 'Scene',
    children: sourceScene?.nodes ?? topLevelNodes(decoded),
    scale: [
      character.sourceScale ?? 1,
      character.sourceScale ?? 1,
      character.sourceScale ?? 1,
    ],
    ...(sourceScene?.extras !== null && sourceScene?.extras !== undefined
      ? { extras: sourceScene.extras }
      : {}),
  });

  const exportRoot = nodes.length;
  nodes.push({
    name: exercise.clipName,
    children: [characterRoot],
    ...(exercise.travel
      ? { extras: { homeGymPT: { travelSpeed: exercise.travel.speed } } }
      : {}),
  });
  builder.json.nodes = nodes;
  builder.json.scenes = [{ name: exercise.clipName, nodes: [exportRoot] }];
  builder.json.scene = 0;

  const equipmentTracks = equipment.length
    ? appendFirstPartyEquipment(
        builder,
        equipment,
        equipmentBake(baked, equipment, Boolean(character.mirrored)),
        exportRoot,
        { handPlacement: handEquipmentPlacement(character, decoded) },
      )
    : [];

  builder.json.animations = [];
  addHgGltfAnimation(builder, {
    name: baked.name,
    tracks: [...tracks, ...equipmentTracks],
  });

  const bytes = builder.toGlb();
  return new Blob([new Uint8Array(bytes)], { type: 'model/gltf-binary' });
}
