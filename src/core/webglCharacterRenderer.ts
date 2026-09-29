import { HgMat4 } from './linearMath';
import type { HgPerspectiveCamera } from './sceneGraph';
import type { HgCharacterTriangleGeometry } from './webglCharacterTrianglePipeline';
import type { HgCharacterTrianglePipeline } from './webglCharacterTrianglePipeline';
import { hgClipMatrix } from './webglFlatRenderer';

/** Camera-aware first-party renderer for posed character geometry. */
export class HgCharacterRenderer {
  private readonly clip = new HgMat4();

  constructor(private readonly triangles: HgCharacterTrianglePipeline) {}

  draw(
    camera: Pick<HgPerspectiveCamera, 'projectionMatrix' | 'matrixWorldInverse'>,
    world: { readonly elements: ArrayLike<number> },
    geometry: HgCharacterTriangleGeometry,
    baseColour: readonly [number, number, number, number],
  ): void {
    this.triangles.draw(
      geometry,
      hgClipMatrix(camera, world, this.clip),
      world,
      baseColour,
    );
  }
}
