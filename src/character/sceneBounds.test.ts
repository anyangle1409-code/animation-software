import { describe, expect, it } from 'vitest';
import { HgVec3 } from '../core/linearMath';
import { HgBone, HgGroup } from '../core/sceneGraph';
import {
  HgBufferAttribute,
  HgBufferGeometry,
  HgMesh,
  HgSkeleton,
  HgSkinnedMesh,
  HgStandardMaterial,
} from '../core/sceneSkin';
import { measureSceneHeight } from './sceneBounds';

const referenceHeight = (root: HgGroup) => {
  root.updateMatrixWorld(true);
  let minimum = Infinity;
  let maximum = -Infinity;
  const point = new HgVec3();

  root.traverse((object) => {
    if (!(object instanceof HgMesh)) return;
    const position = object.geometry.getAttribute('position');
    for (let index = 0; index < position.count; index += 1) {
      if (object instanceof HgSkinnedMesh) object.getVertexPosition(index, point);
      else point.set(position.getX(index), position.getY(index), position.getZ(index));
      point.applyMatrix4(object.matrixWorld);
      minimum = Math.min(minimum, point.y);
      maximum = Math.max(maximum, point.y);
    }
  });

  return Number.isFinite(minimum) && Number.isFinite(maximum)
    ? Math.max(0.5, maximum - minimum)
    : 0.5;
};

describe('first-party character scene bounds', () => {
  it('matches an independent transformed-mesh traversal', () => {
    const geometry = new HgBufferGeometry();
    geometry.setAttribute('position', new HgBufferAttribute(new Float32Array([
      -0.2, 0.1, 0,
       0.3, 1.6, 0.2,
       0.0, 0.8, -0.1,
    ]), 3));
    const mesh = new HgMesh(geometry, new HgStandardMaterial());
    mesh.position.set(0.3, 0.4, -0.2);
    mesh.rotation.z = 0.23;
    mesh.scale.set(1.1, 0.9, 1.2);
    const root = new HgGroup();
    root.add(mesh);

    expect(measureSceneHeight(root)).toBeCloseTo(referenceHeight(root), 6);
  });

  it('matches an independent morph + skin traversal in the bind hierarchy', () => {
    const geometry = new HgBufferGeometry();
    geometry.setAttribute('position', new HgBufferAttribute(new Float32Array([
      0, 0, 0,
      0, 0.8, 0,
      0, 1.6, 0,
    ]), 3));
    geometry.setAttribute('skinIndex', new HgBufferAttribute(new Uint16Array([
      0, 0, 0, 0,
      0, 1, 0, 0,
      1, 0, 0, 0,
    ]), 4));
    geometry.setAttribute('skinWeight', new HgBufferAttribute(new Float32Array([
      1, 0, 0, 0,
      0.5, 0.5, 0, 0,
      1, 0, 0, 0,
    ]), 4));
    const morph = new HgBufferAttribute(new Float32Array([
      0, 0, 0,
      0, 0.15, 0,
      0, 0.2, 0,
    ]), 3);
    geometry.morphAttributes.position = [morph];
    geometry.morphTargetsRelative = true;

    const rootBone = new HgBone();
    const upper = new HgBone();
    upper.position.y = 0.8;
    rootBone.add(upper);

    const mesh = new HgSkinnedMesh(geometry, new HgStandardMaterial());
    mesh.add(rootBone);
    mesh.bind(new HgSkeleton([rootBone, upper]));
    mesh.updateMorphTargets();
    mesh.morphTargetInfluences![0] = 0.65;

    upper.rotation.z = 0.28;
    const root = new HgGroup();
    root.add(mesh);

    expect(measureSceneHeight(root)).toBeCloseTo(referenceHeight(root), 6);
  });
});
