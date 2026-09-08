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
