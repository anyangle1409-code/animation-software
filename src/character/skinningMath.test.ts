import { describe, expect, it } from 'vitest';
import { HgVec3 } from '../core/linearMath';
import { HgBone } from '../core/sceneGraph';
import {
  HgBufferAttribute,
  HgBufferGeometry,
  HgSkeleton,
  HgSkinnedMesh,
  HgStandardMaterial,
} from '../core/sceneSkin';
import { posedLocalVertex, skinnedBindLocalVertex } from './skinningMath';

const fixture = () => {
  const geometry = new HgBufferGeometry();
  geometry.setAttribute('position', new HgBufferAttribute(new Float32Array([
    0, 0, 0,
    0.2, 0.8, 0,
    -0.1, 1.5, 0.15,
  ]), 3));
  geometry.setAttribute('skinIndex', new HgBufferAttribute(new Uint16Array([
    0, 0, 0, 0,
    0, 1, 0, 0,
    1, 0, 0, 0,
  ]), 4));
  geometry.setAttribute('skinWeight', new HgBufferAttribute(new Float32Array([
    1, 0, 0, 0,
    0.35, 0.65, 0, 0,
    1, 0, 0, 0,
  ]), 4));
  const morph = new HgBufferAttribute(new Float32Array([
    0, 0, 0,
    0.04, 0.12, 0.03,
    -0.02, 0.2, 0.05,
  ]), 3);
  geometry.morphAttributes.position = [morph];
  geometry.morphTargetsRelative = true;

  const root = new HgBone();
  const upper = new HgBone();
  upper.position.y = 0.8;
  root.add(upper);

  const mesh = new HgSkinnedMesh(geometry, new HgStandardMaterial());
  mesh.add(root);
  mesh.bind(new HgSkeleton([root, upper]));
  mesh.updateMorphTargets();
  mesh.morphTargetInfluences![0] = 0.6;
  mesh.position.set(0.2, 0.1, -0.3);
  upper.rotation.z = 0.31;
  mesh.updateMatrixWorld(true);
  mesh.skeleton.update();
  return mesh;
};

describe('first-party skinning math', () => {
  it('matches the independent scene-skin morphed + skinned vertex path', () => {
    const mesh = fixture();
    for (let index = 0; index < 3; index += 1) {
      const expected = mesh.getVertexPosition(index, new HgVec3());
      const actual = posedLocalVertex(mesh, index, new HgVec3());
      expect(actual.x).toBeCloseTo(expected.x, 6);
      expect(actual.y).toBeCloseTo(expected.y, 6);
      expect(actual.z).toBeCloseTo(expected.z, 6);
    }
  });

  it('matches the independent scene-skin bind-position transform without morphs', () => {
    const mesh = fixture();
    const position = mesh.geometry.getAttribute('position');
    for (let index = 0; index < 3; index += 1) {
      const expected = new HgVec3(
        position.getX(index),
        position.getY(index),
        position.getZ(index),
      );
      mesh.applyBoneTransform(index, expected);
      const actual = skinnedBindLocalVertex(mesh, index, new HgVec3());
      expect(actual.x).toBeCloseTo(expected.x, 6);
      expect(actual.y).toBeCloseTo(expected.y, 6);
      expect(actual.z).toBeCloseTo(expected.z, 6);
    }
  });
});
