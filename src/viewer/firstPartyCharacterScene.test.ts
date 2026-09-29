import { describe, expect, it } from 'vitest';
import { HgBone } from '../core/sceneGraph';
import {
  HgBufferAttribute,
  HgBufferGeometry,
  HgSkeleton,
  HgSkinnedMesh,
  HgStandardMaterial,
} from '../core/sceneSkin';
import { posedCharacterGeometry } from './firstPartyCharacterScene';

describe('first-party posed character scene geometry', () => {
  it('snapshots current morph + skin deformation with UV and vertex-colour data', () => {
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
      1, 1, 0,
      0, 1, 0,
    ]), 3));
    geometry.setAttribute('uv', new HgBufferAttribute(new Float32Array([
      0, 0,
      1, 1,
      0, 1,
    ]), 2));
    geometry.setAttribute('color', new HgBufferAttribute(new Float32Array([
      1, 0, 0,
      0, 1, 0,
      0, 0, 1,
    ]), 3));
    geometry.setAttribute('skinIndex', new HgBufferAttribute(new Uint16Array([
      0, 0, 0, 0,
      1, 0, 0, 0,
      1, 0, 0, 0,
    ]), 4));
    geometry.setAttribute('skinWeight', new HgBufferAttribute(new Float32Array([
      1, 0, 0, 0,
      1, 0, 0, 0,
      1, 0, 0, 0,
    ]), 4));
    geometry.setIndex([0, 1, 2]);

    const morph = new HgBufferAttribute(new Float32Array([
      0, 0, 0,
      0, 0.2, 0,
      0, 0.2, 0,
    ]), 3);
    morph.name = 'bend';
    geometry.morphAttributes.position = [morph];
    geometry.morphTargetsRelative = true;

    const mesh = new HgSkinnedMesh(
      geometry,
      new HgStandardMaterial({ color: '#ffffff', vertexColors: true }),
    );
    mesh.add(root);
    mesh.bind(new HgSkeleton([root, tip]));
    mesh.updateMorphTargets();
    mesh.morphTargetInfluences![0] = 0.5;

    tip.position.y = 1.5;
    root.updateMatrixWorld(true);

    const posed = posedCharacterGeometry(mesh);
    const morphStep = new Float32Array([0.2])[0] * 0.5;
    expect(posed.positions).toEqual([
      0, 0, 0,
      1, 1.5 + morphStep, 0,
      0, 1.5 + morphStep, 0,
    ]);
    expect(posed.indices).toEqual([0, 1, 2]);
    expect(posed.uvs).toEqual([0, 0, 1, 1, 0, 1]);
    expect(posed.colours).toEqual([
      1, 0, 0,
      0, 1, 0,
      0, 0, 1,
    ]);
    expect(posed.normals[2]).toBeCloseTo(1, 9);
    expect(posed.normals[5]).toBeCloseTo(1, 9);
    expect(posed.normals[8]).toBeCloseTo(1, 9);
  });
});
