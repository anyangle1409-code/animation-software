import { describe, expect, it, vi } from 'vitest';
import { boxPrimitiveData, spherePrimitiveData } from './primitiveGeometry';
import {
  HgPrimitiveMaterial,
  HgPrimitiveMesh,
  hgRgbaFromHex,
} from './sceneMesh';
import { HgGroup, HgPerspectiveCamera, HgScene } from './sceneGraph';
import { HgPrimitiveSceneRenderer } from './webglSceneRenderer';

describe('first-party primitive scene rendering', () => {
  it('parses deterministic renderer-neutral colours and mutable opacity', () => {
    expect(hgRgbaFromHex('#8fa3bf')).toEqual([
      0x8f / 255,
      0xa3 / 255,
      0xbf / 255,
      1,
    ]);
    expect(hgRgbaFromHex('#abc', 0.5)).toEqual([
      0xaa / 255,
      0xbb / 255,
      0xcc / 255,
      0.5,
    ]);
    const material = new HgPrimitiveMaterial('#123456');
    material.setOpacity(0.4).setColour('#ffffff');
    expect(material.colour).toEqual([1, 1, 1, 0.4]);
    expect(() => hgRgbaFromHex('red')).toThrow(/#rgb/);
  });

  it('traverses lit and flat project meshes with inherited visibility', () => {
    const litDraw = vi.fn();
    const flatDraw = vi.fn();
    const renderer = new HgPrimitiveSceneRenderer(
      { draw: litDraw },
      { draw: flatDraw },
    );
    const scene = new HgScene();
    const group = new HgGroup();
    group.position.set(0.2, 0.4, -0.1);
    scene.add(group);

    const lit = new HgPrimitiveMesh(
      boxPrimitiveData([0.4, 0.2, 0.3]),
      new HgPrimitiveMaterial('#8fa3bf', 'lit'),
    );
    lit.position.set(0, 0.5, 0);
    group.add(lit);

    const flat = new HgPrimitiveMesh(
      spherePrimitiveData(0.05, 8, 6),
      new HgPrimitiveMaterial('#ffb43a', 'flat'),
    );
    flat.position.set(0.1, 0.2, 0.3);
    group.add(flat);

    const hiddenGroup = new HgGroup();
    hiddenGroup.visible = false;
    hiddenGroup.add(new HgPrimitiveMesh(
      boxPrimitiveData([1, 1, 1]),
      new HgPrimitiveMaterial('#ffffff'),
    ));
    scene.add(hiddenGroup);

    const camera = new HgPerspectiveCamera(38, 16 / 9, 0.05, 100);
    camera.position.set(2.3, 1.35, 2.7);
    camera.lookAt(0, 0.8, 0);

    expect(renderer.render(scene, camera)).toBe(2);
    expect(litDraw).toHaveBeenCalledTimes(1);
    expect(flatDraw).toHaveBeenCalledTimes(1);

    const [, litWorld, litGeometry, litColour] = litDraw.mock.calls[0];
    expect(litGeometry).toBe(lit.geometry);
    expect(litColour).toBe(lit.material.colour);
    expect(litWorld.elements[12]).toBeCloseTo(0.2, 10);
    expect(litWorld.elements[13]).toBeCloseTo(0.9, 10);
    expect(litWorld.elements[14]).toBeCloseTo(-0.1, 10);
  });

  it('skips an individually hidden mesh without visiting its renderer', () => {
    const draw = vi.fn();
    const renderer = new HgPrimitiveSceneRenderer({ draw }, { draw });
    const scene = new HgScene();
    const mesh = new HgPrimitiveMesh(
      boxPrimitiveData([1, 1, 1]),
      new HgPrimitiveMaterial('#ffffff'),
    );
    mesh.visible = false;
    scene.add(mesh);
    expect(renderer.render(scene, new HgPerspectiveCamera())).toBe(0);
    expect(draw).not.toHaveBeenCalled();
  });
  it('keeps alpha-zero pointer hit meshes in the scene but out of draw submission', () => {
    const litDraw = vi.fn();
    const flatDraw = vi.fn();
    const renderer = new HgPrimitiveSceneRenderer(
      { draw: litDraw },
      { draw: flatDraw },
    );
    const scene = new HgScene();
    const hiddenHit = new HgPrimitiveMesh(
      boxPrimitiveData([1, 1, 1]),
      new HgPrimitiveMaterial('#ffffff', 'flat').setOpacity(0),
    );
    scene.add(hiddenHit);
    const count = renderer.render(scene, new HgPerspectiveCamera());
    expect(count).toBe(0);
    expect(flatDraw).not.toHaveBeenCalled();
    expect(hiddenHit.visible).toBe(true);
  });

});
