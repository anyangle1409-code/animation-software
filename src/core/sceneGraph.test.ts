import { describe, expect, it } from 'vitest';
import {
  Bone,
  Group,
  Object3D,
  PerspectiveCamera,
  Quaternion,
  Scene,
  Vector3,
} from 'three';
import {
  HgBone,
  HgGroup,
  HgObject3D,
  HgPerspectiveCamera,
  HgScene,
} from './sceneGraph';

const close = (one: ArrayLike<number>, two: ArrayLike<number>, epsilon = 1e-10) => {
  expect(one.length).toBe(two.length);
  for (let index = 0; index < one.length; index += 1) {
    expect(Math.abs(one[index] - two[index]), String(index)).toBeLessThan(epsilon);
  }
};

describe('first-party scene graph parity', () => {
  it('matches hierarchy world transforms and reparenting', () => {
    const hgRoot = new HgGroup();
    const hgMid = new HgObject3D();
    const hgChild = new HgBone();
    const threeRoot = new Group();
    const threeMid = new Object3D();
    const threeChild = new Bone();

    hgRoot.position.set(0.3, 1.2, -0.5);
    threeRoot.position.set(0.3, 1.2, -0.5);
    hgRoot.rotation.set(0.2, -0.1, 0.35);
    threeRoot.rotation.set(0.2, -0.1, 0.35);

    hgMid.position.set(-0.2, 0.4, 0.7);
    threeMid.position.set(-0.2, 0.4, 0.7);
    hgMid.rotation.set(-0.3, 0.25, 0.1);
    threeMid.rotation.set(-0.3, 0.25, 0.1);
    hgMid.scale.set(1.2, 0.8, 1.1);
    threeMid.scale.set(1.2, 0.8, 1.1);

    hgChild.position.set(0.1, 0.25, -0.15);
    threeChild.position.set(0.1, 0.25, -0.15);
    hgRoot.add(hgMid);
    hgMid.add(hgChild);
    threeRoot.add(threeMid);
    threeMid.add(threeChild);

    hgRoot.updateMatrixWorld(true);
    threeRoot.updateMatrixWorld(true);
    close(hgChild.matrixWorld.elements, threeChild.matrixWorld.elements, 1e-10);

    const hgPoint = hgChild.localToWorld(new HgVec3(0.2, 0.1, -0.3));
    const threePoint = threeChild.localToWorld(new Vector3(0.2, 0.1, -0.3));
    close(hgPoint.toArray(), threePoint.toArray(), 1e-10);

    hgRoot.add(hgChild);
    threeRoot.add(threeChild);
    hgRoot.updateMatrixWorld(true);
    threeRoot.updateMatrixWorld(true);
    close(hgChild.matrixWorld.elements, threeChild.matrixWorld.elements, 1e-10);
  });

  it('matches scene traversal and clear semantics', () => {
    const hg = new HgScene();
    const three = new Scene();
    const hgA = new HgGroup(); hgA.name = 'a';
    const hgB = new HgObject3D(); hgB.name = 'b';
    const threeA = new Group(); threeA.name = 'a';
    const threeB = new Object3D(); threeB.name = 'b';
    hg.add(hgA); hgA.add(hgB);
    three.add(threeA); threeA.add(threeB);

    const hgNames: string[] = [];
    const threeNames: string[] = [];
    hg.traverse((object) => hgNames.push(object.name));
    three.traverse((object) => threeNames.push(object.name));
    expect(hgNames).toEqual(threeNames);

    hgA.clear();
    threeA.clear();
    expect(hgA.children).toHaveLength(0);
    expect(hgB.parent).toBeNull();
    expect(threeB.parent).toBeNull();
  });

  it('matches perspective projection and camera lookAt', () => {
    const hg = new HgPerspectiveCamera(38, 16 / 9, 0.05, 100);
    const three = new PerspectiveCamera(38, 16 / 9, 0.05, 100);
    close(hg.projectionMatrix.elements, three.projectionMatrix.elements, 1e-10);

    hg.position.set(2.3, 1.35, 2.7);
    three.position.set(2.3, 1.35, 2.7);
    hg.updateMatrixWorld(true);
    three.updateMatrixWorld(true);
    hg.lookAt(0, 0.9, 0);
    three.lookAt(0, 0.9, 0);
    hg.updateMatrixWorld(true);
    three.updateMatrixWorld(true);

    const hq = hg.quaternion.clone().normalize();
    const tq = new Quaternion().copy(three.quaternion).normalize();
    const dot = Math.abs(hq.x * tq.x + hq.y * tq.y + hq.z * tq.z + hq.w * tq.w);
    expect(1 - dot).toBeLessThan(1e-10);
    close(hg.matrixWorldInverse.elements, three.matrixWorldInverse.elements, 1e-10);
  });
});
