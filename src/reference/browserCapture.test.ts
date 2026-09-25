import { describe, expect, it } from 'vitest';
import {
  browserReviewCaptureAvailable,
  captureReviewRequests,
  installBrowserReviewCaptureAdapter,
} from './browserCapture';
import type { ReviewCaptureRequest } from './evidence';

const request: ReviewCaptureRequest = {
  referenceId: 'curl.standing.supinated.v1',
  exerciseId: 'generated_test',
  captureId: 'start__front',
  momentId: 'start',
  time: 0,
  normalizedTime: 0,
  viewId: 'front',
  renderMode: 'beauty',
  camera: { preset: 'front', target: 'full_body' },
  viewport: {
    width: 64,
    height: 64,
    dpr: 1,
    backdrop: 'review_neutral',
    showGrid: false,
    showGizmos: false,
    showIkHandles: false,
    viewMode: 'character',
  },
};

describe('browser review capture registry', () => {
  it('routes a batch through the mounted adapter and can be removed', async () => {
    const uninstall = installBrowserReviewCaptureAdapter({
      snapshot: () => ({ saved: true }),
      apply: () => undefined,
      settle: () => undefined,
      capturePng: () => ({ bytes: new Uint8Array([1]), width: 64, height: 64 }),
      restore: () => undefined,
    });

    expect(browserReviewCaptureAvailable()).toBe(true);
    const evidence = await captureReviewRequests([request]);
    expect(evidence).toHaveLength(1);
    expect(evidence[0].captureId).toBe('start__front');

    uninstall();
    expect(browserReviewCaptureAvailable()).toBe(false);
    await expect(captureReviewRequests([request])).rejects.toThrow(/not mounted/);
  });
});
