import { describe, expect, it, vi } from 'vitest';
import { Euler, Matrix4, PerspectiveCamera, Quaternion, Vector3 } from 'three';
import { HgMat4, HgQuat, HgVec3 } from './linearMath';
import { boxPrimitiveData } from './primitiveGeometry';
import { HgPerspectiveCamera } from './sceneGraph';
import { HgFlatPrimitiveRenderer, hgClipMatrix } from './webglFlatRenderer';
import type { HgTrianglePipeline } from './webglTrianglePipeline';

const close = (one: ArrayLike<number>, two: ArrayLike<number>) => {
  expect(one.length).toBe(two.length);
  for (let index = 0; index < one.length; index += 1) {
    expect(Math.abs(one[index] - two[index]), String(index)).toBeLessThan(1e-9);
  }
};

describe('first-party flat primitive renderer', () => {
  it('matches renderer clip-space matrix composition', () => {
    const hgCamera = new HgPerspectiveCamera(38, 16 / 9, 0.05, 100);
    hgCamera.position.set(2.3, 1.35, 2.7);
    hgCamera.updateMatrixWorld(true);
    hgCamera.lookAt(0, 0.9, 0);
    hgCamera.updateMatrixWorld(true);

    const threeCamera = new PerspectiveCamera(38, 16 / 9, 0.05, 100);
    threeCamera.position.set(2.3, 1.35, 2.7);
    threeCamera.lookAt(0, 0.9, 0);
    threeCamera.updateMatrixWorld(true);

    const hgWorld = new HgMat4().compose(
      new HgVec3(0.2, 0.4, -0.3),
      new HgQuat().setFromEulerXYZ(0.1, -0.2, 0.3),
      new HgVec3(1.2, 0.9, 1.1),
    );
    const threeWorld = new Matrix4().compose(
      new Vector3(0.2, 0.4, -0.3),
      new Quaternion().setFromEuler(new Euler(0.1, -0.2, 0.3)),
      new Vector3(1.2, 0.9, 1.1),
    );

    const actual = hgClipMatrix(hgCamera, hgWorld);
    const expected = new Matrix4()
      .copy(threeCamera.projectionMatrix)
      .multiply(threeCamera.matrixWorldInverse)
      .multiply(threeWorld);
    close(actual.elements, expected.elements);
  });

  it('submits shared primitive geometry with the composed clip matrix', () => {
    const drawPrimitive = vi.fn();
    const triangles = { drawPrimitive } as unknown as HgTrianglePipeline;
    const renderer = new HgFlatPrimitiveRenderer(triangles);
    const camera = new HgPerspectiveCamera();
    camera.updateMatrixWorld(true);
    const world = new HgMat4().makeTranslation(0.2, 0.3, -0.4);
    const box = boxPrimitiveData([1, 2, 3]);

    renderer.draw(camera, world, box, [0.1, 0.2, 0.3, 1]);
    expect(drawPrimitive).toHaveBeenCalledTimes(1);
    const [geometry, matrix, colour] = drawPrimitive.mock.calls[0];
    expect(geometry).toBe(box);
    close(matrix.elements, hgClipMatrix(camera, world).elements);
    expect(colour).toEqual([0.1, 0.2, 0.3, 1]);
  });
});
