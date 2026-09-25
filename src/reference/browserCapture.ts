import type { ReviewCaptureAdapter } from './captureController';
import { captureReviewBatch } from './captureController';
import type { ReviewCaptureRequest, ReviewImageEvidence } from './evidence';

let adapter: ReviewCaptureAdapter<unknown> | null = null;

export function installBrowserReviewCaptureAdapter(next: ReviewCaptureAdapter<unknown>): () => void {
  adapter = next;
  return () => {
    if (adapter === next) adapter = null;
  };
}

export function browserReviewCaptureAvailable(): boolean {
  return adapter !== null;
}

export async function captureReviewRequests(
  requests: ReviewCaptureRequest[],
): Promise<ReviewImageEvidence[]> {
  if (!adapter) throw new Error('The review capture bridge is not mounted.');
  return captureReviewBatch(requests, adapter);
}
