import { describe, expect, it } from 'vitest';
import { Bone, MeshStandardMaterial, SkinnedMesh, type Object3D } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { HgGltfBuilder } from '../core/gltfBuilder';
import { HgBone, HgObject3D } from '../core/sceneGraph';
import { HgSkinnedMesh, HgStandardMaterial } from '../core/sceneSkin';
import { loadHgFirstPartyScene } from './gltfFirstPartyScene';

function fixture(): Uint8Array {
  const builder = new HgGltfBuilder();
  const position = builder.addAccessor(
    [0, 0, 0, 0.2, 0, 0, 0, 0.3, 0],
    { type: 'VEC3', componentType: 5126, target: 34962 },
  );
  const normal = builder.addAccessor(
    [0, 0, 1, 0, 0, 1, 0, 0, 1],
    { type: 'VEC3', componentType: 5126, target: 34962 },
  );
  const joints = builder.addAccessor(
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    { type: 'VEC4', componentType: 5121, target: 34962 },
  );
  const weights = builder.addAccessor(
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    { type: 'VEC4', componentType: 5126, target: 34962 },
  );
  const morph = builder.addAccessor(
    [0, 0, 0, 0, 0.02, 0, 0, 0, 0],
    { type: 'VEC3', componentType: 5126, target: 34962 },
  );
  const indices = builder.addAccessor(
    [0, 1, 2],
    { type: 'SCALAR', componentType: 5123, target: 34963 },
  );
  const inverseBind = builder.addAccessor(
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -0.1, -0.2, -0.3, 1],
    { type: 'MAT4', componentType: 5126 },
  );

  builder.json.materials = [{
    name: 'mat',
    pbrMetallicRoughness: {
      baseColorFactor: [0.6, 0.4, 0.2, 1],
      metallicFactor: 0.1,
      roughnessFactor: 0.75,
    },
  }];
  builder.json.meshes = [{
    name: 'body',
    weights: [0.35],
    extras: { targetNames: ['bend'] },
    primitives: [{
      attributes: {
        POSITION: position,
        NORMAL: normal,
        JOINTS_0: joints,
        WEIGHTS_0: weights,
      },
      targets: [{ POSITION: morph }],
      indices,
      material: 0,
    }],
  }];
  builder.json.skins = [{ joints: [0], skeleton: 0, inverseBindMatrices: inverseBind }];
  builder.json.nodes = [
    {
      name: 'pelvis',
      children: [1],
      translation: [0.1, 0.2, 0.3],
      rotation: [0, 0, 0, 1],
      scale: [1, 1, 1],
    },
    {
      name: 'body_node',
      mesh: 0,
      skin: 0,
      translation: [0, 0.5, 0],
      rotation: [0, 0, 0, 1],
      scale: [1, 1, 1],
    },
  ];
  builder.json.scenes = [{ nodes: [0] }];
  builder.json.scene = 0;
  return builder.toGlb();
}

function collectThree(root: Object3D) {
  root.updateMatrixWorld(true);
  const bones: Bone[] = [];
  const meshes: SkinnedMesh[] = [];
  root.traverse((object) => {
    if ((object as Bone).isBone) bones.push(object as Bone);
    if ((object as SkinnedMesh).isSkinnedMesh) meshes.push(object as SkinnedMesh);
  });
  return { bones, meshes };
}

function collectFirstParty(root: HgObject3D) {
  root.updateMatrixWorld(true);
  const bones: HgBone[] = [];
  const meshes: HgSkinnedMesh[] = [];
  root.traverse((object) => {
    if (object instanceof HgBone) bones.push(object);
    if (object instanceof HgSkinnedMesh) meshes.push(object);
  });
  return { bones, meshes };
}

function expectArrayClose(actual: ArrayLike<number>, expected: ArrayLike<number>, digits = 7) {
  expect(actual.length).toBe(expected.length);
  for (let index = 0; index < actual.length; index += 1) {
    expect(Number(actual[index]), `index ${index}`).toBeCloseTo(Number(expected[index]), digits);
  }
}

describe('first-party GLB scene materialiser parity', () => {
  it('matches GLTFLoader for the supported skinned/morph subset', async () => {
    const bytes = fixture();
    const buffer = bytes.buffer.slice(
      bytes.byteOffset,
      bytes.byteOffset + bytes.byteLength,
    ) as ArrayBuffer;

    const reference = (await new GLTFLoader().parseAsync(buffer, '')).scene;
    const actual = await loadHgFirstPartyScene(bytes);

    const expected = collectThree(reference);
    const current = collectFirstParty(actual);
    expect(current.bones.map((bone) => bone.name)).toEqual(expected.bones.map((bone) => bone.name));
    expect(current.meshes).toHaveLength(expected.meshes.length);
    expect(current.bones).toHaveLength(1);
    expect(current.meshes).toHaveLength(1);

    expectArrayClose(current.bones[0].matrixWorld.elements, expected.bones[0].matrixWorld.elements);
    expectArrayClose(
      current.meshes[0].geometry.getAttribute('position').array,
      expected.meshes[0].geometry.getAttribute('position').array,
    );
    expectArrayClose(
      current.meshes[0].geometry.getAttribute('skinWeight').array,
      expected.meshes[0].geometry.getAttribute('skinWeight').array,
    );
    expect(current.meshes[0].skeleton.bones.map((bone) => bone.name))
      .toEqual(expected.meshes[0].skeleton.bones.map((bone) => bone.name));
    expectArrayClose(
      current.meshes[0].skeleton.boneInverses[0].elements,
      expected.meshes[0].skeleton.boneInverses[0].elements,
    );
    expect(current.meshes[0].morphTargetDictionary).toEqual(expected.meshes[0].morphTargetDictionary);
    expect(current.meshes[0].morphTargetInfluences?.[0])
      .toBeCloseTo(expected.meshes[0].morphTargetInfluences?.[0] ?? 0, 7);

    const currentMaterial = current.meshes[0].material;
    const expectedMaterial = expected.meshes[0].material;
    if (Array.isArray(currentMaterial) || Array.isArray(expectedMaterial)) {
      throw new Error('Fixture unexpectedly produced a material array');
    }
    const currentStandard = currentMaterial as HgStandardMaterial;
    const expectedStandard = expectedMaterial as MeshStandardMaterial;
    expect(currentStandard.metalness).toBeCloseTo(expectedStandard.metalness, 7);
    expect(currentStandard.roughness).toBeCloseTo(expectedStandard.roughness, 7);
    expectArrayClose(
      [currentStandard.color.r, currentStandard.color.g, currentStandard.color.b],
      expectedStandard.color.toArray(),
    );
  });
});
