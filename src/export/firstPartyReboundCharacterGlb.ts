import type { StudioClip } from '../animation/clip';
import { parseHgGlb } from '../core/glbContainer';
import { addHgGltfAnimation, type HgAnimationPath, type HgAnimationTrackInput } from '../core/gltfAnimation';
import { HgGltfBuilder } from '../core/gltfBuilder';
import type { CharacterBuild } from '../character/types';
import { anatomicalGripOffset, handAttachmentLocalMatrix } from '../equipment/attach';
import { equipmentSocketForInstance } from '../equipment/library';
import type { EquipmentInstance } from '../equipment/types';
import type { ExerciseDefinition } from '../exercises/types';
import { canonicalSkeleton } from '../rig/skeleton';
import { bakeClipData, type BakedClipData } from './clipData';
import { appendFirstPartyEquipment } from './firstPartyEquipment';

type JsonObject = Record<string, unknown>;

interface AttributeLike {
  readonly count: number;
  readonly itemSize: number;
  readonly array: ArrayLike<number>;
}

function objects(value: unknown, label: string): JsonObject[] {
  if (value === undefined) return [];
  if (!Array.isArray(value)) throw new Error(label + ' must be an array');
  return value.map((entry, index) => {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) {
      throw new Error(label + '[' + index + '] must be an object');
    }
    return entry as JsonObject;
  });
}

const valuesOf = (attribute: AttributeLike): number[] => Array.from(attribute.array);

const indexValues = (index: { readonly count: number; getX(i: number): number }): number[] =>
  Array.from({ length: index.count }, (_, i) => index.getX(i));

function sourcePrimitive(
  builder: HgGltfBuilder,
  origin: NonNullable<CharacterBuild['sourceSurfaceOrigins']>[number],
): JsonObject {
  const mesh = objects(builder.json.meshes, 'meshes')[origin.meshIndex];
  if (!mesh) throw new Error('Rebound surface references a missing source mesh');
  const primitive = objects(mesh.primitives, 'source mesh primitives')[origin.primitiveIndex];
  if (!primitive) throw new Error('Rebound surface references a missing source primitive');
  return primitive;
}

function appendRuntimeMeshes(
  builder: HgGltfBuilder,
  character: CharacterBuild,
): number[] {
  const origins = character.sourceSurfaceOrigins;
  if (!origins || origins.length !== character.meshes.length) {
    throw new Error('Rebound character has no complete source primitive map');
  }

  const meshes = objects(builder.json.meshes, 'meshes');
  builder.json.meshes = meshes;
  const indices: number[] = [];

  character.meshes.forEach((mesh, surfaceIndex) => {
    const geometry = mesh.geometry;
    const position = geometry.getAttribute('position') as unknown as AttributeLike | undefined;
    const normal = geometry.getAttribute('normal') as unknown as AttributeLike | undefined;
    const uv = geometry.getAttribute('uv') as unknown as AttributeLike | undefined;
    const color = geometry.getAttribute('color') as unknown as AttributeLike | undefined;
    const skinIndex = geometry.getAttribute('skinIndex') as unknown as AttributeLike | undefined;
    const skinWeight = geometry.getAttribute('skinWeight') as unknown as AttributeLike | undefined;
    const index = geometry.getIndex();
    if (!position || !skinIndex || !skinWeight || !index) {
      throw new Error('Rebound surface is missing required position/skin/index data');
    }

    const attributes: Record<string, number> = {
      POSITION: builder.addAccessor(valuesOf(position), {
        type: 'VEC3',
        componentType: 5126,
        target: 34962,
        includeMinMax: true,
      }),
      JOINTS_0: builder.addAccessor(valuesOf(skinIndex), {
        type: 'VEC4',
        componentType: 5123,
        target: 34962,
      }),
      WEIGHTS_0: builder.addAccessor(valuesOf(skinWeight), {
        type: 'VEC4',
        componentType: 5126,
        target: 34962,
      }),
    };
    if (normal) {
      attributes.NORMAL = builder.addAccessor(valuesOf(normal), {
        type: 'VEC3', componentType: 5126, target: 34962,
      });
    }
    if (uv) {
      attributes.TEXCOORD_0 = builder.addAccessor(valuesOf(uv), {
        type: 'VEC2', componentType: 5126, target: 34962,
      });
    }
    if (color) {
      attributes.COLOR_0 = builder.addAccessor(valuesOf(color), {
        type: color.itemSize === 4 ? 'VEC4' : 'VEC3',
        componentType: 5126,
        target: 34962,
      });
    }

    const rawIndices = indexValues(index);
    const source = sourcePrimitive(builder, origins[surfaceIndex]);
    const primitive: JsonObject = {
      attributes,
      indices: builder.addAccessor(rawIndices, {
        type: 'SCALAR',
        componentType: Math.max(...rawIndices) <= 65535 ? 5123 : 5125,
        target: 34963,
      }),
      mode: typeof source.mode === 'number' ? source.mode : 4,
      ...(typeof source.material === 'number' ? { material: source.material } : {}),
    };

    const meshIndex = meshes.length;
    meshes.push({
      name: mesh.name,
      primitives: [primitive],
    });
    indices.push(meshIndex);
  });

  return indices;
}

