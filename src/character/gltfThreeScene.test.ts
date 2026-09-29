import { describe, expect, it } from 'vitest';
import { Bone, MeshStandardMaterial, SkinnedMesh } from 'three';
import { HgGltfBuilder } from '../core/gltfBuilder';
import { loadHgThreeScene } from './gltfThreeScene';

function fixture(): Uint8Array {
  const builder = new HgGltfBuilder();
  const position = builder.addAccessor(
    [0, 0, 0, 1, 0, 0, 0, 1, 0],
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
    [0, 0, 0, 0, 0.1, 0, 0, 0, 0],
    { type: 'VEC3', componentType: 5126, target: 34962 },
  );
  const indices = builder.addAccessor(
    [0, 1, 2],
    { type: 'SCALAR', componentType: 5123, target: 34963 },
  );
  const inverseBind = builder.addAccessor(
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    { type: 'MAT4', componentType: 5126 },
  );

  builder.json.materials = [{
    name: 'skin',
    pbrMetallicRoughness: {
      baseColorFactor: [0.7, 0.5, 0.3, 1],
      metallicFactor: 0,
      roughnessFactor: 0.8,
    },
  }];
  builder.json.meshes = [{
    name: 'body',
    weights: [0.4],
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
  builder.json.skins = [{
    joints: [0],
    skeleton: 0,
    inverseBindMatrices: inverseBind,
  }];
  builder.json.nodes = [
    { name: 'pelvis', children: [1] },
    {
      name: 'body_node',
      mesh: 0,
      skin: 0,
      translation: [0, 1, 0],
      extras: { homeGymPT: { gripSolutionId: 'fixture' } },
    },
  ];
  builder.json.scenes = [{ name: 'fixture_scene', nodes: [0] }];
  builder.json.scene = 0;
  return builder.toGlb();
}

describe('first-party GLB to temporary Three scene adapter', () => {
  it('materializes decoded bones, skin, morphs, material and extras', async () => {
    const scene = await loadHgThreeScene(fixture());
    expect(scene.name).toBe('fixture_scene');

    const bones: Bone[] = [];
    const meshes: SkinnedMesh[] = [];
    scene.traverse((object) => {
      if ((object as Bone).isBone) bones.push(object as Bone);
      if ((object as SkinnedMesh).isSkinnedMesh) meshes.push(object as SkinnedMesh);
    });

    expect(bones.map((bone) => bone.name)).toEqual(['pelvis']);
    expect(meshes).toHaveLength(1);
    const mesh = meshes[0];
    expect(mesh.geometry.getAttribute('position').count).toBe(3);
    expect(mesh.geometry.getAttribute('skinWeight').count).toBe(3);
    expect(mesh.skeleton.bones[0]).toBe(bones[0]);
    expect(mesh.morphTargetDictionary).toEqual({ bend: 0 });
    expect(mesh.morphTargetInfluences?.[0]).toBeCloseTo(0.4, 6);
    expect(mesh.parent?.userData.homeGymPT).toEqual({ gripSolutionId: 'fixture' });

    const material = mesh.material as MeshStandardMaterial;
    expect(material.name).toBe('skin');
    expect(material.metalness).toBe(0);
    expect(material.roughness).toBeCloseTo(0.8, 6);
  });
});
