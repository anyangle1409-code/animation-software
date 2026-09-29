import type { HgPrimitiveGeometryData } from './primitiveGeometry';
import { HgPrimitiveMesh, type HgRgba } from './sceneMesh';
import type { HgObject3D, HgPerspectiveCamera } from './sceneGraph';

export interface HgPrimitiveRendererPort {
  draw(
    camera: Pick<HgPerspectiveCamera, 'projectionMatrix' | 'matrixWorldInverse'>,
    world: { readonly elements: ArrayLike<number> },
    geometry: HgPrimitiveGeometryData,
    colour: HgRgba,
  ): void;
}

/**
 * Traverse the Home Gym PT scene graph and submit only project-owned primitive
 * mesh nodes. Visibility is inherited: hiding a group hides its full subtree.
 */
export class HgPrimitiveSceneRenderer {
  constructor(
    private readonly lit: HgPrimitiveRendererPort,
    private readonly flat: HgPrimitiveRendererPort,
  ) {}

  render(root: HgObject3D, camera: HgPerspectiveCamera): number {
    root.updateMatrixWorld(true);
    camera.updateWorldMatrix(true, false);
    let count = 0;

    const visit = (object: HgObject3D, parentVisible: boolean) => {
      const visible = parentVisible && object.visible;
      if (!visible) return;

      if (object instanceof HgPrimitiveMesh) {
        const renderer = object.material.shading === 'lit' ? this.lit : this.flat;
        renderer.draw(
          camera,
          object.matrixWorld,
          object.geometry,
          object.material.colour,
        );
        count += 1;
      }

      for (const child of object.children) visit(child, visible);
    };

    visit(root, true);
    return count;
  }
}
