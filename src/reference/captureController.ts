import type { ReviewCaptureRequest, ReviewImageEvidence, ReviewImageEvidenceMeta } from './evidence';

export interface CapturedPng {
  bytes: Uint8Array | ArrayBuffer | Blob;
  width: number;
  height: number;
}

export interface ReviewCaptureAdapter<StateSnapshot = unknown> {
  /** Save all viewport/editor state that the batch is allowed to change. */
  snapshot(): StateSnapshot | Promise<StateSnapshot>;
  /** Pause, seek, set camera/view and hide editor-only overlays for one request. */
  apply(request: ReviewCaptureRequest): void | Promise<void>;
  /**
   * Wait until the requested time/camera/character state has actually reached
   * the renderer. The bridge decides whether that is one frame, two frames or
   * another deterministic barrier.
   */
  settle(request: ReviewCaptureRequest): void | Promise<void>;
  /** Read the already-rendered local canvas as PNG bytes. */
  capturePng(request: ReviewCaptureRequest): CapturedPng | Promise<CapturedPng>;
  /** Restore the exact user state even when a capture fails. */
  restore(snapshot: StateSnapshot): void | Promise<void>;
}

export interface CaptureBatchProgress {
  index: number;
  total: number;
  request: ReviewCaptureRequest;
}

/**
 * Capture one deterministic local review batch.
 *
 * Policy (semantic moments/cameras) is already resolved in the requests. This
 * controller only guarantees ordered execution and state restoration.
 */
export async function captureReviewBatch<StateSnapshot>(
  requests: ReviewCaptureRequest[],
  adapter: ReviewCaptureAdapter<StateSnapshot>,
  onProgress?: (progress: CaptureBatchProgress) => void,
): Promise<ReviewImageEvidence[]> {
  const snapshot = await adapter.snapshot();
  const evidence: ReviewImageEvidence[] = [];

  try {
    for (let index = 0; index < requests.length; index += 1) {
      const request = requests[index];
      onProgress?.({ index, total: requests.length, request });
      await adapter.apply(request);
      await adapter.settle(request);
      const captured = await adapter.capturePng(request);
      const meta: ReviewImageEvidenceMeta = {
        referenceId: request.referenceId,
        exerciseId: request.exerciseId,
        captureId: request.captureId,
        momentId: request.momentId,
        time: request.time,
        normalizedTime: request.normalizedTime,
        viewId: request.viewId,
        width: captured.width,
        height: captured.height,
        mimeType: 'image/png',
      };
      evidence.push({ ...meta, image: captured.bytes });
    }
    return evidence;
  } finally {
    await adapter.restore(snapshot);
  }
}
