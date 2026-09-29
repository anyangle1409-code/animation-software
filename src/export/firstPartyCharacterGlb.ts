import type { StudioClip } from '../animation/clip';
import { HgGltfBuilder } from '../core/gltfBuilder';
import {
  addHgGltfAnimation,
  type HgAnimationPath,
  type HgAnimationTrackInput,
} from '../core/gltfAnimation';
import type { ExerciseDefinition } from '../exercises/types';
import { canonicalSkeleton } from '../rig/skeleton';
import type { CharacterSource } from '../character';
import { bakeClipData, type BakedClipData } from './clipData';
import { appendFirstPartyEquipment } from './firstPartyEquipment';

interface AttributeLike {
  readonly count: number;
  readonly itemSize: number;
  readonly array: ArrayLike<number>;
}

interface MaterialLike {
  readonly name?: string;
  readonly color?: { r: number; g: number; b: number };
  readonly opacity?: number;
  readonly metalness?: number;
  readonly roughness?: number;
}

const valuesOf = (attribute: AttributeLike): number[] => Array.from(attribute.array);

const indexValues = (index: { readonly count: number; getX(i: number): number }): number[] =>
  Array.from({ length: index.count }, (_, i) => index.getX(i));

const animationTracks = (
  builder: HgGltfBuilder,
  baked: BakedClipData,
  nodeIndex: ReadonlyMap<string, number>,
  extraTracks: readonly HgAnimationTrackInput[] = [],
) => {
  const tracks: HgAnimationTrackInput[] = baked.tracks.map((track) => {
    const node = nodeIndex.get(track.bone);
    if (node === undefined) throw new Error(`Animation track references unknown bone "${track.bone}"`);
    const path: HgAnimationPath = track.property === 'quaternion' ? 'rotation' : 'translation';
    return { node, path, times: track.times, values: track.values };
  });
  addHgGltfAnimation(builder, { name: baked.name, tracks: [...tracks, ...extraTracks] });
};

/**
 * First-party GLB writer for the clean canonical character.
 *
 * This path owns the GLB container, accessors, mesh, skin, node hierarchy and
 * animation and project-authored equipment. Textured/imported characters and
 * morph deformation stay on the compatibility exporter until their parity
 * gates are implemented.
 */
