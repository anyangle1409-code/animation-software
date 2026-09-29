import { HgQuat } from '../core/linearMath';
import type { HgAnimationTrackInput } from '../core/gltfAnimation';
import type { HgGltfBuilder } from '../core/gltfBuilder';
import type { EquipmentInstance } from '../equipment/types';
import { equipmentParts } from '../equipment/geometry';
import type { BakedClipData } from './clipData';
import { buildEquipmentObject } from './rigBuilder';

interface AttributeLike {
  readonly count: number;
  readonly itemSize: number;
  readonly array: ArrayLike<number>;
}

interface GeometryLike {
  getAttribute(name: string): AttributeLike | undefined;
  getIndex(): { readonly count: number; getX(index: number): number } | null;
  dispose?(): void;
}

interface MaterialLike {
  readonly name?: string;
  readonly color?: { r: number; g: number; b: number };
  readonly opacity?: number;
  readonly metalness?: number;
  readonly roughness?: number;
  dispose?(): void;
}

interface EquipmentChildLike {
  readonly geometry?: GeometryLike;
  readonly material?: MaterialLike | MaterialLike[];
}

interface EquipmentObjectLike {
  readonly children: readonly EquipmentChildLike[];
}

const valuesOf = (attribute: AttributeLike): number[] => Array.from(attribute.array);

const indicesOf = (index: { readonly count: number; getX(i: number): number } | null, count: number): number[] =>
  index
    ? Array.from({ length: index.count }, (_, i) => index.getX(i))
    : Array.from({ length: count }, (_, i) => i);

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

const addEquipmentPrimitive = (
  builder: HgGltfBuilder,
  geometry: GeometryLike,
  material: MaterialLike,
  name: string,
): number => {
  const { materials, meshes } = arrays(builder);
  const position = geometry.getAttribute('position');
  if (!position) throw new Error('Equipment geometry has no position data');
  const attributes: Record<string, number> = {
    POSITION: builder.addAccessor(valuesOf(position), {
      type: 'VEC3', componentType: 5126, target: 34962, includeMinMax: true,
    }),
  };
  const normal = geometry.getAttribute('normal');
  if (normal) attributes.NORMAL = builder.addAccessor(valuesOf(normal), {
    type: 'VEC3', componentType: 5126, target: 34962,
  });
  const uv = geometry.getAttribute('uv');
  if (uv) attributes.TEXCOORD_0 = builder.addAccessor(valuesOf(uv), {
    type: 'VEC2', componentType: 5126, target: 34962,
  });

  const indices = indicesOf(geometry.getIndex(), position.count);
  const indexAccessor = builder.addAccessor(indices, {
    type: 'SCALAR',
    componentType: Math.max(...indices) <= 65535 ? 5123 : 5125,
    target: 34963,
  });

  const tint = material.color ?? { r: 1, g: 1, b: 1 };
  const opacity = material.opacity ?? 1;
  const materialIndex = materials.length;
  materials.push({
    ...(material.name ? { name: material.name } : {}),
    pbrMetallicRoughness: {
      baseColorFactor: [tint.r, tint.g, tint.b, opacity],
      metallicFactor: material.metalness ?? 0,
      roughnessFactor: material.roughness ?? 1,
    },
    ...(opacity < 1 ? { alphaMode: 'BLEND' } : {}),
  });

  const meshIndex = meshes.length;
  meshes.push({
    name,
    primitives: [{ attributes, indices: indexAccessor, material: materialIndex, mode: 4 }],
  });
  return meshIndex;
};

/** Add project-authored equipment to the first-party GLB and return its animation tracks. */
export function appendFirstPartyEquipment(
  builder: HgGltfBuilder,
  instances: readonly EquipmentInstance[],
  baked: BakedClipData,
  sceneRootIndex: number,
): HgAnimationTrackInput[] {
  const { nodes } = arrays(builder);
  const sceneRoot = nodes[sceneRootIndex];
  if (!sceneRoot) throw new Error('First-party equipment export has no scene root');
  const sceneChildren = Array.isArray(sceneRoot.children) ? [...sceneRoot.children as number[]] : [];
  const tracks: HgAnimationTrackInput[] = [];

  for (const instance of instances) {
    if (!instance.visible) continue;
    const track = baked.equipmentTracks.get(instance.id);
    if (!track || track.position.length < 3 || track.quaternion.length < 4) {
      throw new Error('No baked equipment transform for ' + instance.id);
    }

    const object = buildEquipmentObject(instance.kind, instance.backAngle) as unknown as EquipmentObjectLike;
    const parts = equipmentParts(instance.kind, instance.backAngle);
    if (object.children.length !== parts.length) {
      throw new Error('Equipment part count changed while exporting ' + instance.id);
    }

    const rootIndex = nodes.length;
    const rootName =
      instance.attachment.mode === 'hands' || instance.attachment.mode === 'cable'
        ? 'equipment_' + instance.id
        : (instance.label ?? instance.id);
    nodes.push({
      name: rootName,
      translation: track.position.slice(0, 3),
      rotation: track.quaternion.slice(0, 4),
      ...(track.scale ? { scale: track.scale.slice(0, 3) } : {}),
      children: [],
    });
    sceneChildren.push(rootIndex);
    const partNodes: number[] = [];

    try {
      object.children.forEach((child, partIndex) => {
        const geometry = child.geometry;
        const rawMaterial = child.material;
        const material = Array.isArray(rawMaterial) ? null : rawMaterial;
        if (!geometry || !material) throw new Error('Equipment part is not a single-material mesh');
        const meshIndex = addEquipmentPrimitive(
          builder, geometry, material, 'equipment_part_' + rootIndex + '_' + partIndex,
        );
        const part = parts[partIndex];
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
    } finally {
      for (const child of object.children) {
        child.geometry?.dispose?.();
        const material = child.material;
        if (Array.isArray(material)) material.forEach((entry) => entry.dispose?.());
        else material?.dispose?.();
      }
    }

    (nodes[rootIndex].children as number[]) = partNodes;
    tracks.push(
      { node: rootIndex, path: 'translation', times: baked.times, values: track.position },
      { node: rootIndex, path: 'rotation', times: baked.times, values: track.quaternion },
    );
    if (track.scale) tracks.push({
      node: rootIndex, path: 'scale', times: baked.times, values: track.scale,
    });
  }

  sceneRoot.children = sceneChildren;
  return tracks;
}
