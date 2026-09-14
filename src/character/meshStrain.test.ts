import { Bone, BufferAttribute, BufferGeometry, Skeleton, SkinnedMesh } from 'three';
import { describe, expect, it } from 'vitest';
import { meshStrainDiagnostics } from './meshStrain';

function skinnedTriangle(): { mesh: SkinnedMesh; bone: Bone } {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(new Float32Array([
    0, 0, 0,
    1, 0, 0,
    0, 1, 0,
  ]), 3));
  geometry.setIndex([0, 1, 2]);
  geometry.setAttribute('skinIndex', new BufferAttribute(new Uint16Array([
    0, 0, 0, 0,
    0, 0, 0, 0,
    0, 0, 0, 0,
  ]), 4));
  geometry.setAttribute('skinWeight', new BufferAttribute(new Float32Array([
    1, 0, 0, 0,
    1, 0, 0, 0,
    1, 0, 0, 0,
  ]), 4));
  const morph = new BufferAttribute(new Float32Array([
    0, 0, 0,
    0.5, 0, 0,
    0, 0, 0,
  ]), 3);
  morph.name = 'homeGymPT_test';
  geometry.morphTargetsRelative = true;
  geometry.morphAttributes.position = [morph];
  const mesh = new SkinnedMesh(geometry);
  mesh.name = 'TestBody';
  const bone = new Bone();
  mesh.add(bone);
  mesh.bind(new Skeleton([bone]));
  mesh.updateMorphTargets();
  return { mesh, bone };
}

describe('mesh strain diagnostics', () => {
  it('reports zero strain for a rigidly transformed surface', () => {
    const { mesh, bone } = skinnedTriangle();
    bone.position.set(1, 2, 3);
    bone.updateMatrixWorld(true);
    const result = meshStrainDiagnostics([mesh], 100)[0];
    expect(result.max).toBeCloseTo(0, 6);
    expect(result.severeCompression).toBe(0);
    expect(result.severeStretch).toBe(0);
  });

  it('detects non-rigid morph stretch', () => {
    const { mesh } = skinnedTriangle();
    mesh.morphTargetInfluences![0] = 1;
    const result = meshStrainDiagnostics([mesh], 100)[0];
    expect(result.sampledEdges).toBe(3);
    expect(result.max).toBeCloseTo(0.5, 6);
    expect(result.severeStretch).toBeGreaterThan(0);
  });
});