export async function exportFirstPartyCanonicalCharacterGlb(
  studioClip: StudioClip,
  exercise: ExerciseDefinition,
  source: CharacterSource,
  fps?: number,
  includeEquipment = false,
): Promise<Blob> {
  const character = await source.build(canonicalSkeleton);
  try {
    if (character.driver) throw new Error('First-party canonical export does not accept a source-skeleton driver');
    if (character.capabilities.textured) throw new Error('First-party canonical export does not yet write textures');
    if (character.deformation?.sampler?.() || character.sampler?.()) {
      throw new Error('First-party canonical export does not yet write character deformation tracks');
    }
    if (character.meshes.length !== 1) {
      throw new Error('First-party canonical export currently requires one skinned surface');
    }

    const mesh = character.meshes[0];
    const geometry = mesh.geometry;
    const position = geometry.getAttribute('position') as unknown as AttributeLike;
    const normal = geometry.getAttribute('normal') as unknown as AttributeLike | undefined;
    const uv = geometry.getAttribute('uv') as unknown as AttributeLike | undefined;
    const color = geometry.getAttribute('color') as unknown as AttributeLike | undefined;
    const skinIndex = geometry.getAttribute('skinIndex') as unknown as AttributeLike | undefined;
    const skinWeight = geometry.getAttribute('skinWeight') as unknown as AttributeLike | undefined;
    const index = geometry.getIndex();

    if (!position || !skinIndex || !skinWeight || !index) {
      throw new Error('Canonical character surface is missing required position/skin/index data');
    }

    const builder = new HgGltfBuilder();
    const baked = bakeClipData(studioClip, canonicalSkeleton, { fps });
    const attributes: Record<string, number> = {};

    attributes.POSITION = builder.addAccessor(valuesOf(position), {
      type: 'VEC3',
      componentType: 5126,
      target: 34962,
      includeMinMax: true,
    });
    if (normal) {
      attributes.NORMAL = builder.addAccessor(valuesOf(normal), {
        type: 'VEC3',
        componentType: 5126,
        target: 34962,
      });
    }
    if (uv) {
      attributes.TEXCOORD_0 = builder.addAccessor(valuesOf(uv), {
        type: 'VEC2',
        componentType: 5126,
        target: 34962,
      });
    }
    if (color) {
      attributes.COLOR_0 = builder.addAccessor(valuesOf(color), {
        type: color.itemSize === 4 ? 'VEC4' : 'VEC3',
        componentType: 5126,
        target: 34962,
      });
    }
    attributes.JOINTS_0 = builder.addAccessor(valuesOf(skinIndex), {
      type: 'VEC4',
      componentType: 5123,
      target: 34962,
    });
    attributes.WEIGHTS_0 = builder.addAccessor(valuesOf(skinWeight), {
      type: 'VEC4',
      componentType: 5126,
      target: 34962,
    });

    const indices = indexValues(index);
    const indexComponent = Math.max(...indices) <= 65535 ? 5123 : 5125;
    const indexAccessor = builder.addAccessor(indices, {
      type: 'SCALAR',
      componentType: indexComponent,
      target: 34963,
    });

    const rawMaterial = Array.isArray(mesh.material) ? null : mesh.material as unknown as MaterialLike;
    if (!rawMaterial) throw new Error('First-party canonical export requires one material per surface');
    const tint = rawMaterial.color ?? { r: 1, g: 1, b: 1 };
    const opacity = rawMaterial.opacity ?? 1;
    builder.json.materials = [{
      ...(rawMaterial.name ? { name: rawMaterial.name } : {}),
      pbrMetallicRoughness: {
        baseColorFactor: [tint.r, tint.g, tint.b, opacity],
        metallicFactor: rawMaterial.metalness ?? 0,
        roughnessFactor: rawMaterial.roughness ?? 1,
      },
      ...(opacity < 1 ? { alphaMode: 'BLEND' } : {}),
    }];

    builder.json.meshes = [{
      name: mesh.name,
      primitives: [{
        attributes,
        indices: indexAccessor,
        material: 0,
        mode: 4,
      }],
    }];

    const inverseBindValues = character.skeleton.boneInverses.flatMap((matrix) =>
      Array.from(matrix.elements));
    const inverseBindAccessor = builder.addAccessor(inverseBindValues, {
      type: 'MAT4',
      componentType: 5126,
    });

    const sceneRootIndex = 0;
    const meshNodeIndex = 1;
    const boneStart = 2;
    const boneNodeIndex = new Map<string, number>(
      canonicalSkeleton.bones.map((bone, index) => [bone.name, boneStart + index]),
    );

    const boneNodes = canonicalSkeleton.bones.map((bone) => {
      const children = bone.children.map((child) => boneNodeIndex.get(child)!);
      return {
        name: bone.name,
        translation: [bone.offset.x, bone.offset.y, bone.offset.z],
        rotation: [
          bone.restLocalQuaternion.x,
          bone.restLocalQuaternion.y,
          bone.restLocalQuaternion.z,
          bone.restLocalQuaternion.w,
        ],
        ...(children.length ? { children } : {}),
      };
    });

    builder.json.nodes = [
      {
        name: exercise.clipName,
        children: [meshNodeIndex],
        ...(exercise.travel
          ? { extras: { homeGymPT: { travelSpeed: exercise.travel.speed } } }
          : {}),
      },
      {
        name: mesh.name,
        mesh: 0,
        skin: 0,
        children: [boneNodeIndex.get(canonicalSkeleton.bones[0].name)!],
      },
      ...boneNodes,
    ];
    builder.json.skins = [{
      name: 'hgpt_canonical_skin',
      joints: character.skeleton.bones.map((bone) => {
        const node = boneNodeIndex.get(bone.name);
        if (node === undefined) throw new Error(`Skin references unknown canonical bone "${bone.name}"`);
        return node;
      }),
      skeleton: boneNodeIndex.get(canonicalSkeleton.bones[0].name)!,
      inverseBindMatrices: inverseBindAccessor,
    }];
    builder.json.scenes = [{ name: exercise.clipName, nodes: [sceneRootIndex] }];
    builder.json.scene = 0;

    const equipmentTracks = includeEquipment
      ? appendFirstPartyEquipment(builder, studioClip.equipment, baked, sceneRootIndex)
      : [];
    animationTracks(builder, baked, boneNodeIndex, equipmentTracks);

    const bytes = builder.toGlb();
    return new Blob([new Uint8Array(bytes)], { type: 'model/gltf-binary' });
  } finally {
    character.dispose();
  }
}
