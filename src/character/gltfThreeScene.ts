import {
  Bone,
  BufferAttribute,
  BufferGeometry,
  ClampToEdgeWrapping,
  Color,
  DoubleSide,
  FrontSide,
  LinearFilter,
  LinearMipmapLinearFilter,
  LinearMipmapNearestFilter,
  Matrix4,
  Mesh,
  MeshStandardMaterial,
  MirroredRepeatWrapping,
  NearestFilter,
  NearestMipmapLinearFilter,
  NearestMipmapNearestFilter,
  Object3D,
  RepeatWrapping,
  Skeleton,
  SkinnedMesh,
  SRGBColorSpace,
  Texture,
} from 'three';
import { parseHgGlb } from '../core/glbContainer';
import {
  readHgGltfScene,
  type HgGltfMaterial,
  type HgGltfPrimitive,
  type HgGltfSceneDocument,
  type HgGltfTextureInfo,
} from '../core/gltfScene';
import type {
  HgGltfSampler,
  HgImageMimeType,
} from '../core/gltfTextures';

type DecodedImage = ImageBitmap | HTMLImageElement;

const ATTRIBUTE_NAMES = {
  POSITION: 'position',
  NORMAL: 'normal',
  TEXCOORD_0: 'uv',
  COLOR_0: 'color',
  JOINTS_0: 'skinIndex',
  WEIGHTS_0: 'skinWeight',
} as const;

function extrasInto(object: Object3D, extras: unknown): void {
  if (extras && typeof extras === 'object' && !Array.isArray(extras)) {
    Object.assign(object.userData, extras);
  }
}

const RESERVED_BINDING_CHARS = /[\[\].:\/]/g;

/**
 * Match the established glTF runtime naming contract without calling Three's
 * PropertyBinding helper: whitespace becomes underscores and characters
 * reserved by animation track syntax are removed.
 */
function runtimeNodeName(name: string, used: Map<string, number>): string {
  const sanitized = name.replace(/\s/g, '_').replace(RESERVED_BINDING_CHARS, '');
  if (!sanitized) return '';
  const seen = used.get(sanitized);
  if (seen === undefined) {
    used.set(sanitized, 0);
    return sanitized;
  }
  const next = seen + 1;
  used.set(sanitized, next);
  return `${sanitized}_${next}`;
}

