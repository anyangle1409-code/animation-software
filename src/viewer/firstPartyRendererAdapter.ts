import { HgCharacterRenderer } from '../core/webglCharacterRenderer';
import { HgCharacterTrianglePipeline } from '../core/webglCharacterTrianglePipeline';
import { HgFlatPrimitiveRenderer } from '../core/webglFlatRenderer';
import { HgLitPrimitiveRenderer } from '../core/webglLitRenderer';
import { HgLitTrianglePipeline } from '../core/webglLitTrianglePipeline';
import { HgWebGLRenderer } from '../core/webglRenderer';
import { HgPrimitiveSceneRenderer } from '../core/webglSceneRenderer';
import { HgStudioSceneRenderer } from '../core/webglStudioSceneRenderer';
import { HgTrianglePipeline } from '../core/webglTrianglePipeline';
import type { HgPerspectiveCamera, HgScene } from '../core/sceneGraph';
import { hgRgbaFromHex } from '../core/sceneMesh';

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
  setClearColor(r: number, g: number, b: number, a?: number): void;
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
        if (typeof scene.background === 'string') {
          const [r, g, b, a] = hgRgbaFromHex(scene.background);
          this.surface.setClearColor(r, g, b, a);
        }
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
 * Browser WebGL2 implementation of the Home Gym PT studio renderer.
 *
 * Primitive scene nodes and posed-character triangle nodes share the same
 * first-party canvas, frame lifecycle and camera.
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
  const characterTriangles = new HgCharacterTrianglePipeline(gl);
  const primitiveRenderer = new HgPrimitiveSceneRenderer(
    new HgLitPrimitiveRenderer(litTriangles),
    new HgFlatPrimitiveRenderer(flatTriangles),
  );
  const sceneRenderer = new HgStudioSceneRenderer(
    primitiveRenderer,
    new HgCharacterRenderer(characterTriangles),
  );

  return new HgFirstPartyRendererAdapterCore(
    surface,
    sceneRenderer,
    () => {
      characterTriangles.dispose();
      litTriangles.dispose();
      flatTriangles.dispose();
    },
  );
}
