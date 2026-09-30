import { HgGltfBuilder } from '../core/gltfBuilder';
import { HgMat4, HgVec3 } from '../core/linearMath';

export interface HgRigifyFixture {
  data: ArrayBuffer;
  positions: Float32Array;
  boneNames: string[];
}

interface FixtureBone {
  name: string;
  parent: number | null;
  offset: [number, number, number];
  world: HgVec3;
  children: number[];
}

/**
 * Small Rigify-shaped skinned GLB authored directly through the Home Gym PT
 * codec. The source skeleton intentionally includes deform twists and an
 * armature-root helper so imported-character tests cover passive bones.
 */
export function hgRigifyFixture(): HgRigifyFixture {
  const bones: FixtureBone[] = [];
  const byName = new Map<string, number>();

  const bone = (
    name: string,
    parentName: string | null,
    offset: [number, number, number],
  ) => {
    const parent = parentName === null ? null : byName.get(parentName);
    if (parentName !== null && parent === undefined) {
      throw new Error(`Fixture parent ${parentName} is missing`);
    }
    const world = new HgVec3(...offset);
    if (parent !== null && parent !== undefined) world.add(bones[parent].world);
    const index = bones.length;
    bones.push({ name, parent: parent ?? null, offset, world, children: [] });
    if (parent !== null && parent !== undefined) bones[parent].children.push(index);
    byName.set(name, index);
  };

  bone('DEF-spine', null, [0, 0.95, 0]);
  bone('DEF-spine.001', 'DEF-spine', [0, 0.14, 0]);
  bone('DEF-spine.002', 'DEF-spine.001', [0, 0.14, 0]);
  bone('DEF-spine.003', 'DEF-spine.002', [0, 0.14, 0]);
  bone('DEF-spine.004', 'DEF-spine.003', [0, 0.15, 0]);
  bone('DEF-spine.005', 'DEF-spine.004', [0, 0.05, 0]);
  bone('DEF-spine.006', 'DEF-spine.005', [0, 0.05, 0]);
  bone('DEF-jaw.helper', 'DEF-spine', [0.02, 0.62, 0.06]);

  for (const [side, sign] of [['L', 1], ['R', -1]] as const) {
    bone(`DEF-shoulder.${side}`, 'DEF-spine.003', [sign * 0.04, 0.12, 0]);
    bone(`DEF-upper_arm.${side}`, `DEF-shoulder.${side}`, [sign * 0.12, 0, 0]);
    bone(`DEF-upper_arm.${side}.001`, `DEF-upper_arm.${side}`, [sign * 0.14, 0, 0]);
    bone(`DEF-forearm.${side}`, `DEF-upper_arm.${side}.001`, [sign * 0.14, 0, 0]);
    bone(`DEF-forearm.${side}.001`, `DEF-forearm.${side}`, [sign * 0.12, 0, 0]);
    bone(`DEF-hand.${side}`, `DEF-forearm.${side}.001`, [sign * 0.12, 0, 0]);
    bone(`DEF-thigh.${side}`, 'DEF-spine', [sign * 0.09, -0.04, 0]);
    bone(`DEF-shin.${side}`, `DEF-thigh.${side}`, [0, -0.42, 0]);
    bone(`DEF-foot.${side}`, `DEF-shin.${side}`, [0, -0.42, 0]);
    bone(`DEF-toe.${side}`, `DEF-foot.${side}`, [0, -0.04, 0.12]);
  }

  const positions: number[] = [];
  const skinIndices: number[] = [];
  const skinWeights: number[] = [];
  const indices: number[] = [];

  bones.forEach((entry, boneIndex) => {
    const start = positions.length / 3;
    for (let step = 0; step < 6; step += 1) {
      const angle = (step / 6) * Math.PI * 2;
      positions.push(
        entry.world.x + 0.04 * Math.cos(angle),
        entry.world.y + 0.02 * (step % 2 === 0 ? 1 : -1),
        entry.world.z + 0.04 * Math.sin(angle),
      );
      const shared = step < 2 && entry.parent !== null;
      skinIndices.push(boneIndex, shared ? entry.parent! : 0, 0, 0);
      skinWeights.push(shared ? 0.6 : 1, shared ? 0.4 : 0, 0, 0);
    }
    for (let step = 0; step < 4; step += 1) {
      const next = start + step + 2 > start + 5 ? start + 1 : start + step + 2;
      indices.push(start, start + step + 1, next);
    }
  });

  const authored = new Float32Array(positions);
  const builder = new HgGltfBuilder();
  const positionAccessor = builder.addAccessor(Array.from(authored), {
    type: 'VEC3', componentType: 5126, target: 34962, includeMinMax: true,
  });
  const uvAccessor = builder.addAccessor(
    Array.from({ length: (positions.length / 3) * 2 }, () => 0.5),
    { type: 'VEC2', componentType: 5126, target: 34962 },
  );
  const jointsAccessor = builder.addAccessor(skinIndices, {
    type: 'VEC4', componentType: 5123, target: 34962,
  });
  const weightsAccessor = builder.addAccessor(skinWeights, {
    type: 'VEC4', componentType: 5126, target: 34962,
  });
  const indexAccessor = builder.addAccessor(indices, {
    type: 'SCALAR',
    componentType: Math.max(...indices) <= 65535 ? 5123 : 5125,
    target: 34963,
  });

  const inverseBinds = bones.flatMap((entry) =>
    new HgMat4().makeTranslation(
      -entry.world.x,
      -entry.world.y,
      -entry.world.z,
    ).toArray(),
  );
  const inverseBindAccessor = builder.addAccessor(inverseBinds, {
    type: 'MAT4', componentType: 5126,
  });

  builder.json.materials = [{
    name: 'FixtureMaterial',
    pbrMetallicRoughness: {
      baseColorFactor: [0.8, 0.8, 0.8, 1],
      metallicFactor: 0,
      roughnessFactor: 1,
    },
  }];
  builder.json.meshes = [{
    name: 'FixtureBody',
    primitives: [{
      attributes: {
        POSITION: positionAccessor,
        TEXCOORD_0: uvAccessor,
        JOINTS_0: jointsAccessor,
        WEIGHTS_0: weightsAccessor,
      },
      indices: indexAccessor,
      material: 0,
    }],
  }];

  const boneNodes = bones.map((entry) => ({
    name: entry.name,
    translation: [...entry.offset],
    ...(entry.children.length ? { children: [...entry.children] } : {}),
  }));
  const meshNode = boneNodes.length;
  builder.json.nodes = [
    ...boneNodes,
    { name: 'FixtureBodyNode', mesh: 0, skin: 0 },
  ];
  builder.json.skins = [{
    name: 'FixtureSkin',
    joints: bones.map((_, index) => index),
    skeleton: 0,
    inverseBindMatrices: inverseBindAccessor,
  }];
  builder.json.scenes = [{
    name: 'FixtureCharacter',
    nodes: [0, meshNode],
  }];
  builder.json.scene = 0;

  const bytes = builder.toGlb();
  return {
    data: bytes.slice().buffer as ArrayBuffer,
    positions: authored,
    boneNames: bones.map((entry) => entry.name),
  };
}
