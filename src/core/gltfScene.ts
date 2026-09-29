import type { HgGlbDocument } from './glbContainer';
import { readHgAccessor, type HgAccessorData } from './gltfAccessors';
import { readHgGltfTextures, type HgGltfTextureDocument } from './gltfTextures';

type JsonObject = Record<string, unknown>;

export type HgVertexSemantic =
  | 'POSITION'
  | 'NORMAL'
  | 'TEXCOORD_0'
  | 'COLOR_0'
  | 'JOINTS_0'
  | 'WEIGHTS_0';

export type HgMorphSemantic = 'POSITION' | 'NORMAL';

export interface HgGltfPrimitive {
  readonly attributes: Partial<Record<HgVertexSemantic, HgAccessorData>>;
  readonly targets: Array<Partial<Record<HgMorphSemantic, HgAccessorData>>>;
  readonly indices: HgAccessorData | null;
  readonly material: number | null;
  readonly mode: 4;
}

export interface HgGltfMesh {
  readonly index: number;
  readonly name: string;
  readonly primitives: HgGltfPrimitive[];
  readonly weights: number[] | null;
  readonly extras: unknown;
}

export interface HgGltfSkin {
  readonly index: number;
  readonly name: string;
  readonly joints: number[];
  readonly skeleton: number | null;
  readonly inverseBindMatrices: HgAccessorData | null;
}

export interface HgGltfNode {
  readonly index: number;
  readonly name: string;
  readonly children: number[];
  readonly mesh: number | null;
  readonly skin: number | null;
  readonly matrix: number[] | null;
  readonly translation: [number, number, number] | null;
  readonly rotation: [number, number, number, number] | null;
  readonly scale: [number, number, number] | null;
  readonly weights: number[] | null;
  readonly extras: unknown;
}

export interface HgGltfTextureInfo {
  readonly index: number;
  readonly texCoord: 0;
}

export interface HgGltfNormalTextureInfo extends HgGltfTextureInfo {
  readonly scale: number;
}

export interface HgGltfOcclusionTextureInfo extends HgGltfTextureInfo {
  readonly strength: number;
}

export interface HgGltfMaterial {
  readonly index: number;
  readonly name: string;
  readonly baseColorFactor: [number, number, number, number];
  readonly baseColorTexture: HgGltfTextureInfo | null;
  readonly metallicFactor: number;
  readonly roughnessFactor: number;
  readonly metallicRoughnessTexture: HgGltfTextureInfo | null;
  readonly normalTexture: HgGltfNormalTextureInfo | null;
  readonly occlusionTexture: HgGltfOcclusionTextureInfo | null;
  readonly emissiveTexture: HgGltfTextureInfo | null;
  readonly emissiveFactor: [number, number, number];
  readonly doubleSided: boolean;
}

export interface HgGltfSceneDefinition {
  readonly index: number;
  readonly name: string;
  readonly nodes: number[];
  readonly extras: unknown;
}

export interface HgGltfSceneDocument {
  readonly nodes: HgGltfNode[];
  readonly meshes: HgGltfMesh[];
  readonly skins: HgGltfSkin[];
  readonly materials: HgGltfMaterial[];
  readonly textureData: HgGltfTextureDocument;
  readonly scenes: HgGltfSceneDefinition[];
  readonly defaultScene: number | null;
}

const SUPPORTED_ATTRIBUTES = new Set<HgVertexSemantic>([
  'POSITION',
  'NORMAL',
  'TEXCOORD_0',
  'COLOR_0',
  'JOINTS_0',
  'WEIGHTS_0',
]);