function geometryFor(primitive: HgGltfPrimitive, targetNames: string[]): BufferGeometry {
  const geometry = new BufferGeometry();

  for (const [semantic, accessor] of Object.entries(primitive.attributes)) {
    if (!accessor) continue;
    const name = ATTRIBUTE_NAMES[semantic as keyof typeof ATTRIBUTE_NAMES];
    const values = semantic === 'JOINTS_0'
      ? new Uint16Array(accessor.values)
      : new Float32Array(accessor.values);
    geometry.setAttribute(name, new BufferAttribute(values, accessor.components));
  }

  if (primitive.indices) {
    const values = primitive.indices.componentType === 5125
      ? new Uint32Array(primitive.indices.values)
      : new Uint16Array(primitive.indices.values);
    geometry.setIndex(new BufferAttribute(values, 1));
  }

  const morphPositions: BufferAttribute[] = [];
  const morphNormals: BufferAttribute[] = [];
  primitive.targets.forEach((target, index) => {
    if (target.POSITION) {
      const attribute = new BufferAttribute(new Float32Array(target.POSITION.values), 3);
      attribute.name = targetNames[index] ?? String(index);
      morphPositions.push(attribute);
    }
    if (target.NORMAL) {
      const attribute = new BufferAttribute(new Float32Array(target.NORMAL.values), 3);
      attribute.name = targetNames[index] ?? String(index);
      morphNormals.push(attribute);
    }
  });
  if (morphPositions.length) geometry.morphAttributes.position = morphPositions;
  if (morphNormals.length) geometry.morphAttributes.normal = morphNormals;
  if (primitive.targets.length) geometry.morphTargetsRelative = true;

  if (!geometry.getAttribute('normal')) geometry.computeVertexNormals();
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

async function decodeImage(bytes: Uint8Array, mimeType: HgImageMimeType): Promise<DecodedImage> {
  const blob = new Blob([new Uint8Array(bytes)], { type: mimeType });
  if (typeof createImageBitmap === 'function') {
    return createImageBitmap(blob);
  }

  if (
    typeof Image !== 'undefined' &&
    typeof URL !== 'undefined' &&
    typeof URL.createObjectURL === 'function'
  ) {
    const url = URL.createObjectURL(blob);
    try {
      return await new Promise<HTMLImageElement>((resolve, reject) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.onerror = () => reject(new Error(`Failed to decode embedded ${mimeType} image`));
        image.src = url;
      });
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  throw new Error('Browser-native image decoding is unavailable for this textured GLB');
}

function wrap(value: HgGltfSampler['wrapS']) {
  switch (value) {
    case 33071: return ClampToEdgeWrapping;
    case 33648: return MirroredRepeatWrapping;
    case 10497: return RepeatWrapping;
  }
}

function magFilter(value: HgGltfSampler['magFilter']) {
  switch (value) {
    case 9728: return NearestFilter;
    case 9729:
    case null:
      return LinearFilter;
  }
}

function minFilter(value: HgGltfSampler['minFilter']) {
  switch (value) {
    case 9728: return NearestFilter;
    case 9729: return LinearFilter;
    case 9984: return NearestMipmapNearestFilter;
    case 9985: return LinearMipmapNearestFilter;
    case 9986: return NearestMipmapLinearFilter;
    case 9987:
    case null:
      return LinearMipmapLinearFilter;
  }
}

class TextureCache {
  private readonly images = new Map<number, Promise<DecodedImage>>();
  private readonly textures = new Map<string, Promise<Texture>>();

  constructor(private readonly scene: HgGltfSceneDocument) {}

  async texture(info: HgGltfTextureInfo, srgb: boolean): Promise<Texture> {
    const key = `${info.index}:${srgb ? 'srgb' : 'linear'}`;
    let promise = this.textures.get(key);
    if (!promise) {
      promise = this.build(info.index, srgb);
      this.textures.set(key, promise);
    }
    return promise;
  }

  private async build(index: number, srgb: boolean): Promise<Texture> {
    const definition = this.scene.textureData.textures[index];
    if (!definition) throw new Error(`Missing decoded texture ${index}`);
    const imageDefinition = this.scene.textureData.images[definition.source];
    if (!imageDefinition) throw new Error(`Missing decoded image ${definition.source}`);

    let image = this.images.get(definition.source);
    if (!image) {
      image = decodeImage(imageDefinition.bytes, imageDefinition.mimeType);
      this.images.set(definition.source, image);
    }

    const texture = new Texture(await image);
    texture.name = definition.name || imageDefinition.name;
    texture.flipY = false;
    const sampler = definition.sampler === null
      ? null
      : this.scene.textureData.samplers[definition.sampler];
    texture.wrapS = wrap(sampler?.wrapS ?? 10497);
    texture.wrapT = wrap(sampler?.wrapT ?? 10497);
    texture.magFilter = magFilter(sampler?.magFilter ?? null);
    texture.minFilter = minFilter(sampler?.minFilter ?? null);
    if (srgb) texture.colorSpace = SRGBColorSpace;
    texture.needsUpdate = true;
    return texture;
  }
}

async function materialFor(
  definition: HgGltfMaterial | null,
  hasVertexColors: boolean,
  textures: TextureCache,
): Promise<MeshStandardMaterial> {
  const material = new MeshStandardMaterial();
  if (!definition) {
    material.vertexColors = hasVertexColors;
    return material;
  }

  material.name = definition.name;
  material.color.copy(new Color().setRGB(
    definition.baseColorFactor[0],
    definition.baseColorFactor[1],
    definition.baseColorFactor[2],
  ));
  material.metalness = definition.metallicFactor;
  material.roughness = definition.roughnessFactor;
  material.side = definition.doubleSided ? DoubleSide : FrontSide;
  material.vertexColors = hasVertexColors;
  material.emissive.copy(new Color().setRGB(
    definition.emissiveFactor[0],
    definition.emissiveFactor[1],
    definition.emissiveFactor[2],
  ));

  if (definition.baseColorTexture) {
    material.map = await textures.texture(definition.baseColorTexture, true);
  }
  if (definition.metallicRoughnessTexture) {
    const map = await textures.texture(definition.metallicRoughnessTexture, false);
    material.metalnessMap = map;
    material.roughnessMap = map;
  }
  if (definition.normalTexture) {
    material.normalMap = await textures.texture(definition.normalTexture, false);
    material.normalScale.setScalar(definition.normalTexture.scale);
  }
  if (definition.occlusionTexture) {
    material.aoMap = await textures.texture(definition.occlusionTexture, false);
    material.aoMapIntensity = definition.occlusionTexture.strength;
  }
  if (definition.emissiveTexture) {
    material.emissiveMap = await textures.texture(definition.emissiveTexture, true);
  }
  return material;
}

function applyNodeTransform(
  object: Object3D,
  node: HgGltfSceneDocument['nodes'][number],
): void {
  if (node.matrix) {
    object.matrix.fromArray(node.matrix);
    object.matrix.decompose(object.position, object.quaternion, object.scale);
    return;
  }
  object.position.fromArray(node.translation!);
  object.quaternion.fromArray(node.rotation!);
  object.scale.fromArray(node.scale!);
}

function inverseMatrices(
  values: readonly number[] | undefined,
  count: number,
): Matrix4[] | undefined {
  if (!values) return undefined;
  return Array.from({ length: count }, (_, index) =>
    new Matrix4().fromArray(values, index * 16));
}

/**
 * Temporary renderer compatibility adapter.
 *
 * GLB parsing, accessor validation, mesh/skin/morph/material decoding and
 * texture extraction are project-owned before this boundary. This file only
 * materializes the decoded data into Three scene objects while the renderer and
 * skin runtime are still being migrated.
 */
export async function loadHgThreeScene(
  input: ArrayBuffer | Uint8Array,
): Promise<Object3D> {
  const decoded = readHgGltfScene(parseHgGlb(input));
  const jointNodes = new Set(decoded.skins.flatMap((skin) => skin.joints));
  const nodeNamesUsed = new Map<string, number>();
  const nodes = decoded.nodes.map((node) => {
    const object = jointNodes.has(node.index) ? new Bone() : new Object3D();
    object.name = runtimeNodeName(node.name, nodeNamesUsed);
    applyNodeTransform(object, node);
    extrasInto(object, node.extras);
    return object;
  });

  decoded.nodes.forEach((node) => {
    for (const child of node.children) nodes[node.index].add(nodes[child]);
  });

  const root = new Object3D();
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

  const textureCache = new TextureCache(decoded);
  const pending: Array<{ mesh: SkinnedMesh; skinIndex: number }> = [];

  for (const node of decoded.nodes) {
    if (node.mesh === null) continue;
    const meshDefinition = decoded.meshes[node.mesh];
    const names = targetNames(meshDefinition.extras, meshDefinition.primitives[0].targets.length);
    const weights = node.weights ?? meshDefinition.weights ?? [];

    for (let primitiveIndex = 0; primitiveIndex < meshDefinition.primitives.length; primitiveIndex += 1) {
      const primitive = meshDefinition.primitives[primitiveIndex];
      const geometry = geometryFor(primitive, names);
      const materialDefinition = primitive.material === null
        ? null
        : decoded.materials[primitive.material];
      const material = await materialFor(
        materialDefinition,
        Boolean(primitive.attributes.COLOR_0),
        textureCache,
      );

      const mesh = node.skin === null
        ? new Mesh(geometry, material)
        : new SkinnedMesh(geometry, material);
      const baseName = meshDefinition.name || node.name || `mesh_${node.index}`;
      mesh.name = meshDefinition.primitives.length === 1
        ? baseName
        : `${baseName}_${primitiveIndex}`;
      // GLTFLoader materializes a single mesh node as the mesh itself. This
      // temporary adapter keeps a lightweight node wrapper for extras and
      // hierarchy, so disambiguate an identical wrapper/mesh name. Otherwise
      // Three PropertyBinding finds the wrapper first and morph animation
      // tracks target an Object3D with no morphTargetInfluences.
      if (nodes[node.index].name === mesh.name) {
        nodes[node.index].name = `${mesh.name}__node`;
      }
      extrasInto(mesh, meshDefinition.extras);
      nodes[node.index].add(mesh);

      if (primitive.targets.length) {
        mesh.updateMorphTargets();
        for (let index = 0; index < Math.min(weights.length, mesh.morphTargetInfluences?.length ?? 0); index += 1) {
          mesh.morphTargetInfluences![index] = weights[index];
        }
      }

      if (mesh instanceof SkinnedMesh && node.skin !== null) {
        pending.push({ mesh, skinIndex: node.skin });
      }
    }
  }

  root.updateMatrixWorld(true);
  for (const { mesh, skinIndex } of pending) {
    const skin = decoded.skins[skinIndex];
    const bones = skin.joints.map((joint) => nodes[joint] as Bone);
    const inverses = inverseMatrices(skin.inverseBindMatrices?.values, bones.length);
    const skeleton = inverses ? new Skeleton(bones, inverses) : new Skeleton(bones);
    mesh.bind(skeleton, mesh.matrixWorld);
  }
  root.updateMatrixWorld(true);
  return root;
}

