/**
 * Home Gym PT first-party animation-frame scheduler.
 *
 * R3F currently supplies the outer render tick. HgFrameDispatcher owns the
 * deterministic project-consumer ordering independently of that host, while
 * HgFrameLoop adds an optional requestAnimationFrame-style scheduler for the
 * future first-party host.
 */

export interface HgFrame {
  /** Seconds since the previous frame. */
  delta: number;
  /** Seconds since this loop started. */
  elapsed: number;
  /** Original scheduler timestamp in milliseconds. */
  timestampMs: number;
}

export type HgFrameCallback = (frame: HgFrame) => void;

export interface HgFrameScheduler {
  request(callback: (timestampMs: number) => void): number;
  cancel(handle: number): void;
}

interface Entry {
  id: number;
  priority: number;
  order: number;
  callback: HgFrameCallback;
}

export class HgFrameDispatcher {
  private readonly entries = new Map<number, Entry>();
  private nextId = 1;
  private nextOrder = 1;

  add(callback: HgFrameCallback, priority = 0): () => void {
    const id = this.nextId++;
    this.entries.set(id, { id, priority, order: this.nextOrder++, callback });
    return () => {
      this.entries.delete(id);
    };
  }

  dispatch(frame: HgFrame): void {
    const ordered = [...this.entries.values()].sort(
      (a, b) => a.priority - b.priority || a.order - b.order,
    );
    for (const entry of ordered) {
      if (this.entries.has(entry.id)) entry.callback(frame);
    }
  }

  get subscriberCount(): number {
    return this.entries.size;
  }
}

export class HgFrameLoop {
  private readonly consumers = new HgFrameDispatcher();
  private running = false;
  private handle: number | null = null;
  private startedAt: number | null = null;
  private previousAt: number | null = null;

  constructor(private readonly scheduler: HgFrameScheduler) {}

  add(callback: HgFrameCallback, priority = 0): () => void {
    return this.consumers.add(callback, priority);
  }

  /** Run one frame manually. Useful for deterministic tests and headless tools. */
  tick(timestampMs: number): void {
    if (!Number.isFinite(timestampMs)) throw new Error('Frame timestamp must be finite');

    if (this.startedAt === null) this.startedAt = timestampMs;
    const previous = this.previousAt ?? timestampMs;
    this.previousAt = timestampMs;

    this.consumers.dispatch({
      delta: Math.max(0, (timestampMs - previous) / 1000),
      elapsed: Math.max(0, (timestampMs - this.startedAt) / 1000),
      timestampMs,
    });
  }

  start(): void {
    if (this.running) return;
    this.running = true;
    this.startedAt = null;
    this.previousAt = null;

    const next = (timestampMs: number) => {
      if (!this.running) return;
      this.tick(timestampMs);
      if (this.running) this.handle = this.scheduler.request(next);
    };

    this.handle = this.scheduler.request(next);
  }

  stop(): void {
    if (!this.running) return;
    this.running = false;
    if (this.handle !== null) this.scheduler.cancel(this.handle);
    this.handle = null;
    this.startedAt = null;
    this.previousAt = null;
  }

  get isRunning(): boolean {
    return this.running;
  }

  get subscriberCount(): number {
    return this.consumers.subscriberCount;
  }
}

export function browserFrameScheduler(): HgFrameScheduler {
  if (
    typeof globalThis.requestAnimationFrame !== 'function' ||
    typeof globalThis.cancelAnimationFrame !== 'function'
  ) {
    throw new Error('requestAnimationFrame is unavailable in this environment');
  }

  return {
    request: (callback) => globalThis.requestAnimationFrame(callback),
    cancel: (handle) => globalThis.cancelAnimationFrame(handle),
  };
}
