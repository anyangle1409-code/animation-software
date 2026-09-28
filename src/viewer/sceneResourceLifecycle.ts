import { useEffect, useRef } from 'react';

export interface DisposableSceneResource {
  dispose(): void;
}

export interface DeferredDisposalScheduler {
  schedule(callback: () => void): ReturnType<typeof setTimeout>;
  cancel(handle: ReturnType<typeof setTimeout>): void;
}

const browserScheduler: DeferredDisposalScheduler = {
  schedule: (callback) => setTimeout(callback, 0),
  cancel: (handle) => clearTimeout(handle),
};

/**
 * Delays destructive scene-resource disposal by one task.
 *
 * React Strict Mode intentionally replays effects as setup -> cleanup -> setup
 * in development. Scene resources are memoized across that replay, so disposing
 * synchronously in the first cleanup destroys the same object the second setup
 * is about to reuse. Re-activating the same resource cancels its pending
 * disposal; replacing it with a different resource does not.
 */
export class DeferredSceneResourceDisposer<T extends DisposableSceneResource> {
  private readonly pending = new Map<T, ReturnType<typeof setTimeout>>();

  constructor(private readonly scheduler: DeferredDisposalScheduler = browserScheduler) {}

  activate(resource: T): void {
    const handle = this.pending.get(resource);
    if (handle === undefined) return;
    this.scheduler.cancel(handle);
    this.pending.delete(resource);
  }

  deactivate(resource: T): void {
    if (this.pending.has(resource)) return;
    const handle = this.scheduler.schedule(() => {
      this.pending.delete(resource);
      resource.dispose();
    });
    this.pending.set(resource, handle);
  }
}

/** Strict-Mode-safe lifetime hook for memoized Three scene resources. */
export function useSceneResourceDisposal<T extends DisposableSceneResource>(resource: T): void {
  const disposer = useRef<DeferredSceneResourceDisposer<T> | null>(null);
  if (!disposer.current) disposer.current = new DeferredSceneResourceDisposer<T>();

  useEffect(() => {
    const current = disposer.current!;
    current.activate(resource);
    return () => current.deactivate(resource);
  }, [resource]);
}
