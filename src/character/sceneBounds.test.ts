import { describe, expect, it } from 'vitest';
import {
  Bone,
  Box3,
  BufferAttribute,
  BufferGeometry,
  Group,
  Mesh,
  MeshBasicMaterial,
  Skeleton,
  SkinnedMesh,
} from 'three';
import { measureSceneHeight } from './sceneBounds';

const threeHeight = (object: Group) => {
  object.updateMatrixWorld(true);
  const box = new Box3().setFromObject(object);
  return Math.max(0.5, box.max.y - box.min.y);
};

describe('first-party character scene bounds', () => {
  it('matches transformed mesh bounds', () => {
    const geometry = new BufferGeometry();
    geometry.setAttribute('position', new BufferAttribute(new Float32Array([
      -0.2, 0.1, 0,
       0.3, 1.6, 0.2,
       0.0, 0.8, -0.1,
    ]), 3));
    const mesh = new Mesh(geometry, new MeshBasicMaterial());
    mesh.position.set(0.3, 0.4, -0.2);
    mesh.rotation.z = 0.23;
    mesh.scale.set(1.1, 0.9, 1.2);
    const root = new Group();
    root.add(mesh);

    expect(measureSceneHeight(root)).toBeCloseTo(threeHeight(root), 6);
  });

  it('matches morph and skin deformation bounds in the bind hierarchy', () => {
    const geometry = new BufferGeometry();
    geometry.setAttribute('position', new BufferAttribute(new Float32Array([
      0, 0, 0,
      0, 0.8, 0,
      0, 1.6, 0,
    ]), 3));
    geometry.setAttribute('skinIndex', new BufferAttribute(new Uint16Array([
      0, 0, 0, 0,
      0, 1, 0, 0,
      1, 0, 0, 0,
    ]), 4));
    geometry.setAttribute('skinWeight', new BufferAttribute(new Float32Array([
      1, 0, 0, 0,
      0.5, 0.5, 0, 0,
      1, 0, 0, 0,
    ]), 4));
    const morph = new BufferAttribute(new Float32Array([
      0, 0, 0,
      0, 0.15, 0,
      0, 0.2, 0,
    ]), 3);
    geometry.morphAttributes.position = [morph];
    geometry.morphTargetsRelative = true;

    const rootBone = new Bone();
    const upper = new Bone();
    upper.position.y = 0.8;
    rootBone.add(upper);

    const mesh = new SkinnedMesh(geometry, new MeshBasicMaterial());
    mesh.add(rootBone);
    mesh.bind(new Skeleton([rootBone, upper]));
    mesh.updateMorphTargets();
    mesh.morphTargetInfluences![0] = 0.65;

    upper.rotation.z = 0.28;
    const root = new Group();
    root.add(mesh);

    expect(measureSceneHeight(root)).toBeCloseTo(threeHeight(root), 5);
  });
});
