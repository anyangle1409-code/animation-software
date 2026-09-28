import type { HgSceneSurface } from './sceneLifecycle';

export type HgResizeObserverFactory = (callback: () => void) => Pick<ResizeObserver, 'observe' | 'disconnect'>;

/** DOM event adapter for the renderer-neutral scene lifecycle. Does not create a renderer. */
export function browserSceneSurface(
  canvas: HTMLCanvasElement,
  container: Element,
  browser: Window = window,
  observerFactory: HgResizeObserverFactory = callback => new ResizeObserver(callback),
): HgSceneSurface {
  return {
    measure() {
      const { width, height } = container.getBoundingClientRect();
      return { width, height, devicePixelRatio: browser.devicePixelRatio };
    },
    onResize(callback) {
      const observer = observerFactory(callback);
      observer.observe(container);
      // DPR can change while the CSS dimensions stay constant.
      browser.addEventListener('resize', callback);
      return () => {
        observer.disconnect();
        browser.removeEventListener('resize', callback);
      };
    },
    onContextLost(callback) {
      const handler = (event: Event) => {
        event.preventDefault();
        callback();
      };
      canvas.addEventListener('webglcontextlost', handler);
      return () => canvas.removeEventListener('webglcontextlost', handler);
    },
    onContextRestored(callback) {
      canvas.addEventListener('webglcontextrestored', callback);
      return () => canvas.removeEventListener('webglcontextrestored', callback);
    },
  };
}
