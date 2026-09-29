import { describe, expect, it } from 'vitest';
import { HgGltfBuilder } from '../core/gltfBuilder';
import { HgBone, HgObject3D } from '../core/sceneGraph';
import { HgSkinnedMesh, HgStandardMaterial } from '../core/sceneSkin';
import {
  hgFirstPartyPrimitiveSource,
  loadHgFirstPartyScene,
} from './gltfFirstPartyScene';

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
  const inverseBindValues = [
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    -0.1, -0.2, -0.3, 1,
  ];
  const inverseBind = builder.addAccessor(inverseBindValues, {
    type: 'MAT4',
    componentType: 5126,
  });

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
  builder.json.skins = [{
    joints: [0],
    skeleton: 0,
    inverseBindMatrices: inverseBind,
  }];
  builder.json.nodes = [
    {
      name: 'pelvis.root',
      children: [1],
      translation: [0.1, 0.2, 0.3],
      rotation: [0, 0, 0, 1],
      scale: [1, 1, 1],
    },
    {
      name: 'body',
      mesh: 0,
      skin: 0,
      translation: [0, 0.5, 0],
      rotation: [0, 0, 0, 1],
      scale: [1, 1, 1],
      extras: { homeGymPT: { gripSolutionId: 'fixture' } },
    },
  ];
  builder.json.scenes = [{ name: 'fixture_scene', nodes: [0] }];
  builder.json.scene = 0;
  return builder.toGlb();
}

const collect = (root: HgObject3D) => {
  root.updateMatrixWorld(true);
  const bones: HgBone[] = [];
  const meshes: HgSkinnedMesh[] = [];
  root.traverse((object) => {
    if (object instanceof HgBone) bones.push(object);
    if (object instanceof HgSkinnedMesh) meshes.push(object);
  });
  return { bones, meshes };
};

describe('first-party GLB scene materialiser', () => {
  it('materialises the supported skin/morph/material subset without renderer objects', async () => {
    const scene = await loadHgFirstPartyScene(fixture());
    expect(scene.name).toBe('fixture_scene');
    const { bones, meshes } = collect(scene);

    expect(bones.map((bone) => bone.name)).toEqual(['pelvisroot']);
    expect(meshes).toHaveLength(1);
    const mesh = meshes[0];
    expect(mesh.geometry.getAttribute('position')?.count).toBe(3);
    expect(mesh.geometry.getAttribute('skinWeight')?.count).toBe(3);
    expect(mesh.skeleton.bones[0]).toBe(bones[0]);
    expect(mesh.skeleton.boneInverses[0].toArray()).toEqual([
      1, 0, 0, 0,
      0, 1, 0, 0,
      0, 0, 1, 0,
      -0.1, -0.2, -0.3, 1,
    ]);
    expect(mesh.morphTargetDictionary).toEqual({ bend: 0 });
    expect(mesh.morphTargetInfluences?.[0]).toBeCloseTo(0.35, 7);
    expect(mesh.name).toBe('body');
    expect(mesh.parent?.name).not.toBe(mesh.name);
    expect(mesh.parent?.userData.homeGymPT).toEqual({ gripSolutionId: 'fixture' });
    expect(hgFirstPartyPrimitiveSource(mesh)).toEqual({
      nodeIndex: 1,
      meshIndex: 0,
      primitiveIndex: 0,
      targetNames: ['bend'],
    });

    const material = mesh.material;
    expect(Array.isArray(material)).toBe(false);
    const standard = material as HgStandardMaterial;
    expect(standard.name).toBe('mat');
    expect(standard.metalness).toBe(0.1);
    expect(standard.roughness).toBe(0.75);
    expect([standard.color.r, standard.color.g, standard.color.b]).toEqual([0.6, 0.4, 0.2]);

    // Node transforms use the decoded GLB values, not renderer defaults.
    expect(bones[0].position.toArray()).toEqual([0.1, 0.2, 0.3]);
    expect(mesh.parent?.position.toArray()).toEqual([0, 0.5, 0]);
  });

  it('sanitizes and de-duplicates runtime node names identically to the live adapter', async () => {
    const builder = new HgGltfBuilder();
    builder.json.nodes = [
      { name: 'arm.R' },
      { name: 'arm:R' },
      { name: 'arm R' },
    ];
    builder.json.scenes = [{ nodes: [0, 1, 2] }];
    builder.json.scene = 0;
    const scene = await loadHgFirstPartyScene(builder.toGlb());
    expect(scene.children.map((child) => child.name)).toEqual([
      'armR',
      'armR_1',
      'arm_R',
    ]);
  });
});
