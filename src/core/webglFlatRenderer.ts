import { HgMat4 } from './linearMath';
import type { HgPerspectiveCamera } from './sceneGraph';
import type { HgPrimitiveGeometryData } from './primitiveGeometry';
import { HgTrianglePipeline } from './webglTrianglePipeline';

/** Compose projection × view × world for the first-party renderer. */
export function hgClipMatrix(
  camera: Pick<HgPerspectiveCamera, 'projectionMatrix' | 'matrixWorldInverse'>,
  world: { readonly elements: ArrayLike<number> },
  target = new HgMat4(),
): HgMat4 {
  return target
    .copy(camera.projectionMatrix)
    .multiply(camera.matrixWorldInverse)
    .multiply(world);
}

export class HgFlatPrimitiveRenderer {
  private readonly clipMatrix = new HgMat4();

  constructor(private readonly triangles: HgTrianglePipeline) {}

  draw(
    camera: Pick<HgPerspectiveCamera, 'projectionMatrix' | 'matrixWorldInverse'>,
    world: { readonly elements: ArrayLike<number> },
    geometry: HgPrimitiveGeometryData,
    colour: readonly [number, number, number, number],
  ): void {
    this.triangles.drawPrimitive(
      geometry,
      hgClipMatrix(camera, world, this.clipMatrix),
      colour,
    );
  }
}
