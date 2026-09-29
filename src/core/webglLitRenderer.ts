import { HgMat4 } from './linearMath';
import type { HgPerspectiveCamera } from './sceneGraph';
import type { HgPrimitiveGeometryData } from './primitiveGeometry';
import type { HgLitTrianglePipeline } from './webglLitTrianglePipeline';
import { hgClipMatrix } from './webglFlatRenderer';

/** Camera-aware lit primitive renderer built on the first-party WebGL pipeline. */
export class HgLitPrimitiveRenderer {
  private readonly clipMatrix = new HgMat4();

  constructor(private readonly triangles: HgLitTrianglePipeline) {}

  draw(
    camera: Pick<HgPerspectiveCamera, 'projectionMatrix' | 'matrixWorldInverse'>,
    world: { readonly elements: ArrayLike<number> },
    geometry: HgPrimitiveGeometryData,
    colour: readonly [number, number, number, number],
  ): void {
    this.triangles.drawPrimitive(
      geometry,
      hgClipMatrix(camera, world, this.clipMatrix),
      world,
      colour,
    );
  }
}
