import { HgQuat } from '../core/linearMath';
import type { HgAnimationTrackInput } from '../core/gltfAnimation';
import type { HgGltfBuilder } from '../core/gltfBuilder';
import type { EquipmentInstance } from '../equipment/types';
import { equipmentParts, MATERIALS, type Part } from '../equipment/geometry';
import type { BakedClipData } from './clipData';

export interface EquipmentPrimitiveData {
  positions: number[];
  normals: number[];
  uvs: number[];
  indices: number[];
}

type Point3 = [number, number, number];

const pushVertex = (
  mesh: EquipmentPrimitiveData,
  point: Point3,
  normal: Point3,
  uv: [number, number],
): number => {
  const index = mesh.positions.length / 3;
  mesh.positions.push(point[0], point[1], point[2]);
  mesh.normals.push(normal[0], normal[1], normal[2]);
  mesh.uvs.push(uv[0], uv[1]);
  return index;
};

const emptyPrimitive = (): EquipmentPrimitiveData => ({
  positions: [],
  normals: [],
  uvs: [],
  indices: [],
});

const add3 = (a: Point3, b: Point3): Point3 => [
  a[0] + b[0],
  a[1] + b[1],
  a[2] + b[2],
];

const scale3 = (a: Point3, scale: number): Point3 => [
  a[0] * scale,
  a[1] * scale,
  a[2] * scale,
];

const boxPrimitive = (size: [number, number, number]): EquipmentPrimitiveData => {
  const mesh = emptyPrimitive();
  const half: Point3 = [size[0] / 2, size[1] / 2, size[2] / 2];

  const face = (center: Point3, u: Point3, v: Point3, normal: Point3) => {
    const start = mesh.positions.length / 3;
    const corners: Point3[] = [
      add3(add3(center, scale3(u, -1)), scale3(v, -1)),
      add3(add3(center, u), scale3(v, -1)),
      add3(add3(center, u), v),
      add3(add3(center, scale3(u, -1)), v),
    ];
    const uvs: [number, number][] = [[0, 0], [1, 0], [1, 1], [0, 1]];
    corners.forEach((corner, index) => pushVertex(mesh, corner, normal, uvs[index]));
    mesh.indices.push(
      start, start + 1, start + 2,
      start, start + 2, start + 3,
    );
  };

  face([half[0], 0, 0], [0, half[1], 0], [0, 0, half[2]], [1, 0, 0]);
  face([-half[0], 0, 0], [0, half[1], 0], [0, 0, -half[2]], [-1, 0, 0]);
  face([0, half[1], 0], [0, 0, half[2]], [half[0], 0, 0], [0, 1, 0]);
  face([0, -half[1], 0], [0, 0, half[2]], [-half[0], 0, 0], [0, -1, 0]);
  face([0, 0, half[2]], [half[0], 0, 0], [0, half[1], 0], [0, 0, 1]);
  face([0, 0, -half[2]], [half[0], 0, 0], [0, -half[1], 0], [0, 0, -1]);
  return mesh;
};

const cylinderPrimitive = (
  radiusBottom: number,
  radiusTop: number,
  length: number,
  segments: number,
): EquipmentPrimitiveData => {
  const mesh = emptyPrimitive();
  const radialSegments = Math.max(3, Math.floor(segments));
  const half = length / 2;
  const slope = length === 0 ? 0 : (radiusBottom - radiusTop) / length;
  const normalScale = 1 / Math.hypot(1, slope);

  for (let segment = 0; segment <= radialSegments; segment += 1) {
    const u = segment / radialSegments;
    const angle = u * Math.PI * 2;
    const cosine = Math.cos(angle);
    const sine = Math.sin(angle);
    const normal: Point3 = [
      cosine * normalScale,
      slope * normalScale,
      sine * normalScale,
    ];
    pushVertex(
      mesh,
      [radiusBottom * cosine, -half, radiusBottom * sine],
      normal,
      [u, 0],
    );
    pushVertex(
      mesh,
      [radiusTop * cosine, half, radiusTop * sine],
      normal,
      [u, 1],
    );
  }

  for (let segment = 0; segment < radialSegments; segment += 1) {
    const bottom = segment * 2;
    const top = bottom + 1;
    const nextBottom = bottom + 2;
    const nextTop = bottom + 3;
    mesh.indices.push(
      bottom, top, nextBottom,
      top, nextTop, nextBottom,
    );
  }

  const cap = (y: number, radius: number, normalY: number) => {
    const center = pushVertex(mesh, [0, y, 0], [0, normalY, 0], [0.5, 0.5]);
    const ringStart = mesh.positions.length / 3;
    for (let segment = 0; segment <= radialSegments; segment += 1) {
      const angle = (segment / radialSegments) * Math.PI * 2;
      const cosine = Math.cos(angle);
      const sine = Math.sin(angle);
      pushVertex(
        mesh,
        [radius * cosine, y, radius * sine],
        [0, normalY, 0],
        [0.5 + cosine * 0.5, 0.5 + sine * 0.5],
      );
    }
    for (let segment = 0; segment < radialSegments; segment += 1) {
      const current = ringStart + segment;
      const next = current + 1;
      if (normalY > 0) mesh.indices.push(center, next, current);
      else mesh.indices.push(center, current, next);
    }
  };

  cap(half, radiusTop, 1);
  cap(-half, radiusBottom, -1);
  return mesh;
};

