import { describe, expect, it, vi } from 'vitest';
import { HgCharacterMesh } from './sceneCharacter';
import { HgGroup, HgPerspectiveCamera, HgScene } from './sceneGraph';
import { HgStudioSceneRenderer } from './webglStudioSceneRenderer';

describe('unified first-party studio scene renderer', () => {
  it('renders primitive and posed-character nodes in one inherited-visibility scene', () => {
    const primitiveRender = vi.fn(() => 3);
    const characterDraw = vi.fn();
    const renderer = new HgStudioSceneRenderer(
      { render: primitiveRender },
      { draw: characterDraw },
    );
    const scene = new HgScene();
    const group = new HgGroup();
    group.position.set(0.2, 0.1, -0.3);
    scene.add(group);

    const image = {} as TexImageSource;
    const texture = { image, flipY: false };
    const character = new HgCharacterMesh({
      positions: [0, 0, 0, 1, 0, 0, 0, 1, 0],
      normals: [0, 0, 1, 0, 0, 1, 0, 0, 1],
      indices: [0, 1, 2],
    }, [0.8, 0.7, 0.6, 1], texture);
    character.position.set(0, 0.5, 0);
    group.add(character);

    const hidden = new HgGroup();
    hidden.visible = false;
    hidden.add(new HgCharacterMesh({
      positions: [0, 0, 0, 1, 0, 0, 0, 1, 0],
      normals: [0, 0, 1, 0, 0, 1, 0, 0, 1],
      indices: [0, 1, 2],
    }));
    scene.add(hidden);

    const camera = new HgPerspectiveCamera();
    expect(renderer.render(scene, camera)).toBe(4);
    expect(primitiveRender).toHaveBeenCalledWith(scene, camera);
    expect(characterDraw).toHaveBeenCalledTimes(1);
    const [, world, geometry, colour, baseTexture] = characterDraw.mock.calls[0];
    expect(geometry).toBe(character.geometry);
    expect(colour).toBe(character.baseColour);
    expect(baseTexture).toBe(texture);
    expect(world.elements[12]).toBeCloseTo(0.2, 10);
    expect(world.elements[13]).toBeCloseTo(0.6, 10);
    expect(world.elements[14]).toBeCloseTo(-0.3, 10);
  });
});
