import { describe, expect, it } from 'vitest';
import { boxPrimitiveData } from '../core/primitiveGeometry';
import { HgPerspectiveCamera, HgScene } from '../core/sceneGraph';
import { HgPrimitiveMaterial, HgPrimitiveMesh } from '../core/sceneMesh';
import { HgMat4, HgVec3 } from '../core/linearMath';
import {
  createSceneRay,
  intersectSceneMeshes,
  setSceneRayFromCamera,
  type HgSceneRay,
} from './sceneRaycast';

const boxDistance = (
  ray: HgSceneRay,
  matrixWorld: HgMat4,
  halfExtent = 0.5,
): number | null => {
  const inverse = matrixWorld.clone().invert();
  const origin = ray.origin.clone().applyMatrix4(inverse);
  const localPoint = ray.origin.clone().add(ray.direction).applyMatrix4(inverse);
  const direction = localPoint.sub(origin).normalize();
  let near = -Infinity;
  let far = Infinity;
  for (const axis of ['x', 'y', 'z'] as const) {
    const o = origin[axis];
    const d = direction[axis];
    if (Math.abs(d) < 1e-12) {
      if (o < -halfExtent || o > halfExtent) return null;
      continue;
    }
    const one = (-halfExtent - o) / d;
    const two = (halfExtent - o) / d;
    near = Math.max(near, Math.min(one, two));
    far = Math.min(far, Math.max(one, two));
  }
  if (far < Math.max(near, 0)) return null;
  const localDistance = near >= 0 ? near : far;
  const localHit = direction.clone().multiplyScalar(localDistance).add(origin);
  const worldHit = localHit.applyMatrix4(matrixWorld);
  return worldHit.distanceTo(ray.origin);
};

describe('first-party scene raycast', () => {
  it('matches independent analytic hit ordering and distance for transformed meshes', () => {
    const camera = new HgPerspectiveCamera(50, 1.5, 0.1, 100);
    camera.position.set(0.4, 0.3, 5);
    camera.lookAt(0, 0.2, 0);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld(true);

    const root = new HgScene();
    const near = new HgPrimitiveMesh(
      boxPrimitiveData([1, 1, 1]),
      new HgPrimitiveMaterial('#ffffff'),
    );
    near.name = 'near';
    near.position.set(0, 0.1, 0.4);
    near.rotation.y = 0.25;
    const far = new HgPrimitiveMesh(
      boxPrimitiveData([1.4, 1.4, 1.4]),
      new HgPrimitiveMaterial('#ffffff'),
    );
    far.name = 'far';
    far.position.set(0, 0.1, -1.1);
    far.rotation.y = -0.17;
    root.add(near, far);
    root.updateMatrixWorld(true);

    const ray = createSceneRay();
    setSceneRayFromCamera(ray, camera, 0, 0);
    const expected = [
      { name: near.name, distance: boxDistance(ray, near.matrixWorld)! },
      { name: far.name, distance: boxDistance(ray, far.matrixWorld, 0.7)! },
    ].sort((left, right) => left.distance - right.distance);
    const actual = intersectSceneMeshes(root.children, ray);

    expect(actual.map((hit) => (hit.object as HgPrimitiveMesh).name))
      .toEqual(expected.map((hit) => hit.name));
    expect(actual).toHaveLength(expected.length);
    actual.forEach((hit, index) => {
      expect(hit.distance).toBeCloseTo(expected[index].distance, 3);
    });
  });

  it('returns no hit for a ray outside the mesh cluster', () => {
    const camera = new HgPerspectiveCamera(45, 1, 0.1, 100);
    camera.position.set(0, 0, 4);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld(true);
    const root = new HgScene();
    root.add(new HgPrimitiveMesh(
      boxPrimitiveData([1, 1, 1]),
      new HgPrimitiveMaterial('#ffffff'),
    ));
    root.updateMatrixWorld(true);

    const ray = createSceneRay();
    setSceneRayFromCamera(ray, camera, 0.95, 0.95);
    expect(intersectSceneMeshes(root.children, ray)).toEqual([]);
  });

  it('hits first-party primitive meshes through the renderer-neutral path', () => {
    const camera = new HgPerspectiveCamera(50, 1, 0.1, 100);
    camera.position.set(0, 0, 4);
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld(true);

    const scene = new HgScene();
    const mesh = new HgPrimitiveMesh(
      boxPrimitiveData([1, 1, 1]),
      new HgPrimitiveMaterial('#ffffff'),
    );
    mesh.name = 'first-party-box';
    scene.add(mesh);
    scene.updateMatrixWorld(true);

    const ray = createSceneRay();
    setSceneRayFromCamera(ray, camera, 0, 0);
    const hits = intersectSceneMeshes(scene.children, ray);
    expect(hits).toHaveLength(1);
    expect(hits[0].object).toBe(mesh);
    expect(hits[0].distance).toBeCloseTo(3.5, 5);
  });
});
