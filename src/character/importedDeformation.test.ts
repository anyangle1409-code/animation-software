import { describe, expect, it } from 'vitest';
import {
  Bone,
  BufferAttribute,
  BufferGeometry,
  Group,
  MeshBasicMaterial,
  Skeleton as ThreeSkeleton,
  SkinnedMesh,
} from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { restPose } from '../rig/pose';
import type { BoneName } from '../rig/boneNames';
import { importedElbowDeformation } from './importedDeformation';

function elbowFixture() {
  const upper = new Bone();
  upper.name = 'DEF-upper_arm.L';
  upper.position.set(0, 0.1, 0);
  const lower = new Bone();
  lower.name = 'DEF-forearm.L';
  lower.position.set(0, -0.1, 0);
  upper.add(lower);

  // A coarse 3x3 patch over the back of the elbow. The centre deliberately
  // protrudes by 20 mm, giving the directional pass a polygonal point to settle.
  const positions: number[] = [];
  for (const y of [-0.03, 0, 0.03]) {
    for (const x of [-0.03, 0, 0.03]) {
      positions.push(x, y, x === 0 && y === 0 ? -0.07 : -0.05);
    }
  }
  const indices = [
    0, 3, 1, 1, 3, 4,
    1, 4, 2, 2, 4, 5,
    3, 6, 4, 4, 6, 7,
    4, 7, 5, 5, 7, 8,
  ];
  const skinIndex: number[] = [];
  const skinWeight: number[] = [];
  for (let vertex = 0; vertex < 9; vertex += 1) {
    skinIndex.push(0, 1, 0, 0);
    skinWeight.push(0.5, 0.5, 0, 0);
  }

  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(new Float32Array(positions), 3));
  geometry.setAttribute('skinIndex', new BufferAttribute(new Uint16Array(skinIndex), 4));
  geometry.setAttribute('skinWeight', new BufferAttribute(new Float32Array(skinWeight), 4));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();

  const mesh = new SkinnedMesh(geometry, new MeshBasicMaterial());
  mesh.name = 'elbow-fixture';
  const scene = new Group();
  scene.add(mesh, upper);
  scene.updateMatrixWorld(true);
  mesh.bind(new ThreeSkeleton([upper, lower]));
  scene.updateMatrixWorld(true);

  const boneByName = new Map<BoneName, Bone>([
    ['upperarm_l', upper],
    ['forearm_l', lower],
  ]);
  return { mesh, boneByName };
}

function morphOffset(mesh: SkinnedMesh, morph: BufferAttribute, vertex: number) {
  const base = mesh.geometry.getAttribute('position');
  const baseX = mesh.geometry.morphTargetsRelative ? 0 : base.getX(vertex);
  const baseY = mesh.geometry.morphTargetsRelative ? 0 : base.getY(vertex);
  const baseZ = mesh.geometry.morphTargetsRelative ? 0 : base.getZ(vertex);
  return {
    x: morph.getX(vertex) - baseX,
    y: morph.getY(vertex) - baseY,
    z: morph.getZ(vertex) - baseZ,
  };
}

function addExistingMorph(mesh: SkinnedMesh, relative: boolean) {
  const position = mesh.geometry.getAttribute('position');
  const values = new Float32Array(position.count * 3);
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    const start = vertex * 3;
    if (!relative) {
      values[start] = position.getX(vertex);
      values[start + 1] = position.getY(vertex);
      values[start + 2] = position.getZ(vertex);
    }
  }
  // Give the pre-existing target an easily checked, non-zero expression delta.
  values[0] += 0.012;
  const expression = new BufferAttribute(values, 3);
  expression.name = 'existing_expression';
  mesh.geometry.morphTargetsRelative = relative;
  mesh.geometry.morphAttributes.position = [expression];
  mesh.updateMorphTargets();
  return expression;
}

