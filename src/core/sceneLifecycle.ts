import { HgFrameLoop } from './frameLoop';
import type { HgFrameCallback, HgFrameScheduler } from './frameLoop';

export interface HgSceneSize {
  width: number;
  height: number;
  pixelRatio: number;
}

/** Browser event plumbing is provided by an adapter; this contract owns no WebGL. */
export interface HgSceneSurface {
  measure(): { width: number; height: number; devicePixelRatio: number };
  onResize(callback: () => void): () => void;
  onContextLost(callback: () => void): () => void;
  onContextRestored(callback: () => void): () => void;
}

/** One scene lifetime, one ordered frame loop, and no dependency on R3F/Three. */
export class HgSceneLifecycle {
  private readonly loop: HgFrameLoop;
  private readonly unsubscribe: Array<() => void> = [];
  private mounted = false;
  private disposed = false;
  private contextLost = false;

  constructor(
    scheduler: HgFrameScheduler,
    private readonly surface: HgSceneSurface,
    private readonly applySize: (size: HgSceneSize) => void,
  ) {
    this.loop = new HgFrameLoop(scheduler);
  }

  onFrame(callback: HgFrameCallback, priority = 0): () => void {
    if (this.disposed) throw new Error('Scene lifecycle is disposed');
    return this.loop.add(callback, priority);
  }

  mount(): void {
    if (this.disposed) throw new Error('Scene lifecycle is disposed');
    if (this.mounted) return;
    this.mounted = true;
    this.unsubscribe.push(
      this.surface.onResize(() => this.refresh()),
      this.surface.onContextLost(() => {
        this.contextLost = true;
        this.loop.stop();
      }),
      this.surface.onContextRestored(() => {
        this.contextLost = false;
        this.refresh();
      }),
    );
    this.refresh();
  }

  private refresh(): void {
    if (!this.mounted || this.disposed) return;
    const { width, height, devicePixelRatio } = this.surface.measure();
    if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
      this.loop.stop();
      return;
    }
    const pixelRatio = Number.isFinite(devicePixelRatio)
      ? Math.max(1, Math.min(2, devicePixelRatio)) : 1;
    if (!this.contextLost) {
      this.applySize({ width, height, pixelRatio });
      this.loop.start();
    }
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.loop.stop();
    for (const remove of this.unsubscribe.splice(0)) remove();
  }
}
