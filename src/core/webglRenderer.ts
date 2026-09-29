export interface HgWebGLContextPort {
  readonly COLOR_BUFFER_BIT: number;
  readonly DEPTH_BUFFER_BIT: number;
  readonly DEPTH_TEST: number;
  viewport(x: number, y: number, width: number, height: number): void;
  clearColor(r: number, g: number, b: number, a: number): void;
  enable(capability: number): void;
  clear(mask: number): void;
  getExtension(name: string): { loseContext?(): void } | null;
}

export interface HgWebGLCanvasPort {
  width: number;
  height: number;
  style: { width: string; height: string };
  getContext(
    type: 'webgl2',
    attributes?: WebGLContextAttributes,
  ): WebGL2RenderingContext | null;
}

export interface HgWebGLRendererInfo {
  render: { frame: number };
}

/**
 * First-party browser WebGL surface/lifecycle foundation.
 *
 * This owns canvas sizing, DPR, depth-buffer setup, deterministic frame
 * accounting and disposal without a rendering library. Mesh/material drawing
 * is added separately before this replaces the live Three renderer.
 */
export class HgWebGLRenderer {
  readonly info: HgWebGLRendererInfo = { render: { frame: 0 } };
  private pixelRatio = 1;
  private width = 1;
  private height = 1;
  private clear = [0, 0, 0, 0] as [number, number, number, number];
  private disposed = false;

  constructor(
    private readonly canvas: HgWebGLCanvasPort,
    private readonly gl: HgWebGLContextPort =
      canvas.getContext('webgl2', {
        antialias: true,
        alpha: true,
        depth: true,
        stencil: false,
      }) as unknown as HgWebGLContextPort,
  ) {
    if (!gl) throw new Error('WebGL2 is unavailable');
    gl.enable(gl.DEPTH_TEST);
    this.resizeDrawingBuffer();
  }

  setPixelRatio(value: number): void {
    this.assertActive();
    this.pixelRatio = Math.max(0.1, Number.isFinite(value) ? value : 1);
    this.resizeDrawingBuffer();
  }

  setSize(width: number, height: number, updateStyle = true): void {
    this.assertActive();
    this.width = Math.max(1, Math.round(width));
    this.height = Math.max(1, Math.round(height));
    if (updateStyle) {
      this.canvas.style.width = this.width + 'px';
      this.canvas.style.height = this.height + 'px';
    }
    this.resizeDrawingBuffer();
  }

  setClearColor(r: number, g: number, b: number, a = 1): void {
    this.assertActive();
    this.clear = [r, g, b, a];
  }

  /**
   * Begin one renderer frame by setting viewport/depth state and clearing the
   * native drawing buffer. Draw submission will build on this exact boundary.
   */
  beginFrame(): void {
    this.assertActive();
    const [r, g, b, a] = this.clear;
    this.gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    this.gl.enable(this.gl.DEPTH_TEST);
    this.gl.clearColor(r, g, b, a);
    this.gl.clear(this.gl.COLOR_BUFFER_BIT | this.gl.DEPTH_BUFFER_BIT);
    this.info.render.frame += 1;
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.gl.getExtension('WEBGL_lose_context')?.loseContext?.();
  }

  private resizeDrawingBuffer(): void {
    const width = Math.max(1, Math.round(this.width * this.pixelRatio));
    const height = Math.max(1, Math.round(this.height * this.pixelRatio));
    this.canvas.width = width;
    this.canvas.height = height;
    this.gl.viewport(0, 0, width, height);
  }

  private assertActive(): void {
    if (this.disposed) throw new Error('WebGL renderer is disposed');
  }
}
