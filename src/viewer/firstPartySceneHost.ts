import { HgPerspectiveCamera, HgScene } from '../core/sceneGraph';
import { HgSceneLifecycle } from '../core/sceneLifecycle';
import type { HgSceneSurface } from '../core/sceneLifecycle';
import type { HgFrameCallback, HgFrameScheduler } from '../core/frameLoop';
import type { HgFirstPartyRendererPort } from './firstPartyRendererAdapter';

/**
 * First-party replacement for ThreeSceneHost.
 *
 * Camera, scene, lifecycle and frame ordering are all Home Gym PT-owned.
 */
export class FirstPartySceneHost {
  readonly scene = new HgScene();
  readonly camera = new HgPerspectiveCamera(38, 1, 0.05, 100);
  private readonly lifecycle: HgSceneLifecycle;
  private disposed = false;

  constructor(
    scheduler: HgFrameScheduler,
    surface: HgSceneSurface,
    private readonly renderer: HgFirstPartyRendererPort,
  ) {
    this.camera.position.set(2.3, 1.35, 2.7);
    this.camera.lookAt(0, 0, 0);
    this.lifecycle = new HgSceneLifecycle(
      scheduler,
      surface,
      ({ width, height, pixelRatio }) => {
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setPixelRatio(pixelRatio);
        this.renderer.setSize(width, height, false);
      },
    );
    this.lifecycle.onFrame(
      () => this.renderer.render(this.scene, this.camera),
      1000,
    );
  }

  onFrame(callback: HgFrameCallback, priority = 0): () => void {
    if (priority >= 1000) {
      throw new Error('Scene consumer priority must precede render');
    }
    return this.lifecycle.onFrame(callback, priority);
  }

  mount(): void {
    this.lifecycle.mount();
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.lifecycle.dispose();
    this.renderer.dispose();
  }
}
