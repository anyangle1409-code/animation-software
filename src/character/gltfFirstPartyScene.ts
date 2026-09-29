import { parseHgGlb } from '../core/glbContainer';
import { HgMat4 } from '../core/linearMath';
import { HgBone, HgObject3D } from '../core/sceneGraph';
import {
  HgBufferAttribute,
  HgBufferGeometry,
  HgMesh,
  HgSkeleton,
  HgSkinnedMesh,
  HgStandardMaterial,
} from '../core/sceneSkin';
import { hgRuntimeNodeName } from '../core/gltfRuntimeNames';
import {
  readHgGltfScene,
  type HgGltfMaterial,
  type HgGltfPrimitive,
  type HgGltfSceneDocument,
} from '../core/gltfScene';

export interface HgFirstPartyPrimitiveSource {
  readonly nodeIndex: number;
  readonly meshIndex: number;
  readonly primitiveIndex: number;
  readonly targetNames: readonly string[];
}

const primitiveSources = new WeakMap<HgObject3D, HgFirstPartyPrimitiveSource>();

export function hgFirstPartyPrimitiveSource(
  object: HgObject3D,
): HgFirstPartyPrimitiveSource | null {
  return primitiveSources.get(object) ?? null;
}

const ATTRIBUTE_NAMES = {
  POSITION: 'position',
  NORMAL: 'normal',
  TEXCOORD_0: 'uv',
  COLOR_0: 'color',
  JOINTS_0: 'skinIndex',
  WEIGHTS_0: 'skinWeight',
} as const;

const attribute = (
  semantic: keyof typeof ATTRIBUTE_NAMES,
  values: readonly number[],
  components: number,
): HgBufferAttribute => {
  const typed = semantic === 'JOINTS_0'
    ? new Uint16Array(values)
    : new Float32Array(values);
  return new HgBufferAttribute(typed, components);
};

function geometryFor(
  primitive: HgGltfPrimitive,
  targetNames: readonly string[],
): HgBufferGeometry {
  const geometry = new HgBufferGeometry();
  for (const [semantic, accessor] of Object.entries(primitive.attributes)) {
    if (!accessor) continue;
    const key = semantic as keyof typeof ATTRIBUTE_NAMES;
    const name = ATTRIBUTE_NAMES[key];
    if (!name) continue;
    geometry.setAttribute(name, attribute(key, accessor.values, accessor.components));
  }

  if (primitive.indices) {
    const values = primitive.indices.componentType === 5125
      ? new Uint32Array(primitive.indices.values)
      : new Uint16Array(primitive.indices.values);
    geometry.setIndex(new HgBufferAttribute(values, 1));
  }

  const positions: HgBufferAttribute[] = [];
  const normals: HgBufferAttribute[] = [];
  primitive.targets.forEach((target, index) => {
    if (target.POSITION) {
      const value = new HgBufferAttribute(new Float32Array(target.POSITION.values), 3);
      value.name = targetNames[index] ?? String(index);
      positions.push(value);
    }
    if (target.NORMAL) {
      const value = new HgBufferAttribute(new Float32Array(target.NORMAL.values), 3);
      value.name = targetNames[index] ?? String(index);
      normals.push(value);
    }
  });
  if (positions.length) geometry.morphAttributes.position = positions;
  if (normals.length) geometry.morphAttributes.normal = normals;
  if (primitive.targets.length) geometry.morphTargetsRelative = true;
  if (!geometry.getAttribute('normal')) geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return geometry;
}

function targetNames(extras: unknown, count: number): string[] {
  if (!extras || typeof extras !== 'object' || Array.isArray(extras)) return [];
  const raw = (extras as Record<string, unknown>).targetNames;
  if (!Array.isArray(raw) || raw.length !== count || !raw.every((entry) => typeof entry === 'string')) {
    return [];
  }
  return raw as string[];
}

function materialFor(
  definition: HgGltfMaterial | null,
  hasVertexColours: boolean,
): HgStandardMaterial {
  const material = new HgStandardMaterial({ vertexColors: hasVertexColours });
  if (!definition) return material;
  material.name = definition.name;
  material.color.setRGB(
    definition.baseColorFactor[0],
    definition.baseColorFactor[1],
    definition.baseColorFactor[2],
  );
  material.opacity = definition.baseColorFactor[3];
  material.transparent = definition.baseColorFactor[3] < 1;
  material.metalness = definition.metallicFactor;
  material.roughness = definition.roughnessFactor;
  material.vertexColors = hasVertexColours;
  material.side = definition.doubleSided ? 2 : 0;
  material.emissive.setRGB(
    definition.emissiveFactor[0],
    definition.emissiveFactor[1],
    definition.emissiveFactor[2],
  );
  return material;
}

function extrasInto(object: HgObject3D, extras: unknown): void {
  if (extras && typeof extras === 'object' && !Array.isArray(extras)) {
    Object.assign(object.userData, extras);
  }
}

