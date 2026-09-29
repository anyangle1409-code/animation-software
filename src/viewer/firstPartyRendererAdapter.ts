import { HgFlatPrimitiveRenderer } from '../core/webglFlatRenderer';
import { HgLitPrimitiveRenderer } from '../core/webglLitRenderer';
import { HgLitTrianglePipeline } from '../core/webglLitTrianglePipeline';
import { HgWebGLRenderer } from '../core/webglRenderer';
import { HgPrimitiveSceneRenderer } from '../core/webglSceneRenderer';
import { HgTrianglePipeline } from '../core/webglTrianglePipeline';
import type { HgPerspectiveCamera, HgScene } from '../core/sceneGraph';

export interface HgFirstPartyRendererPort {
  setPixelRatio(value: number): void;
  setSize(width: number, height: number, updateStyle: boolean): void;
  render(scene: HgScene, camera: HgPerspectiveCamera): void;
  dispose(): void;
}

export interface HgFirstPartyRendererAdapter {
  readonly port: HgFirstPartyRendererPort;
  frame(): number;
  drawCount(): number;
}

interface HgRendererSurfaceLike {
  readonly info: { render: { frame: number } };
  setPixelRatio(value: number): void;
  setSize(width: number, height: number, updateStyle?: boolean): void;
  beginFrame(): void;
  dispose(): void;
}

interface HgSceneRendererLike {
  render(scene: HgScene, camera: HgPerspectiveCamera): number;
}

/**
 * Project-owned renderer orchestration. Kept injectable so the frame/scene
 * contract is testable without a browser WebGL context.
 */
export class HgFirstPartyRendererAdapterCore implements HgFirstPartyRendererAdapter {
  private lastDrawCount = 0;
  private disposed = false;
  readonly port: HgFirstPartyRendererPort;

  constructor(
    private readonly surface: HgRendererSurfaceLike,
    private readonly sceneRenderer: HgSceneRendererLike,
    private readonly disposePipelines: () => void = () => {},
  ) {
    this.port = {
      setPixelRatio: (value) => this.surface.setPixelRatio(value),
      setSize: (width, height, updateStyle) =>
        this.surface.setSize(width, height, updateStyle),
      render: (scene, camera) => {
        if (this.disposed) throw new Error('First-party renderer adapter is disposed');
        this.surface.beginFrame();
        this.lastDrawCount = this.sceneRenderer.render(scene, camera);
      },
      dispose: () => this.dispose(),
    };
  }

  frame(): number {
    return this.surface.info.render.frame;
  }

  drawCount(): number {
    return this.lastDrawCount;
  }

  private dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.disposePipelines();
    this.surface.dispose();
  }
}

/**
 * Browser WebGL2 implementation of the Home Gym PT primitive-scene renderer.
 *
 * Character triangles use the sibling first-party character pipeline and will
 * join this adapter when the live content graph switches from Three objects.
 */
export function createFirstPartyRendererAdapter(
  canvas: HTMLCanvasElement,
): HgFirstPartyRendererAdapter {
  const gl = canvas.getContext('webgl2', {
    antialias: true,
    alpha: true,
    depth: true,
    stencil: false,
  });
  if (!gl) throw new Error('WebGL2 is unavailable');

  const surface = new HgWebGLRenderer(canvas, gl);
  const flatTriangles = new HgTrianglePipeline(gl);
  const litTriangles = new HgLitTrianglePipeline(gl);
  const sceneRenderer = new HgPrimitiveSceneRenderer(
    new HgLitPrimitiveRenderer(litTriangles),
    new HgFlatPrimitiveRenderer(flatTriangles),
  );

  return new HgFirstPartyRendererAdapterCore(
    surface,
    sceneRenderer,
    () => {
      litTriangles.dispose();
      flatTriangles.dispose();
    },
  );
}