const spherePrimitive = (
  radius: number,
  widthSegments = 16,
  heightSegments = 12,
): EquipmentPrimitiveData => {
  const mesh = emptyPrimitive();
  const width = Math.max(3, Math.floor(widthSegments));
  const height = Math.max(2, Math.floor(heightSegments));

  for (let row = 0; row <= height; row += 1) {
    const v = row / height;
    const theta = v * Math.PI;
    const sinTheta = Math.sin(theta);
    const cosTheta = Math.cos(theta);
    for (let column = 0; column <= width; column += 1) {
      const u = column / width;
      const phi = u * Math.PI * 2;
      const cosine = Math.cos(phi);
      const sine = Math.sin(phi);
      const normal: Point3 = [sinTheta * cosine, cosTheta, sinTheta * sine];
      pushVertex(
        mesh,
        [radius * normal[0], radius * normal[1], radius * normal[2]],
        normal,
        [u, 1 - v],
      );
    }
  }

  const stride = width + 1;
  for (let row = 0; row < height; row += 1) {
    for (let column = 0; column < width; column += 1) {
      const a = row * stride + column;
      const b = (row + 1) * stride + column;
      const c = (row + 1) * stride + column + 1;
      const d = row * stride + column + 1;
      if (row !== 0) mesh.indices.push(a, d, b);
      if (row !== height - 1) mesh.indices.push(d, c, b);
    }
  }
  return mesh;
};

const torusPrimitive = (
  radius: number,
  tube: number,
  arc: number,
  radialSegments = 10,
  tubularSegments = 24,
): EquipmentPrimitiveData => {
  const mesh = emptyPrimitive();
  const radial = Math.max(3, Math.floor(radialSegments));
  const tubular = Math.max(3, Math.floor(tubularSegments));

  for (let row = 0; row <= radial; row += 1) {
    const v = (row / radial) * Math.PI * 2;
    const cosV = Math.cos(v);
    const sinV = Math.sin(v);
    for (let column = 0; column <= tubular; column += 1) {
      const u = (column / tubular) * arc;
      const cosU = Math.cos(u);
      const sinU = Math.sin(u);
      const ring = radius + tube * cosV;
      pushVertex(
        mesh,
        [ring * cosU, ring * sinU, tube * sinV],
        [cosV * cosU, cosV * sinU, sinV],
        [column / tubular, row / radial],
      );
    }
  }

  const stride = tubular + 1;
  for (let row = 0; row < radial; row += 1) {
    for (let column = 0; column < tubular; column += 1) {
      const a = row * stride + column;
      const b = (row + 1) * stride + column;
      const c = (row + 1) * stride + column + 1;
      const d = row * stride + column + 1;
      mesh.indices.push(a, d, b, d, c, b);
    }
  }
  return mesh;
};

export function equipmentPrimitiveData(part: Part): EquipmentPrimitiveData {
  switch (part.shape) {
    case 'box':
      return boxPrimitive(part.size);
    case 'cylinder':
      return cylinderPrimitive(
        part.radius,
        part.radiusTop ?? part.radius,
        part.length,
        part.segments ?? 16,
      );
    case 'sphere':
      return spherePrimitive(part.radius);
    case 'torus':
      return torusPrimitive(part.radius, part.tube, part.arc ?? Math.PI * 2);
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

    const parts = equipmentParts(instance.kind, instance.backAngle);

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
