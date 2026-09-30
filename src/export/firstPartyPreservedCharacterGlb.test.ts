import { describe, expect, it } from 'vitest';
import { HgBufferAttribute, HgHgSkinnedMesh } from '../core/sceneSkin';
import { parseHgGlb } from '../core/glbContainer';
import { readHgAccessor } from '../core/gltfAccessors';
import { readHgGltfAnimations } from '../core/gltfAnimation';
import { HgGltfBuilder } from '../core/gltfBuilder';
import { loadHgFirstPartyScene } from '../character/gltfFirstPartyScene';
import { exportFirstPartyPreservedCharacterGlb } from './firstPartyPreservedCharacterGlb';

function sourceFixture(): { data: ArrayBuffer; positionAccessor: number } {
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
  const existingMorph = builder.addAccessor(
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
      targets: [{ POSITION: existingMorph }],
      indices,
    }],
  }];
  builder.json.skins = [{
    joints: [0],
    skeleton: 0,
    inverseBindMatrices: inverseBind,
  }];
  builder.json.nodes = [
    { name: 'pelvis.root' },
    { name: 'body_node', mesh: 0, skin: 0, children: [0] },
  ];
  builder.json.scenes = [{ name: 'authored_scene', nodes: [1] }];
  builder.json.scene = 0;

  const bytes = builder.toGlb();
  return { data: bytes.slice().buffer as ArrayBuffer, positionAccessor: position };
}

describe('first-party preserved character GLB writer', () => {
  it('keeps authored GLB data and appends source-bone and runtime morph animation', async () => {
    const fixture = sourceFixture();
    const scene = await loadHgFirstPartyScene(fixture.data);
    let mesh: HgSkinnedMesh | null = null;
    scene.traverse((object) => {
      if ((object as HgSkinnedMesh).isHgSkinnedMesh) mesh = object as HgSkinnedMesh;
    });
    expect(mesh).not.toBeNull();

    const geometry = mesh!.geometry;
    const runtimeMorph = new HgBufferAttribute(
      new Float32Array([
        0, 0, 0,
        0, 0.2, 0,
        0, 0, 0,
      ]),
      3,
    );
    runtimeMorph.name = 'runtime_bend';
    geometry.morphAttributes.position = [
      ...(geometry.morphAttributes.position ?? []),
      runtimeMorph,
    ];
    geometry.morphTargetsRelative = true;
    mesh!.updateMorphTargets();
    mesh!.morphTargetInfluences![0] = 0.4;
    mesh!.morphTargetInfluences![1] = 0;

    const blob = exportFirstPartyPreservedCharacterGlb(
      {
        preservedGlb: fixture.data,
        sourceScale: 0.75,
        meshes: [mesh!],
      },
      {
        name: 'fixture_animation',
        duration: 1,
        tracks: [],
        equipmentTracks: new Map(),
        times: [0, 1],
        fps: 20,
        deformationTracks: [
          {
            target: 'pelvisroot',
            property: 'quaternion',
            times: [0, 1],
            values: [0, 0, 0, 1, 0, 0.1, 0, 0.9949874371],
          },
          {
            target: 'body',
            property: 'morphTargetInfluence',
            morphTarget: 'runtime_bend',
            times: [0, 1],
            values: [0, 1],
          },
        ],
      },
      { clipName: 'fixture_clip' },
    );

    const output = parseHgGlb(await blob.arrayBuffer());
    expect(readHgAccessor(output, fixture.positionAccessor).values).toEqual(
      readHgAccessor(parseHgGlb(fixture.data), fixture.positionAccessor).values,
    );

    const meshes = output.json.meshes as Array<{
      extras?: { targetNames?: string[] };
      primitives: Array<{ targets?: Array<{ POSITION?: number }> }>;
    }>;
    expect(meshes[0].extras?.targetNames).toEqual(['bend', 'runtime_bend']);
    expect(meshes[0].primitives[0].targets).toHaveLength(2);
    const appended = meshes[0].primitives[0].targets![1].POSITION!;
    expect(readHgAccessor(output, appended).values).toEqual(
      Array.from(new Float32Array([
        0, 0, 0,
        0, 0.2, 0,
        0, 0, 0,
      ])),
    );

    const animations = readHgGltfAnimations(output);
    expect(animations).toHaveLength(1);
    const rotation = animations[0].channels.find((channel) => channel.path === 'rotation');
    const weights = animations[0].channels.find((channel) => channel.path === 'weights');
    expect(rotation?.node).toBe(0);
    expect(weights?.node).toBe(1);
    expect(weights?.valueSize).toBe(2);
    expect(weights?.values[0]).toBeCloseTo(0.4, 6);
    expect(weights?.values[1]).toBeCloseTo(0, 6);
    expect(weights?.values[2]).toBeCloseTo(0.4, 6);
    expect(weights?.values[3]).toBeCloseTo(1, 6);

    const nodes = output.json.nodes as Array<{
      name?: string;
      children?: number[];
      scale?: number[];
    }>;
    const scenes = output.json.scenes as Array<{ nodes: number[] }>;
    const exportRoot = nodes[scenes[0].nodes[0]];
    const characterRoot = nodes[exportRoot.children![0]];
    expect(exportRoot.name).toBe('fixture_clip');
    expect(characterRoot.name).toBe('authored_scene');
    expect(characterRoot.scale).toEqual([0.75, 0.75, 0.75]);
    expect(characterRoot.children).toEqual([1]);
    expect((output.json.asset as { generator?: string }).generator)
      .toBe('Home Gym PT first-party codec');
  });
});
