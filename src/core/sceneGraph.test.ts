import { describe, expect, it } from 'vitest';
import {
  HgBone,
  HgGroup,
  HgObject3D,
  HgPerspectiveCamera,
  HgScene,
} from './sceneGraph';
import { HgMat4, HgQuat, HgVec3 } from './linearMath';

const close = (one: ArrayLike<number>, two: ArrayLike<number>, epsilon = 1e-10) => {
  expect(one.length).toBe(two.length);
  for (let index = 0; index < one.length; index += 1) {
    expect(Math.abs(one[index] - two[index]), String(index)).toBeLessThan(epsilon);
  }
};

const identity = [
  1, 0, 0, 0,
  0, 1, 0, 0,
  0, 0, 1, 0,
  0, 0, 0, 1,
];

describe('first-party scene graph', () => {
  it('composes hierarchy world transforms and reparenting deterministically', () => {
    const root = new HgGroup();
    const mid = new HgObject3D();
    const child = new HgBone();

    root.position.set(0.3, 1.2, -0.5);
    root.rotation.set(0.2, -0.1, 0.35);
    mid.position.set(-0.2, 0.4, 0.7);
    mid.rotation.set(-0.3, 0.25, 0.1);
    mid.scale.set(1.2, 0.8, 1.1);
    child.position.set(0.1, 0.25, -0.15);
    root.add(mid);
    mid.add(child);
    root.updateMatrixWorld(true);

    const expected = new HgMat4()
      .compose(root.position, root.quaternion, root.scale)
      .multiply(new HgMat4().compose(mid.position, mid.quaternion, mid.scale))
      .multiply(new HgMat4().compose(child.position, child.quaternion, child.scale));
    close(child.matrixWorld.elements, expected.elements);

    const local = new HgVec3(0.2, 0.1, -0.3);
    const world = child.localToWorld(local.clone());
    const expectedWorld = local.clone().applyMatrix4(child.matrixWorld);
    close(world.toArray(), expectedWorld.toArray());

    root.add(child);
    root.updateMatrixWorld(true);
    const reparented = new HgMat4()
      .compose(root.position, root.quaternion, root.scale)
      .multiply(new HgMat4().compose(child.position, child.quaternion, child.scale));
    close(child.matrixWorld.elements, reparented.elements);
    expect(child.parent).toBe(root);
    expect(mid.children).not.toContain(child);
  });

  it('keeps traversal and clear semantics exact', () => {
    const scene = new HgScene();
    const a = new HgGroup(); a.name = 'a';
    const b = new HgObject3D(); b.name = 'b';
    scene.add(a); a.add(b);

    const names: string[] = [];
    scene.traverse((object) => names.push(object.name));
    expect(names).toEqual(['', 'a', 'b']);

    a.clear();
    expect(a.children).toHaveLength(0);
    expect(b.parent).toBeNull();
  });

  it('uses the standard perspective projection formula and an invertible camera view', () => {
    const fov = 38;
    const aspect = 16 / 9;
    const near = 0.05;
    const far = 100;
    const camera = new HgPerspectiveCamera(fov, aspect, near, far);

    const top = near * Math.tan((fov * Math.PI / 180) / 2);
    const height = 2 * top;
    const width = aspect * height;
    const left = -0.5 * width;
    const right = left + width;
    const bottom = top - height;
    const x = 2 * near / (right - left);
    const y = 2 * near / (top - bottom);
    const a = (right + left) / (right - left);
    const b = (top + bottom) / (top - bottom);
    const c = -(far + near) / (far - near);
    const d = -2 * far * near / (far - near);
    close(camera.projectionMatrix.elements, [
      x, 0, 0, 0,
      0, y, 0, 0,
      a, b, c, -1,
      0, 0, d, 0,
    ], 1e-10);

    const projectionIdentity = camera.projectionMatrix.clone()
      .multiply(camera.projectionMatrixInverse);
    close(projectionIdentity.elements, identity, 1e-9);

    camera.position.set(2.3, 1.35, 2.7);
    camera.updateMatrixWorld(true);
    const target = new HgVec3(0, 0.9, 0);
    camera.lookAt(target.x, target.y, target.z);
    camera.updateMatrixWorld(true);

    const viewIdentity = camera.matrixWorld.clone().multiply(camera.matrixWorldInverse);
    close(viewIdentity.elements, identity, 1e-9);

    const forward = new HgVec3(0, 0, -1).applyQuaternion(
      new HgQuat().copy(camera.quaternion),
    ).normalize();
    const desired = target.clone().sub(camera.position).normalize();
    expect(forward.distanceTo(desired)).toBeLessThan(1e-10);
  });
});
