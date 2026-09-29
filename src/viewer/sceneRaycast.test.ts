import { describe, expect, it } from 'vitest';
import {
  BoxGeometry,
  Group,
  Mesh,
  MeshBasicMaterial,
  PerspectiveCamera,
  Raycaster,
  SphereGeometry,
  Vector2,
} from 'three';
import {
  createSceneRay,
  intersectSceneMeshes,
  setSceneRayFromCamera,
} from './sceneRaycast';

describe('first-party scene raycast', () => {
  it('matches Three hit ordering and distance for transformed meshes', () => {
    const camera = new PerspectiveCamera(50, 1.5, 0.1, 100);
    camera.position.set(0.4, 0.3, 5);
    camera.lookAt(0, 0.2, 0);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld(true);

    const root = new Group();
    const near = new Mesh(new BoxGeometry(1, 1, 1), new MeshBasicMaterial());
    near.name = 'near';
    near.position.set(0, 0.1, 0.4);
    near.rotation.y = 0.25;
    const far = new Mesh(new SphereGeometry(0.7, 12, 8), new MeshBasicMaterial());
    far.name = 'far';
    far.position.set(0, 0.1, -1.1);
    root.add(near, far);
    root.updateMatrixWorld(true);

    const ndc = new Vector2(0, 0);
    const three = new Raycaster();
    three.setFromCamera(ndc, camera);
    const expected = three.intersectObjects(root.children, true);

    const ray = createSceneRay();
    setSceneRayFromCamera(ray, camera, ndc.x, ndc.y);
    const actual = intersectSceneMeshes(root.children, ray);

    expect(actual.map((hit) => (hit.object as Mesh).name))
      .toEqual(expected.map((hit) => hit.object.name));
    expect(actual).toHaveLength(expected.length);
    actual.forEach((hit, index) => {
      expect(hit.distance).toBeCloseTo(expected[index].distance, 5);
    });
  });

  it('returns no hit for a ray outside the mesh cluster', () => {
    const camera = new PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.set(0, 0, 4);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld(true);
    const root = new Group();
    root.add(new Mesh(new BoxGeometry(1, 1, 1), new MeshBasicMaterial()));
    root.updateMatrixWorld(true);

    const ray = createSceneRay();
    setSceneRayFromCamera(ray, camera, 0.95, 0.95);
    expect(intersectSceneMeshes(root.children, ray)).toEqual([]);
  });
});
