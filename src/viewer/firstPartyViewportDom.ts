import { characterStore } from '../editor/characterStoreCore';
import { skeleton, studioStore } from '../editor/storeCore';
import { createFirstPartyViewportRuntime } from './firstPartyViewportRuntime';
import { createSceneState } from './sceneStateCore';
import { createStudioSceneController } from './studioSceneController';
import { createNativeWebGL2SkeletonPreview } from './nativeWebGL2SkeletonPreviewRuntime';

type DocumentPort = Pick<Document, 'createElement'>;

export interface FirstPartyViewportDomDependencies {
  createSceneState: typeof createSceneState;
  createRuntime: typeof createFirstPartyViewportRuntime;
  createController: typeof createStudioSceneController;
}

export interface FirstPartyViewportDom {
  element: HTMLDivElement;
  canvas: HTMLCanvasElement;
  dispose(): void;
}

const DEFAULT_DEPENDENCIES: FirstPartyViewportDomDependencies = {
  createSceneState,
  createRuntime: createFirstPartyViewportRuntime,
  createController: createStudioSceneController,
};

/**
 * Framework-neutral DOM/lifecycle wrapper for the already-first-party viewport.
 *
 * This owns only the host/canvas nodes and the runtime/controller lifetime that
 * the temporary React wrapper previously owned. Renderer, frame, pointer,
 * camera/orbit, gizmos and scene composition stay on their existing runtimes.
 */
export function createFirstPartyViewportDom(
  documentRef: DocumentPort = document,
  dependencies: FirstPartyViewportDomDependencies = DEFAULT_DEPENDENCIES,
): FirstPartyViewportDom {
  const scene = dependencies.createSceneState();

  const container = documentRef.createElement('div');
  container.dataset.hgptSceneHost = 'first-party';
  container.style.width = '100%';
  container.style.height = '100%';
  container.style.minHeight = '0';
  container.style.position = 'relative';

  const canvas = documentRef.createElement('canvas');
  canvas.style.display = 'block';
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  container.append(canvas);

  // Opt-in, dev-only comparison of actual FK exercise animation without Three.
  // This does not replace the production editor's mesh/skin, gizmos or picking.
  // Do NOT enable by default until graphical and exercise parity gates pass.
  if (
    import.meta.env.DEV &&
    typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).get('hgptNativeSkeletonPreview') === '1'
  ) {
    const preview = createNativeWebGL2SkeletonPreview(container, canvas, scene);
    container.dataset.hgptNativeViewport = 'skeleton-only-experimental';
    let nativeDisposed = false;
    return {
      element: container,
      canvas,
      dispose() {
        if (nativeDisposed) return;
        nativeDisposed = true;
        preview.dispose();
      },
    };
  }

  const runtime = dependencies.createRuntime(container, canvas, scene);
  const controller = dependencies.createController({
    sceneState: scene,
    bindings: runtime.bindings,
    studioStore,
    characterStore,
    skeleton,
  });

  let disposed = false;
  return {
    element: container,
    canvas,
    dispose() {
      if (disposed) return;
      disposed = true;
      // Preserve the existing React effect cleanup order.
      controller.dispose();
      runtime.dispose();
    },
  };
}
