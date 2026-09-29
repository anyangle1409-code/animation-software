import { describe, expect, it } from 'vitest';
import { parseHgGlb } from './glbContainer';
import { HgGltfBuilder } from './gltfBuilder';
import { readHgGltfScene } from './gltfScene';

function builtScene() {
  const builder = new HgGltfBuilder();
  const position = builder.addAccessor([0, 0, 0, 1, 0, 0, 0, 1, 0], { type: 'VEC3', componentType: 5126, target: 34962 });
  const normal = builder.addAccessor([0, 0, 1, 0, 0, 1, 0, 0, 1], { type: 'VEC3', componentType: 5126, target: 34962 });
  const joints = builder.addAccessor([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], { type: 'VEC4', componentType: 5121, target: 34962 });
  const weights = builder.addAccessor([1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0], { type: 'VEC4', componentType: 5126, target: 34962 });
  const morphPosition = builder.addAccessor([0, 0, 0, 0, 0.1, 0, 0, 0, 0], { type: 'VEC3', componentType: 5126, target: 34962 });
  const indices = builder.addAccessor([0, 1, 2], { type: 'SCALAR', componentType: 5123, target: 34963 });
  const inverseBind = builder.addAccessor(
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    { type: 'MAT4', componentType: 5126 },
  );

  builder.json.materials = [{
    name: 'body',
    pbrMetallicRoughness: { baseColorFactor: [0.7, 0.55, 0.42, 1], metallicFactor: 0, roughnessFactor: 0.8 },
  }];
  builder.json.meshes = [{
    name: 'body_mesh',
    primitives: [{
      attributes: { POSITION: position, NORMAL: normal, JOINTS_0: joints, WEIGHTS_0: weights },
      targets: [{ POSITION: morphPosition }],
      indices,
      material: 0,
    }],
  }];
  builder.json.skins = [{ name: 'body_skin', joints: [0], skeleton: 0, inverseBindMatrices: inverseBind }];
  builder.json.nodes = [
    { name: 'root', children: [1] },
    { name: 'body', mesh: 0, skin: 0, translation: [0, 1, 0] },
  ];
  builder.json.scenes = [{ name: 'main', nodes: [0] }];
  builder.json.scene = 0;
  return parseHgGlb(builder.toGlb());
}

describe('first-party glTF scene decoder', () => {
  it('decodes the project mesh, skin, node hierarchy and material subset', () => {
    const decoded = readHgGltfScene(builtScene());
    expect(decoded.defaultScene).toBe(0);
    expect(decoded.scenes[0]).toEqual({ index: 0, name: 'main', nodes: [0] });
    expect(decoded.nodes[0].children).toEqual([1]);
    expect(decoded.nodes[1].translation).toEqual([0, 1, 0]);
    expect(decoded.nodes[1].rotation).toEqual([0, 0, 0, 1]);
    expect(decoded.nodes[1].scale).toEqual([1, 1, 1]);

    const primitive = decoded.meshes[0].primitives[0];
    expect(primitive.attributes.POSITION?.values).toEqual([0, 0, 0, 1, 0, 0, 0, 1, 0]);
    expect(primitive.attributes.JOINTS_0?.componentType).toBe(5121);
    expect(primitive.targets).toHaveLength(1);
    expect(primitive.targets[0].POSITION?.values).toEqual(
      Array.from(new Float32Array([0, 0, 0, 0, 0.1, 0, 0, 0, 0])),
    );
    expect(primitive.indices?.values).toEqual([0, 1, 2]);
    expect(primitive.material).toBe(0);

    expect(decoded.skins[0].joints).toEqual([0]);
    expect(decoded.skins[0].inverseBindMatrices?.type).toBe('MAT4');
    expect(decoded.skins[0].inverseBindMatrices?.values).toHaveLength(16);
    expect(decoded.materials[0]).toEqual({
      index: 0,
      name: 'body',
      baseColorFactor: [0.7, 0.55, 0.42, 1],
      metallicFactor: 0,
      roughnessFactor: 0.8,
      doubleSided: false,
    });
  });

  it('preserves an authored node matrix without inventing TRS', () => {
    const builder = new HgGltfBuilder();
    builder.json.nodes = [{ matrix: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 2, 3, 4, 1] }];
    builder.json.scenes = [{ nodes: [0] }];
    builder.json.scene = 0;
    const decoded = readHgGltfScene(parseHgGlb(builder.toGlb()));
    expect(decoded.nodes[0].matrix?.slice(12, 15)).toEqual([2, 3, 4]);
    expect(decoded.nodes[0].translation).toBeNull();
    expect(decoded.nodes[0].rotation).toBeNull();
    expect(decoded.nodes[0].scale).toBeNull();
  });

  it('rejects unsupported required extensions explicitly', () => {
    const builder = new HgGltfBuilder();
    builder.json.extensionsRequired = ['KHR_draco_mesh_compression'];
    expect(() => readHgGltfScene(parseHgGlb(builder.toGlb()))).toThrow(/extensions/i);
  });

  it('rejects non-triangle primitives', () => {
    const builder = new HgGltfBuilder();
    const position = builder.addAccessor([0, 0, 0, 1, 0, 0, 0, 1, 0], { type: 'VEC3', componentType: 5126 });
    builder.json.meshes = [{ primitives: [{ attributes: { POSITION: position }, mode: 1 }] }];
    expect(() => readHgGltfScene(parseHgGlb(builder.toGlb()))).toThrow(/TRIANGLES/);
  });

  it('rejects mismatched vertex attribute counts', () => {
    const builder = new HgGltfBuilder();
    const position = builder.addAccessor([0, 0, 0, 1, 0, 0, 0, 1, 0], { type: 'VEC3', componentType: 5126 });
    const normal = builder.addAccessor([0, 0, 1, 0, 0, 1], { type: 'VEC3', componentType: 5126 });
    builder.json.meshes = [{ primitives: [{ attributes: { POSITION: position, NORMAL: normal } }] }];
    expect(() => readHgGltfScene(parseHgGlb(builder.toGlb()))).toThrow(/counts/);
  });

  it('rejects a morph target whose vertex count differs from the base mesh', () => {
    const builder = new HgGltfBuilder();
    const position = builder.addAccessor(
      [0, 0, 0, 1, 0, 0, 0, 1, 0],
      { type: 'VEC3', componentType: 5126 },
    );
    const morph = builder.addAccessor(
      [0, 0, 0, 0, 0.1, 0],
      { type: 'VEC3', componentType: 5126 },
    );
    builder.json.meshes = [{
      primitives: [{ attributes: { POSITION: position }, targets: [{ POSITION: morph }] }],
    }];
    expect(() => readHgGltfScene(parseHgGlb(builder.toGlb()))).toThrow(/target.*count/i);
  });

  it('rejects an inverse-bind accessor that is not FLOAT MAT4', () => {
    const builder = new HgGltfBuilder();
    const inverseBind = builder.addAccessor([0, 0, 0, 1], { type: 'VEC4', componentType: 5126 });
    builder.json.nodes = [{ name: 'root' }];
    builder.json.skins = [{ joints: [0], inverseBindMatrices: inverseBind }];
    expect(() => readHgGltfScene(parseHgGlb(builder.toGlb()))).toThrow(/FLOAT MAT4/);
  });
});