describe('imported elbow directional smoothing', () => {
  it('is explicitly opt-in', () => {
    const { mesh, boneByName } = elbowFixture();
    const deformation = importedElbowDeformation(
      [mesh],
      boneByName,
      canonicalSkeleton,
      { enabled: true, inner: 0, outer: 0, outerSmooth: 0 },
    );
    expect(deformation).toBeNull();
  });

  it('settles only the flexion morph and caps the added bind-space offset', () => {
    const { mesh, boneByName } = elbowFixture();
    const deformation = importedElbowDeformation(
      [mesh],
      boneByName,
      canonicalSkeleton,
      { enabled: true, inner: 0, outer: 0, outerSmooth: 1 },
    );
    expect(deformation).not.toBeNull();

    const morph = mesh.geometry.morphAttributes.position?.[0] as BufferAttribute | undefined;
    expect(morph).toBeDefined();
    let maximum = 0;
    for (let vertex = 0; vertex < morph!.count; vertex += 1) {
      const offset = morphOffset(mesh, morph!, vertex);
      maximum = Math.max(maximum, Math.hypot(offset.x, offset.y, offset.z));
    }

    // The 20 mm polygonal centre is pulled towards its neighbours, but the
    // candidate guardrail limits any one vertex to 8 mm in bind space.
    expect(morphOffset(mesh, morph!, 4).z).toBeGreaterThan(0.005);
    expect(maximum).toBeLessThanOrEqual(0.008001);
    expect(mesh.morphTargetInfluences?.[0]).toBe(0);
  });

  for (const relative of [false, true]) {
    it(`preserves pre-existing ${relative ? 'relative' : 'absolute'} morph targets`, () => {
      const { mesh, boneByName } = elbowFixture();
      const expression = addExistingMorph(mesh, relative);
      const before = Array.from(expression.array as ArrayLike<number>);

      const deformation = importedElbowDeformation(
        [mesh],
        boneByName,
        canonicalSkeleton,
        { enabled: true, inner: 0, outer: 0, outerSmooth: 1 },
      );
      expect(deformation).not.toBeNull();
      expect(mesh.geometry.morphTargetsRelative).toBe(relative);

      const morphs = mesh.geometry.morphAttributes.position as BufferAttribute[];
      expect(morphs).toHaveLength(2);
      expect(Array.from(morphs[0].array as ArrayLike<number>)).toEqual(before);
      expect(morphs[0].name).toBe('existing_expression');

      const corrective = morphs[1];
      let maximum = 0;
      for (let vertex = 0; vertex < corrective.count; vertex += 1) {
        const offset = morphOffset(mesh, corrective, vertex);
        maximum = Math.max(maximum, Math.hypot(offset.x, offset.y, offset.z));
      }
      expect(maximum).toBeGreaterThan(0.005);
      expect(maximum).toBeLessThanOrEqual(0.008001);
    });
  }

  it('tunes outer smoothing live and bakes the same value through the export sampler', () => {
    const { mesh, boneByName } = elbowFixture();
    const tuning = { outerSmooth: 0, defaultOuterSmooth: 0 };
    const deformation = importedElbowDeformation(
      [mesh],
      boneByName,
      canonicalSkeleton,
      { enabled: true, inner: 0, outer: 0, outerSmooth: 0 },
      tuning,
    );
    expect(deformation).not.toBeNull();
    const control = deformation!.controls?.find((entry) => entry.id === 'elbowOuterSmooth');
    expect(control).toBeDefined();
    expect(control!.value).toBe(0);

    const outerIndex = mesh.morphTargetDictionary?.homeGymPT_elbow_outer_l;
    expect(typeof outerIndex).toBe('number');
    const pose = restPose();
    pose.rotations.forearm_l = { x: (120 * Math.PI) / 180, y: 0, z: 0 };
    const evaluation = new PoseEvaluation(canonicalSkeleton).apply(pose);

    deformation!.update({
      rig: canonicalSkeleton,
      pose,
      evaluation,
      character: null as never,
    });
    expect(mesh.morphTargetInfluences?.[outerIndex as number]).toBe(0);

    control!.set(1);
    deformation!.update({
      rig: canonicalSkeleton,
      pose,
      evaluation,
      character: null as never,
    });
    const live = mesh.morphTargetInfluences?.[outerIndex as number] ?? 0;
    expect(live).toBeGreaterThan(0.5);

    const sampler = deformation!.sampler?.();
    expect(sampler).not.toBeNull();
    sampler!.sample(restPose());
    sampler!.sample(pose);
    const track = sampler!.tracks([0, 1]).find((entry) =>
      entry.name.includes('homeGymPT_elbow_outer_l'),
    );
    expect(track).toBeDefined();
    expect(Number(track!.values[track!.values.length - 1])).toBeCloseTo(live, 6);

    control!.set(2);
    expect(control!.value).toBe(1);
    control!.set(-1);
    expect(control!.value).toBe(0);
  });

});
