import { describe, expect, it } from 'vitest';
import { HgVec3 } from './linearMath';
import { HgBone } from './sceneGraph';
import {
  HgBufferAttribute,
  HgBufferGeometry,
  HgSkeleton,
  HgSkinnedMesh,
  HgStandardMaterial,
} from './sceneSkin';
import { posedLocalVertex } from '../character/skinningMath';

describe('first-party scene skin structures', () => {
  it('supports mutable attributes, normals and deterministic bounds', () => {
    const geometry = new HgBufferGeometry();
    const position = new HgBufferAttribute(new Float32Array([
      0, 0, 0,
      1, 0, 0,
      0, 1, 0,
    ]), 3);
    geometry.setAttribute('position', position);
    geometry.setIndex([0, 1, 2]);
    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    geometry.computeBoundingSphere();

    expect(geometry.getAttribute('normal')?.getZ(0)).toBeCloseTo(1, 9);
    expect(geometry.boundingBox?.min.toArray()).toEqual([0, 0, 0]);
    expect(geometry.boundingBox?.max.toArray()).toEqual([1, 1, 0]);
    expect(geometry.boundingSphere?.center.toArray()).toEqual([0.5, 0.5, 0]);

    position.setXYZ(1, 2, 0, 0);
    position.needsUpdate = true;
    expect(position.getX(1)).toBe(2);
    expect(position.needsUpdate).toBe(true);
  });

  it('binds a skeleton and produces the expected skinned + morphed vertex', () => {
    const root = new HgBone();
    root.name = 'root';
    const tip = new HgBone();
    tip.name = 'tip';
    tip.position.set(0, 1, 0);
    root.add(tip);
    root.updateMatrixWorld(true);

    const geometry = new HgBufferGeometry();
    geometry.setAttribute('position', new HgBufferAttribute(new Float32Array([
      0, 0, 0,
      0, 1, 0,
    ]), 3));
    geometry.setAttribute('skinIndex', new HgBufferAttribute(new Uint16Array([
      0, 0, 0, 0,
      1, 0, 0, 0,
    ]), 4));
    geometry.setAttribute('skinWeight', new HgBufferAttribute(new Float32Array([
      1, 0, 0, 0,
      1, 0, 0, 0,
    ]), 4));
    const morph = new HgBufferAttribute(new Float32Array([
      0, 0, 0,
      0, 0.2, 0,
    ]), 3);
    morph.name = 'stretch';
    geometry.morphAttributes.position = [morph];
    geometry.morphTargetsRelative = true;

    const mesh = new HgSkinnedMesh(geometry, new HgStandardMaterial());
    mesh.add(root);
    mesh.bind(new HgSkeleton([root, tip]));
    mesh.updateMorphTargets();
    mesh.morphTargetInfluences![0] = 0.5;

    tip.position.y = 1.5;
    root.updateMatrixWorld(true);
    const point = posedLocalVertex(mesh, 1, new HgVec3());

    // Vertex starts at y=1, gains 0.1 morph, then follows the tip's +0.5 move.
    expect(point.x).toBeCloseTo(0, 9);
    const storedMorph = new Float32Array([0.2])[0];
    expect(point.y).toBe(1.5 + storedMorph * 0.5);
    expect(point.z).toBeCloseTo(0, 9);
    expect(mesh.morphTargetDictionary).toEqual({ stretch: 0 });
  });

  it('preserves presentation material state without renderer objects', () => {
    const material = new HgStandardMaterial({
      color: '#ffffff',
      vertexColors: true,
      roughness: 0.68,
      metalness: 0.02,
    });
    material.color.set('#336699');
    material.opacity = 0.4;
    material.transparent = true;
    material.depthWrite = false;

    expect([material.color.r, material.color.g, material.color.b]).toEqual([
      0x33 / 255,
      0x66 / 255,
      0x99 / 255,
    ]);
    expect(material.vertexColors).toBe(true);
    expect(material.roughness).toBe(0.68);
    expect(material.metalness).toBe(0.02);
    expect(material.opacity).toBe(0.4);
    expect(material.transparent).toBe(true);
    expect(material.depthWrite).toBe(false);
  });
});