function applyNodeTransform(
  object: HgObject3D,
  node: HgGltfSceneDocument['nodes'][number],
): void {
  if (node.matrix) {
    object.matrix.fromArray(node.matrix);
    object.matrix.decompose(object.position, object.quaternion, object.scale);
    object.matrixWorldNeedsUpdate = true;
    return;
  }
  object.position.set(node.translation![0], node.translation![1], node.translation![2]);
  object.quaternion.set(node.rotation![0], node.rotation![1], node.rotation![2], node.rotation![3]);
  object.scale.set(node.scale![0], node.scale![1], node.scale![2]);
  object.matrixWorldNeedsUpdate = true;
}

function inverseMatrices(
  values: readonly number[] | undefined,
  count: number,
): HgMat4[] | undefined {
  if (!values) return undefined;
  return Array.from({ length: count }, (_, index) =>
    new HgMat4().fromArray(values, index * 16));
}

/**
 * Renderer-independent GLB scene materialiser.
 *
 * Parsing/accessor/material decoding is already first-party. This converts the
 * decoded document into Home Gym PT scene, geometry, morph and skin objects.
 * Texture byte upload is deliberately a later WebGL concern; material factors
 * and all authored geometry/skin data are retained here.
 */
export async function loadHgFirstPartyScene(
  input: ArrayBuffer | Uint8Array,
): Promise<HgObject3D> {
  const decoded = readHgGltfScene(parseHgGlb(input));
  const jointNodes = new Set(decoded.skins.flatMap((skin) => skin.joints));
  const namesUsed = new Map<string, number>();
  const nodes = decoded.nodes.map((node) => {
    const object = jointNodes.has(node.index) ? new HgBone() : new HgObject3D();
    object.name = hgRuntimeNodeName(node.name, namesUsed);
    applyNodeTransform(object, node);
    extrasInto(object, node.extras);
    return object;
  });

  decoded.nodes.forEach((node) => {
    for (const child of node.children) nodes[node.index].add(nodes[child]);
  });

  const root = new HgObject3D();
  const sceneDefinition = decoded.defaultScene === null
    ? decoded.scenes[0] ?? null
    : decoded.scenes[decoded.defaultScene] ?? null;
  root.name = sceneDefinition?.name || 'Scene';
  if (sceneDefinition) extrasInto(root, sceneDefinition.extras);

  if (sceneDefinition) {
    for (const node of sceneDefinition.nodes) root.add(nodes[node]);
  } else {
    const children = new Set(decoded.nodes.flatMap((node) => node.children));
    decoded.nodes.forEach((node) => {
      if (!children.has(node.index)) root.add(nodes[node.index]);
    });
  }

  const pending: Array<{ mesh: HgSkinnedMesh; skinIndex: number }> = [];
  for (const node of decoded.nodes) {
    if (node.mesh === null) continue;
    const meshDefinition = decoded.meshes[node.mesh];
    const count = Math.max(
      0,
      ...meshDefinition.primitives.map((primitive) => primitive.targets.length),
    );
    const names = targetNames(meshDefinition.extras, count);
    const weights = node.weights ?? meshDefinition.weights ?? [];

    for (let primitiveIndex = 0; primitiveIndex < meshDefinition.primitives.length; primitiveIndex += 1) {
      const primitive = meshDefinition.primitives[primitiveIndex];
      const geometry = geometryFor(primitive, names);
      const materialDefinition = primitive.material === null
        ? null
        : decoded.materials[primitive.material];
      const material = materialFor(
        materialDefinition,
        Boolean(primitive.attributes.COLOR_0),
      );
      const mesh = node.skin === null
        ? new HgMesh(geometry, material)
        : new HgSkinnedMesh(geometry, material);

      const baseName = meshDefinition.name || node.name || `mesh_${node.index}`;
      mesh.name = meshDefinition.primitives.length === 1
        ? baseName
        : `${baseName}_${primitiveIndex}`;
      primitiveSources.set(mesh, {
        nodeIndex: node.index,
        meshIndex: meshDefinition.index,
        primitiveIndex,
        targetNames: [...names],
      });

      if (nodes[node.index].name === mesh.name) {
        nodes[node.index].name = `${mesh.name}__node`;
      }
      extrasInto(mesh, meshDefinition.extras);
      nodes[node.index].add(mesh);

      if (mesh instanceof HgSkinnedMesh) {
        mesh.updateMorphTargets();
        for (let index = 0; index < Math.min(weights.length, mesh.morphTargetInfluences?.length ?? 0); index += 1) {
          mesh.morphTargetInfluences![index] = weights[index];
        }
        if (node.skin !== null) pending.push({ mesh, skinIndex: node.skin });
      }
    }
  }

  root.updateMatrixWorld(true);
  for (const { mesh, skinIndex } of pending) {
    const skin = decoded.skins[skinIndex];
    const bones = skin.joints.map((joint) => {
      const bone = nodes[joint];
      if (!(bone instanceof HgBone)) {
        throw new Error('Skin joint does not reference a first-party bone node');
      }
      return bone;
    });
    const inverses = inverseMatrices(skin.inverseBindMatrices?.values, bones.length);
    mesh.bind(new HgSkeleton(bones, inverses), mesh.matrixWorld);
  }
  root.updateMatrixWorld(true);
  return root;
}
