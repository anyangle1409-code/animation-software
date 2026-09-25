import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { buildCaptureRequests, DEFAULT_REVIEW_VIEWPORT } from './capturePlan';
import { buildReviewManifest } from './reviewManifest';
import { curlReferenceFor } from './specs/curl';

describe('deterministic review capture planning', () => {
  it('turns the curl review manifest into fixed local capture requests', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const reference = curlReferenceFor(bicepCurl);
    const manifest = buildReviewManifest(reference, clip);
    const requests = buildCaptureRequests(manifest);

    expect(requests).toHaveLength(20);
    expect(requests.every((request) => request.viewport.width === 960)).toBe(true);
    expect(requests.every((request) => request.viewport.height === 960)).toBe(true);
    expect(requests.every((request) => request.viewport.dpr === 1)).toBe(true);
    expect(requests.every((request) => request.viewport.showGrid === false)).toBe(true);
    expect(requests.every((request) => request.viewport.showGizmos === false)).toBe(true);
    expect(requests.every((request) => request.viewport.showIkHandles === false)).toBe(true);
    expect(requests.find((request) => request.captureId === 'peak__grip_closeup')?.camera.target).toBe('hands');
  });

  it('allows an explicit deterministic viewport profile', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const manifest = buildReviewManifest(curlReferenceFor(bicepCurl), clip);
    const viewport = { ...DEFAULT_REVIEW_VIEWPORT, width: 1280, height: 720 };
    const requests = buildCaptureRequests(manifest, viewport);
    expect(requests.every((request) => request.viewport.width === 1280 && request.viewport.height === 720)).toBe(true);
  });
});
