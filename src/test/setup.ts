import { beforeEach } from 'vitest';

/**
 * `GLTFExporter` reaches for `FileReader` when it assembles the binary buffer.
 * Browsers have it; Node does not, so the export tests supply the small part of
 * it the exporter actually uses.
 */
class NodeFileReader {
  result: ArrayBuffer | string | null = null;
  onloadend: (() => void) | null = null;
  onerror: ((error: unknown) => void) | null = null;

  readAsArrayBuffer(blob: Blob): void {
    blob
      .arrayBuffer()
      .then((buffer) => {
        this.result = buffer;
        this.onloadend?.();
      })
      .catch((error) => this.onerror?.(error));
  }

  readAsDataURL(blob: Blob): void {
    blob
      .arrayBuffer()
      .then((buffer) => {
        this.result = `data:${blob.type};base64,${Buffer.from(buffer).toString('base64')}`;
        this.onloadend?.();
      })
      .catch((error) => this.onerror?.(error));
  }
}

if (typeof globalThis.FileReader === 'undefined') {
  (globalThis as { FileReader?: unknown }).FileReader = NodeFileReader;
}

/**
 * Hand the event loop back before every test.
 *
 * The test worker reports progress to the runner over a message port and
 * waits at most 60 s for each reply. A file whose tests only ever await
 * promises that are already settled — building a character from bytes in
 * memory, then measuring it — never returns to the event loop, so the replies
 * sit unread; `selfCollision.test.ts` ran 190 s that way and vitest reported
 * "Timeout calling onTaskUpdate" with every test passing. One macrotask per
 * test lets the replies through. It changes no test's result.
 */
beforeEach(() => new Promise<void>((resolve) => setTimeout(resolve, 0)));