function object(value: unknown, label: string): JsonObject {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be an object`);
  }
  return value as JsonObject;
}

function objectArray(value: unknown, label: string): JsonObject[] {
  if (value === undefined) return [];
  if (!Array.isArray(value)) throw new Error(`${label} must be an array`);
  return value.map((entry, index) => object(entry, `${label}[${index}]`));
}

function nonNegativeInteger(value: unknown, label: string): number {
  if (!Number.isInteger(value) || (value as number) < 0) {
    throw new Error(`${label} must be a non-negative integer`);
  }
  return value as number;
}

function optionalIndex(value: unknown, label: string): number | null {
  return value === undefined ? null : nonNegativeInteger(value, label);
}

function integerArray(value: unknown, label: string): number[] {
  if (!Array.isArray(value)) throw new Error(`${label} must be an array`);
  return value.map((entry, index) => nonNegativeInteger(entry, `${label}[${index}]`));
}

function finite(value: unknown, label: string): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new Error(`${label} must be finite`);
  }
  return value;
}

function tuple(value: unknown, length: number, label: string): number[] {
  if (!Array.isArray(value) || value.length !== length) {
    throw new Error(`${label} must contain ${length} numbers`);
  }
  return value.map((entry, index) => finite(entry, `${label}[${index}]`));
}

function nameOf(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function readAttribute(
  document: HgGlbDocument,
  semantic: HgVertexSemantic,
  index: number,
): HgAccessorData {
  const accessor = readHgAccessor(document, index);
  const fail = (reason: string): never => {
    throw new Error(`${semantic} accessor ${index} ${reason}`);
  };

  switch (semantic) {
    case 'POSITION':
    case 'NORMAL':
      if (accessor.type !== 'VEC3' || accessor.componentType !== 5126 || accessor.normalized) {
        fail('must be a non-normalized FLOAT VEC3');
      }
      break;
    case 'TEXCOORD_0':
      if (accessor.type !== 'VEC2') fail('must be VEC2');
      if (
        accessor.componentType !== 5126 &&
        !((accessor.componentType === 5121 || accessor.componentType === 5123) && accessor.normalized)
      ) fail('must be FLOAT or normalized UNSIGNED_BYTE/UNSIGNED_SHORT');
      break;
    case 'COLOR_0':
      if (accessor.type !== 'VEC3' && accessor.type !== 'VEC4') fail('must be VEC3 or VEC4');
      if (
        accessor.componentType !== 5126 &&
        !((accessor.componentType === 5121 || accessor.componentType === 5123) && accessor.normalized)
      ) fail('must be FLOAT or normalized UNSIGNED_BYTE/UNSIGNED_SHORT');
      break;
    case 'JOINTS_0':
      if (
        accessor.type !== 'VEC4' ||
        (accessor.componentType !== 5121 && accessor.componentType !== 5123) ||
        accessor.normalized
      ) fail('must be a non-normalized UNSIGNED_BYTE/UNSIGNED_SHORT VEC4');
      break;
    case 'WEIGHTS_0':
      if (accessor.type !== 'VEC4') fail('must be VEC4');
      if (
        accessor.componentType !== 5126 &&
        !((accessor.componentType === 5121 || accessor.componentType === 5123) && accessor.normalized)
      ) fail('must be FLOAT or normalized UNSIGNED_BYTE/UNSIGNED_SHORT');
      break;
  }
  return accessor;
}

function readPrimitive(document: HgGlbDocument, value: JsonObject, label: string): HgGltfPrimitive {
  if (value.extensions !== undefined) throw new Error(`${label} extensions are not supported`);

  const mode = value.mode === undefined ? 4 : nonNegativeInteger(value.mode, `${label}.mode`);
  if (mode !== 4) throw new Error(`${label} must use TRIANGLES mode 4`);

  const attributesObject = object(value.attributes, `${label}.attributes`);
  const attributes: Partial<Record<HgVertexSemantic, HgAccessorData>> = {};
  let vertexCount: number | null = null;
  for (const [key, rawIndex] of Object.entries(attributesObject)) {
    if (!SUPPORTED_ATTRIBUTES.has(key as HgVertexSemantic)) {
      throw new Error(`${label} attribute ${key} is not supported`);
    }
    const semantic = key as HgVertexSemantic;
    const accessor = readAttribute(
      document,
      semantic,
      nonNegativeInteger(rawIndex, `${label}.attributes.${key}`),
    );
    if (vertexCount === null) vertexCount = accessor.count;
    else if (accessor.count !== vertexCount) throw new Error(`${label} attribute counts do not match`);
    attributes[semantic] = accessor;
  }
  if (!attributes.POSITION) throw new Error(`${label} has no POSITION attribute`);

  const targets = value.targets === undefined
    ? []
    : objectArray(value.targets, `${label}.targets`).map((target, targetIndex) => {
        const decoded: Partial<Record<HgMorphSemantic, HgAccessorData>> = {};
        for (const [key, rawIndex] of Object.entries(target)) {
          if (key !== 'POSITION' && key !== 'NORMAL') {
            throw new Error(`${label}.targets[${targetIndex}] attribute ${key} is not supported`);
          }
          const semantic = key as HgMorphSemantic;
          const accessor = readAttribute(
            document,
            semantic,
            nonNegativeInteger(rawIndex, `${label}.targets[${targetIndex}].${key}`),
          );
          if (accessor.count !== vertexCount) {
            throw new Error(`${label}.targets[${targetIndex}] attribute count does not match base mesh`);
          }
          decoded[semantic] = accessor;
        }
        if (!Object.keys(decoded).length) {
          throw new Error(`${label}.targets[${targetIndex}] has no supported attributes`);
        }
        return decoded;
      });

  let indices: HgAccessorData | null = null;
  if (value.indices !== undefined) {
    const index = nonNegativeInteger(value.indices, `${label}.indices`);
    indices = readHgAccessor(document, index);
    if (
      indices.type !== 'SCALAR' ||
      (indices.componentType !== 5121 && indices.componentType !== 5123 && indices.componentType !== 5125) ||
      indices.normalized
    ) throw new Error(`${label} indices must be non-normalized unsigned SCALAR values`);
  }

  return {
    attributes,
    targets,
    indices,
    material: optionalIndex(value.material, `${label}.material`),
    mode: 4,
  };
}

function readMesh(document: HgGlbDocument, value: JsonObject, index: number): HgGltfMesh {
  const primitives = objectArray(value.primitives, `meshes[${index}].primitives`).map(
    (primitive, primitiveIndex) =>
      readPrimitive(document, primitive, `meshes[${index}].primitives[${primitiveIndex}]`),
  );
  if (!primitives.length) throw new Error(`meshes[${index}] has no primitives`);

  const targetCount = primitives[0].targets.length;
  if (primitives.some((primitive) => primitive.targets.length !== targetCount)) {
    throw new Error(`meshes[${index}] primitives must expose the same morph-target count`);
  }

  const weights = value.weights === undefined
    ? null
    : tuple(value.weights, targetCount, `meshes[${index}].weights`);

  return {
    index,
    name: nameOf(value.name),
    primitives,
    weights,
    extras: value.extras ?? null,
  };
}

function readSkin(document: HgGlbDocument, value: JsonObject, index: number): HgGltfSkin {
  const joints = integerArray(value.joints, `skins[${index}].joints`);
  if (!joints.length) throw new Error(`skins[${index}] has no joints`);

  let inverseBindMatrices: HgAccessorData | null = null;
  if (value.inverseBindMatrices !== undefined) {
    const accessorIndex = nonNegativeInteger(value.inverseBindMatrices, `skins[${index}].inverseBindMatrices`);
    inverseBindMatrices = readHgAccessor(document, accessorIndex);
    if (inverseBindMatrices.type !== 'MAT4' || inverseBindMatrices.componentType !== 5126) {
      throw new Error(`skins[${index}] inverse bind matrices must be FLOAT MAT4`);
    }
    if (inverseBindMatrices.count !== joints.length) {
      throw new Error(`skins[${index}] inverse bind matrix count must match joints`);
    }
  }

  return {
    index,
    name: nameOf(value.name),
    joints,
    skeleton: optionalIndex(value.skeleton, `skins[${index}].skeleton`),
    inverseBindMatrices,
  };
}

function readNode(value: JsonObject, index: number): HgGltfNode {
  const matrix = value.matrix === undefined ? null : tuple(value.matrix, 16, `nodes[${index}].matrix`);
  const hasTrs = value.translation !== undefined || value.rotation !== undefined || value.scale !== undefined;
  if (matrix && hasTrs) throw new Error(`nodes[${index}] cannot define both matrix and TRS transforms`);

  return {
    index,
    name: nameOf(value.name),
    children: value.children === undefined ? [] : integerArray(value.children, `nodes[${index}].children`),
    mesh: optionalIndex(value.mesh, `nodes[${index}].mesh`),
    skin: optionalIndex(value.skin, `nodes[${index}].skin`),
    matrix,
    translation: matrix ? null : (value.translation === undefined ? [0, 0, 0] : tuple(value.translation, 3, `nodes[${index}].translation`)) as [number, number, number],
    rotation: matrix ? null : (value.rotation === undefined ? [0, 0, 0, 1] : tuple(value.rotation, 4, `nodes[${index}].rotation`)) as [number, number, number, number],
    scale: matrix ? null : (value.scale === undefined ? [1, 1, 1] : tuple(value.scale, 3, `nodes[${index}].scale`)) as [number, number, number],
    weights: value.weights === undefined
      ? null
      : (Array.isArray(value.weights)
          ? value.weights.map((entry, weightIndex) => finite(entry, `nodes[${index}].weights[${weightIndex}]`))
          : (() => { throw new Error(`nodes[${index}].weights must be an array`); })()),
    extras: value.extras ?? null,
  };
}

function unitFactor(value: unknown, fallback: number, label: string): number {
  if (value === undefined) return fallback;
  const result = finite(value, label);
  if (result < 0 || result > 1) throw new Error(`${label} must be in 0..1`);
  return result;
}

function textureInfo(value: unknown, label: string): HgGltfTextureInfo {
  const info = object(value, label);
  if (info.extensions !== undefined) throw new Error(`${label} extensions are not supported`);
  const texCoord = info.texCoord === undefined ? 0 : nonNegativeInteger(info.texCoord, `${label}.texCoord`);
  if (texCoord !== 0) throw new Error(`${label} only supports TEXCOORD_0`);
  return {
    index: nonNegativeInteger(info.index, `${label}.index`),
    texCoord: 0,
  };
}

function readMaterial(value: JsonObject, index: number): HgGltfMaterial {
  const label = `materials[${index}]`;
  if (value.extensions !== undefined) throw new Error(`${label} extensions are not supported`);
  if (value.alphaMode !== undefined && value.alphaMode !== 'OPAQUE') {
    throw new Error(`${label} only supports OPAQUE alpha mode`);
  }

  const pbr = value.pbrMetallicRoughness === undefined
    ? {}
    : object(value.pbrMetallicRoughness, `${label}.pbrMetallicRoughness`);

  const baseColorTexture = pbr.baseColorTexture === undefined
    ? null
    : textureInfo(pbr.baseColorTexture, `${label}.pbrMetallicRoughness.baseColorTexture`);
  const metallicRoughnessTexture = pbr.metallicRoughnessTexture === undefined
    ? null
    : textureInfo(pbr.metallicRoughnessTexture, `${label}.pbrMetallicRoughness.metallicRoughnessTexture`);

  const normalTexture = value.normalTexture === undefined
    ? null
    : (() => {
        const info = object(value.normalTexture, `${label}.normalTexture`);
        const base = textureInfo(info, `${label}.normalTexture`);
        return {
          ...base,
          scale: info.scale === undefined ? 1 : finite(info.scale, `${label}.normalTexture.scale`),
        };
      })();

  const occlusionTexture = value.occlusionTexture === undefined
    ? null
    : (() => {
        const info = object(value.occlusionTexture, `${label}.occlusionTexture`);
        const base = textureInfo(info, `${label}.occlusionTexture`);
        return {
          ...base,
          strength: unitFactor(info.strength, 1, `${label}.occlusionTexture.strength`),
        };
      })();

  const emissiveTexture = value.emissiveTexture === undefined
    ? null
    : textureInfo(value.emissiveTexture, `${label}.emissiveTexture`);

  return {
    index,
    name: nameOf(value.name),
    baseColorFactor: (pbr.baseColorFactor === undefined
      ? [1, 1, 1, 1]
      : tuple(pbr.baseColorFactor, 4, `${label}.baseColorFactor`)) as [number, number, number, number],
    baseColorTexture,
    metallicFactor: unitFactor(pbr.metallicFactor, 1, `${label}.metallicFactor`),
    roughnessFactor: unitFactor(pbr.roughnessFactor, 1, `${label}.roughnessFactor`),
    metallicRoughnessTexture,
    normalTexture,
    occlusionTexture,
    emissiveTexture,
    emissiveFactor: (value.emissiveFactor === undefined
      ? [0, 0, 0]
      : tuple(value.emissiveFactor, 3, `${label}.emissiveFactor`)) as [number, number, number],
    doubleSided: value.doubleSided === true,
  };
}

function assertReference(index: number, length: number, label: string): void {
  if (index >= length) throw new Error(`${label} references missing index ${index}`);
}

function validateReferences(scene: HgGltfSceneDocument): void {
  for (const node of scene.nodes) {
    node.children.forEach((child) => assertReference(child, scene.nodes.length, `nodes[${node.index}].children`));
    if (node.mesh !== null) {
      assertReference(node.mesh, scene.meshes.length, `nodes[${node.index}].mesh`);
      if (node.weights !== null) {
        const expected = scene.meshes[node.mesh].primitives[0].targets.length;
        if (node.weights.length !== expected) {
          throw new Error(`nodes[${node.index}].weights must match mesh morph-target count`);
        }
      }
    } else if (node.weights !== null) {
      throw new Error(`nodes[${node.index}] defines morph weights without a mesh`);
    }
    if (node.skin !== null) assertReference(node.skin, scene.skins.length, `nodes[${node.index}].skin`);
  }
  for (const mesh of scene.meshes) {
    for (const primitive of mesh.primitives) {
      if (primitive.material !== null) assertReference(primitive.material, scene.materials.length, `meshes[${mesh.index}].material`);
    }
  }
  for (const material of scene.materials) {
    const textureRefs = [
      material.baseColorTexture,
      material.metallicRoughnessTexture,
      material.normalTexture,
      material.occlusionTexture,
      material.emissiveTexture,
    ];
    for (const texture of textureRefs) {
      if (texture) {
        assertReference(texture.index, scene.textureData.textures.length, `materials[${material.index}].texture`);
      }
    }
  }
  for (const skin of scene.skins) {
    skin.joints.forEach((joint) => assertReference(joint, scene.nodes.length, `skins[${skin.index}].joints`));
    if (skin.skeleton !== null) assertReference(skin.skeleton, scene.nodes.length, `skins[${skin.index}].skeleton`);
  }
  for (const definition of scene.scenes) {
    definition.nodes.forEach((node) => assertReference(node, scene.nodes.length, `scenes[${definition.index}].nodes`));
  }
  if (scene.defaultScene !== null) assertReference(scene.defaultScene, scene.scenes.length, 'scene');
}

export function readHgGltfScene(document: HgGlbDocument): HgGltfSceneDocument {
  const asset = object(document.json.asset, 'asset');
  if (asset.version !== '2.0') throw new Error('Only glTF 2.0 is supported');

  if (document.json.extensionsRequired !== undefined) {
    if (!Array.isArray(document.json.extensionsRequired)) throw new Error('extensionsRequired must be an array');
    if (document.json.extensionsRequired.length) throw new Error('Required glTF extensions are not supported');
  }

  const textureData = readHgGltfTextures(document);
  const materials = objectArray(document.json.materials, 'materials').map(readMaterial);
  const meshes = objectArray(document.json.meshes, 'meshes').map((mesh, index) => readMesh(document, mesh, index));
  const skins = objectArray(document.json.skins, 'skins').map((skin, index) => readSkin(document, skin, index));
  const nodes = objectArray(document.json.nodes, 'nodes').map(readNode);
  const scenes = objectArray(document.json.scenes, 'scenes').map((value, index) => ({
    index,
    name: nameOf(value.name),
    nodes: value.nodes === undefined ? [] : integerArray(value.nodes, `scenes[${index}].nodes`),
    extras: value.extras ?? null,
  }));
  const defaultScene = optionalIndex(document.json.scene, 'scene');

  const decoded: HgGltfSceneDocument = { nodes, meshes, skins, materials, textureData, scenes, defaultScene };
  validateReferences(decoded);
  return decoded;
}