function animationTracks(
  baked: BakedClipData,
  boneNodeIndex: ReadonlyMap<string, number>,
): HgAnimationTrackInput[] {
  return baked.tracks.map((track) => {
    const node = boneNodeIndex.get(track.bone);
    if (node === undefined) {
      throw new Error('Rebound animation references unknown canonical bone "' + track.bone + '"');
    }
    const path: HgAnimationPath =
      track.property === 'quaternion' ? 'rotation' : 'translation';
    return { node, path, times: track.times, values: track.values };
  });
}

/**
 * First-party writer for the optional diagnostic rebind route.
 *
 * Rebind deliberately changes positions/weights onto the canonical rig, so it
 * cannot preserve the original mesh bytes. It does preserve the source GLB's
 * authored material/texture resources and points the rebuilt runtime surfaces
 * back at their original primitive materials.
 */
export function exportFirstPartyReboundCharacterGlb(
  studioClip: StudioClip,
  exercise: ExerciseDefinition,
  character: CharacterBuild,
  fps?: number,
  includeEquipment = true,
): Blob {
  if (character.driver) {
    throw new Error('Rebound export requires a canonical-skeleton character');
  }
  if (!character.sourceGlb) {
    throw new Error('Rebound character has no source GLB resources');
  }

  const builder = HgGltfBuilder.fromDocument(parseHgGlb(character.sourceGlb));
  const appendedMeshes = appendRuntimeMeshes(builder, character);
  const allMeshes = objects(builder.json.meshes, 'meshes');
  // The original scene graph and source skin are diagnostic input only. Keep
  // authored materials/textures/binary resources, but export only the rebuilt
  // runtime surfaces so stale source bones cannot shadow canonical node names.
  builder.json.meshes = appendedMeshes.map((index) => allMeshes[index]);
  const runtimeMeshes = appendedMeshes.map((_, index) => index);
  const baked = bakeClipData(studioClip, canonicalSkeleton, { fps });

  const nodes: JsonObject[] = [];
  builder.json.nodes = nodes;
  const skins: JsonObject[] = [];
  builder.json.skins = skins;

  const inverseBindAccessor = builder.addAccessor(
    character.skeleton.boneInverses.flatMap((matrix) => Array.from(matrix.elements)),
    { type: 'MAT4', componentType: 5126 },
  );

  const exportRoot = nodes.length;
  nodes.push({ name: exercise.clipName, children: [] });

  const boneStart = nodes.length;
  const boneNodeIndex = new Map(
    canonicalSkeleton.bones.map((bone, index) => [bone.name, boneStart + index]),
  );
  canonicalSkeleton.bones.forEach((bone) => {
    const children = bone.children.map((child) => boneNodeIndex.get(child)!);
    nodes.push({
      name: bone.name,
      translation: [bone.offset.x, bone.offset.y, bone.offset.z],
      rotation: [
        bone.restLocalQuaternion.x,
        bone.restLocalQuaternion.y,
        bone.restLocalQuaternion.z,
        bone.restLocalQuaternion.w,
      ],
      ...(children.length ? { children } : {}),
    });
  });

  const skinIndex = skins.length;
  skins.push({
    name: 'hgpt_canonical_rebound_skin',
    joints: canonicalSkeleton.bones.map((bone) => boneNodeIndex.get(bone.name)!),
    skeleton: boneNodeIndex.get(canonicalSkeleton.bones[0].name)!,
    inverseBindMatrices: inverseBindAccessor,
  });

  const meshNodes = runtimeMeshes.map((mesh, index) => {
    const nodeIndex = nodes.length;
    nodes.push({
      name: character.meshes[index].name,
      mesh,
      skin: skinIndex,
    });
    return nodeIndex;
  });

  const root = nodes[exportRoot];
  root.children = [
    boneNodeIndex.get(canonicalSkeleton.bones[0].name)!,
    ...meshNodes,
  ];
  if (exercise.travel) {
    root.extras = { homeGymPT: { travelSpeed: exercise.travel.speed } };
  }

  builder.json.scenes = [{ name: exercise.clipName, nodes: [exportRoot] }];
  builder.json.scene = 0;
  builder.json.animations = [];

  const canonicalHandPlacement = (instance: EquipmentInstance) => {
    if (instance.attachment.mode !== 'hand') return null;
    const side = instance.attachment.side;
    const boneName = side === 'l' ? 'hand_l' : 'hand_r';
    const parentNode = boneNodeIndex.get(boneName);
    if (parentNode === undefined) {
      throw new Error('Rebound export has no canonical ' + boneName + ' node');
    }
    const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
    const grip = instance.attachment.gripOffset ?? anatomicalGripOffset(side);
    const matrix = handAttachmentLocalMatrix(
      grip,
      socket?.position ?? { x: 0, y: 0, z: 0 },
      {
        gripRotation: instance.attachment.gripRotation,
        socketRotation: socket?.rotation,
      },
    );
    return { parentNode, matrix: Array.from(matrix.elements) };
  };

  const equipmentTracks = includeEquipment
    ? appendFirstPartyEquipment(
        builder,
        studioClip.equipment,
        baked,
        exportRoot,
        { handPlacement: canonicalHandPlacement },
      )
    : [];
  addHgGltfAnimation(builder, {
    name: baked.name,
    tracks: [...animationTracks(baked, boneNodeIndex), ...equipmentTracks],
  });

  const bytes = builder.toGlb();
  return new Blob([new Uint8Array(bytes)], { type: 'model/gltf-binary' });
}
