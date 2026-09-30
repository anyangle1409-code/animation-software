import { describe, expect, it, vi } from 'vitest';
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

const multiply4 = (a: ArrayLike<number>, b: ArrayLike<number>): number[] => {
  const out = Array<number>(16).fill(0);
  for (let column = 0; column < 4; column += 1) {
    for (let row = 0; row < 4; row += 1) {
      let value = 0;
      for (let k = 0; k < 4; k += 1) {
        value += a[k * 4 + row] * b[column * 4 + k];
      }
      out[column * 4 + row] = value;
    }
  }
  return out;
};

describe('first-party flat primitive renderer', () => {
  it('matches an independent scalar clip-space matrix composition', () => {
    const camera = new HgPerspectiveCamera(38, 16 / 9, 0.05, 100);
    camera.position.set(2.3, 1.35, 2.7);
    camera.updateMatrixWorld(true);
    camera.lookAt(0, 0.9, 0);
    camera.updateMatrixWorld(true);

    const world = new HgMat4().compose(
      new HgVec3(0.2, 0.4, -0.3),
      new HgQuat().setFromEulerXYZ(0.1, -0.2, 0.3),
      new HgVec3(1.2, 0.9, 1.1),
    );
    const actual = hgClipMatrix(camera, world);
    const expected = multiply4(
      multiply4(camera.projectionMatrix.elements, camera.matrixWorldInverse.elements),
      world.elements,
    );
    close(actual.elements, expected);
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
