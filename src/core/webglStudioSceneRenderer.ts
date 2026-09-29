import { HgCharacterMesh } from './sceneCharacter';
import type { HgObject3D, HgPerspectiveCamera } from './sceneGraph';
import type { HgPrimitiveSceneRenderer } from './webglSceneRenderer';
import type { HgCharacterRenderer } from './webglCharacterRenderer';

/**
 * Unified Home Gym PT scene renderer.
 *
 * Primitive overlays/stage and posed character surfaces share one scene graph,
 * camera and WebGL frame. Visibility is inherited for both families.
 */
export class HgStudioSceneRenderer {
  constructor(
    private readonly primitives: Pick<HgPrimitiveSceneRenderer, 'render'>,
    private readonly characters: Pick<HgCharacterRenderer, 'draw'>,
  ) {}

  render(root: HgObject3D, camera: HgPerspectiveCamera): number {
    const primitiveCount = this.primitives.render(root, camera);
    let characterCount = 0;

    const visit = (object: HgObject3D, parentVisible: boolean): void => {
      const visible = parentVisible && object.visible;
      if (!visible) return;
      if (object instanceof HgCharacterMesh) {
        this.characters.draw(
          camera,
          object.matrixWorld,
          object.geometry,
          object.baseColour,
        );
        characterCount += 1;
      }
      for (const child of object.children) visit(child, visible);
    };

    visit(root, true);
    return primitiveCount + characterCount;
  }
}
