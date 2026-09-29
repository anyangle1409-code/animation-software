import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { parseHgGlb } from '../core/glbContainer';
import { readHgGltfAnimations } from '../core/gltfAnimation';
import { HgGltfBuilder } from '../core/gltfBuilder';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { proceduralCharacter } from '../character/procedural';
import { exportFirstPartyReboundCharacterGlb } from './firstPartyReboundCharacterGlb';

function sourceResources(): ArrayBuffer {
  const builder = new HgGltfBuilder();
  builder.json.materials = [{
    name: 'authored_source_material',
    pbrMetallicRoughness: {
      baseColorFactor: [0.2, 0.3, 0.4, 1],
      metallicFactor: 0.1,
      roughnessFactor: 0.7,
    },
  }];
  builder.json.meshes = [{
    name: 'authored_source_mesh',
    primitives: [{
      attributes: {},
      material: 0,
      mode: 4,
    }],
  }];
  builder.json.nodes = [{ name: 'old_source_node', mesh: 0 }];
  builder.json.scenes = [{ nodes: [0] }];
  builder.json.scene = 0;
  return builder.toGlb().slice().buffer as ArrayBuffer;
}

describe('first-party rebound character GLB writer', () => {
  it('writes rebuilt canonical geometry while retaining source material resources', async () => {
    const character = await proceduralCharacter.build(canonicalSkeleton);
    character.sourceGlb = sourceResources();
    character.sourceSurfaceOrigins = [{
      nodeIndex: 0,
      meshIndex: 0,
      primitiveIndex: 0,
      targetNames: [],
    }];

    try {
      const studioClip = generateClip(canonicalSkeleton, bicepCurl);
      const blob = exportFirstPartyReboundCharacterGlb(
        studioClip,
        bicepCurl,
        character,
        20,
        false,
      );
      const output = parseHgGlb(await blob.arrayBuffer());

      const materials = output.json.materials as Array<{ name?: string }>;
      expect(materials[0].name).toBe('authored_source_material');

      const meshes = output.json.meshes as Array<{
        name?: string;
        primitives: Array<{ material?: number; attributes: Record<string, number> }>;
      }>;
      const runtime = meshes.find((mesh) => mesh.name === character.meshes[0].name);
      expect(runtime).toBeDefined();
      expect(runtime!.primitives[0].material).toBe(0);
      expect(runtime!.primitives[0].attributes.POSITION).toBeTypeOf('number');
      expect(runtime!.primitives[0].attributes.JOINTS_0).toBeTypeOf('number');
      expect(runtime!.primitives[0].attributes.WEIGHTS_0).toBeTypeOf('number');

      const skins = output.json.skins as Array<{ joints: number[] }>;
      expect(skins.at(-1)?.joints).toHaveLength(canonicalSkeleton.bones.length);
      expect(readHgGltfAnimations(output)).toHaveLength(1);
      expect((output.json.asset as { generator?: string }).generator)
        .toBe('Home Gym PT first-party codec');
    } finally {
      character.dispose();
    }
  });
});
