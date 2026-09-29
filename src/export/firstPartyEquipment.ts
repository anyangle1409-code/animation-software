import { HgQuat } from '../core/linearMath';
import type { HgAnimationTrackInput } from '../core/gltfAnimation';
import type { HgGltfBuilder } from '../core/gltfBuilder';
import type { EquipmentInstance } from '../equipment/types';
import { equipmentParts, MATERIALS, type Part } from '../equipment/geometry';
import type { BakedClipData } from './clipData';

import {
  boxPrimitiveData,
  cylinderPrimitiveData,
  spherePrimitiveData,
  torusPrimitiveData,
  type HgPrimitiveGeometryData,
} from '../core/primitiveGeometry';

export type EquipmentPrimitiveData = HgPrimitiveGeometryData;

export function equipmentPrimitiveData(part: Part): EquipmentPrimitiveData {
  switch (part.shape) {
    case 'box':
      return boxPrimitiveData(part.size);
    case 'cylinder':
      return cylinderPrimitiveData(
        part.radius,
        part.radiusTop ?? part.radius,
        part.length,
        part.segments ?? 16,
      );
    case 'sphere':
      return spherePrimitiveData(part.radius);
    case 'torus':
      return torusPrimitiveData(
        part.radius,
        part.tube,
        part.arc ?? Math.PI * 2,
      );
  }
}

const arrays = (builder: HgGltfBuilder) => {
  const materials = Array.isArray(builder.json.materials)
    ? builder.json.materials as Record<string, unknown>[]
    : [];
  const meshes = Array.isArray(builder.json.meshes)
    ? builder.json.meshes as Record<string, unknown>[]
    : [];
  const nodes = Array.isArray(builder.json.nodes)
    ? builder.json.nodes as Record<string, unknown>[]
    : [];
  builder.json.materials = materials;
  builder.json.meshes = meshes;
  builder.json.nodes = nodes;
  return { materials, meshes, nodes };
};

const colourFactor = (colour: string): [number, number, number, number] => {
  const value = Number.parseInt(colour.replace(/^#/, ''), 16);
  return [
    ((value >> 16) & 255) / 255,
    ((value >> 8) & 255) / 255,
    (value & 255) / 255,
    1,
  ];
};

const addEquipmentPrimitive = (
  builder: HgGltfBuilder,
  geometry: EquipmentPrimitiveData,
  part: Part,
  name: string,
): number => {
  const { materials, meshes } = arrays(builder);
  const attributes: Record<string, number> = {
    POSITION: builder.addAccessor(geometry.positions, {
      type: 'VEC3', componentType: 5126, target: 34962, includeMinMax: true,
    }),
    NORMAL: builder.addAccessor(geometry.normals, {
      type: 'VEC3', componentType: 5126, target: 34962,
    }),
    TEXCOORD_0: builder.addAccessor(geometry.uvs, {
      type: 'VEC2', componentType: 5126, target: 34962,
    }),
  };

  const indexAccessor = builder.addAccessor(geometry.indices, {
    type: 'SCALAR',
    componentType: Math.max(...geometry.indices) <= 65535 ? 5123 : 5125,
    target: 34963,
  });

  const surface = MATERIALS[part.material];
  const materialIndex = materials.length;
  materials.push({
    pbrMetallicRoughness: {
      baseColorFactor: colourFactor(surface.color),
      metallicFactor: surface.metalness,
      roughnessFactor: surface.roughness,
    },
  });

  const meshIndex = meshes.length;
  meshes.push({
    name,
    primitives: [{ attributes, indices: indexAccessor, material: materialIndex, mode: 4 }],
  });
  return meshIndex;
};

export interface FirstPartyHandEquipmentPlacement {
  parentNode: number;
  /** Column-major local matrix under the imported hand node. */
  matrix: readonly number[];
}

/** Add project-authored equipment to the first-party GLB and return its animation tracks. */
export function appendFirstPartyEquipment(
  builder: HgGltfBuilder,
  instances: readonly EquipmentInstance[],
  baked: BakedClipData,
  sceneRootIndex: number,
  options: {
    handPlacement?: (instance: EquipmentInstance) => FirstPartyHandEquipmentPlacement | null;
  } = {},
): HgAnimationTrackInput[] {
  const { nodes } = arrays(builder);
  const sceneRoot = nodes[sceneRootIndex];
  if (!sceneRoot) throw new Error('First-party equipment export has no scene root');
  const sceneChildren = Array.isArray(sceneRoot.children) ? [...sceneRoot.children as number[]] : [];
  const tracks: HgAnimationTrackInput[] = [];

  for (const instance of instances) {
    if (!instance.visible) continue;
    const handPlacement =
      instance.attachment.mode === 'hand'
        ? options.handPlacement?.(instance) ?? null
        : null;
    const track = baked.equipmentTracks.get(instance.id);
    if (!handPlacement &&
        (!track || track.position.length < 3 || track.quaternion.length < 4)) {
      throw new Error('No baked equipment transform for ' + instance.id);
    }
    if (handPlacement &&
        (handPlacement.matrix.length !== 16 ||
          handPlacement.matrix.some((value) => !Number.isFinite(value)))) {
      throw new Error('Invalid hand-held equipment matrix for ' + instance.id);
    }

    const parts = equipmentParts(instance.kind, instance.backAngle);

    const rootIndex = nodes.length;
    const rootName =
      instance.attachment.mode === 'hands' || instance.attachment.mode === 'cable'
        ? 'equipment_' + instance.id
        : (instance.label ?? instance.id);
    nodes.push(handPlacement
      ? {
          name: rootName,
          matrix: [...handPlacement.matrix],
          children: [],
        }
      : {
          name: rootName,
          translation: track!.position.slice(0, 3),
          rotation: track!.quaternion.slice(0, 4),
          ...(track!.scale ? { scale: track!.scale.slice(0, 3) } : {}),
          children: [],
        });
    if (handPlacement) {
      const parent = nodes[handPlacement.parentNode];
      if (!parent) throw new Error('Hand-held equipment parent node is missing');
      const children = Array.isArray(parent.children)
        ? [...parent.children as number[]]
        : [];
      children.push(rootIndex);
      parent.children = children;
    } else {
      sceneChildren.push(rootIndex);
    }
    const partNodes: number[] = [];

    parts.forEach((part, partIndex) => {
      const meshIndex = addEquipmentPrimitive(
        builder,
        equipmentPrimitiveData(part),
        part,
        'equipment_part_' + rootIndex + '_' + partIndex,
      );
      const rotation = 'rotation' in part ? part.rotation : undefined;
      const quaternion = rotation
        ? new HgQuat().setFromEulerXYZ(rotation[0], rotation[1], rotation[2])
        : new HgQuat();
      const nodeIndex = nodes.length;
      nodes.push({
        name: 'equipment_part_' + rootIndex + '_' + partIndex,
        mesh: meshIndex,
        ...(part.position ? { translation: [...part.position] } : {}),
        ...(rotation ? { rotation: [quaternion.x, quaternion.y, quaternion.z, quaternion.w] } : {}),
      });
      partNodes.push(nodeIndex);
    });

    (nodes[rootIndex].children as number[]) = partNodes;
    if (!handPlacement) {
      tracks.push(
        { node: rootIndex, path: 'translation', times: baked.times, values: track!.position },
        { node: rootIndex, path: 'rotation', times: baked.times, values: track!.quaternion },
      );
      if (track!.scale) tracks.push({
        node: rootIndex, path: 'scale', times: baked.times, values: track!.scale,
      });
    }
  }

  sceneRoot.children = sceneChildren;
  return tracks;
}
