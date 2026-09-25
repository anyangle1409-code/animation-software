import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { installBrowserReviewCaptureAdapter } from './browserCapture';
import { captureReferenceEvidence } from './reviewSession';
import { curlReferenceFor } from './specs/curl';

describe('high-level local reference evidence capture', () => {
  it('captures the whole reference-requested review pack', async () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const uninstall = installBrowserReviewCaptureAdapter({
      snapshot: () => null,
      apply: () => undefined,
      settle: () => undefined,
      capturePng: (request) =>
        request.renderMode === 'silhouette'
          ? {
              bytes: new Uint8Array([1]),
              width: 480,
              height: 480,
              silhouette: {
                metrics: {
                  width: 480,
                  height: 480,
                  foregroundPixels: 10,
                  areaRatio: 10 / (480 * 480),
                  bounds: { minX: 0.2, minY: 0.1, maxX: 0.8, maxY: 0.9, width: 0.6, height: 0.8 },
                  centroid: { x: 0.5, y: 0.5 },
                  touches: { left: false, right: false, top: false, bottom: false },
                },
                sanity: { passed: true, issues: [] },
              },
            }
          : { bytes: new Uint8Array([1]), width: 960, height: 960 },
      restore: () => undefined,
    });

    try {
      const batch = await captureReferenceEvidence(curlReferenceFor(bicepCurl), bicepCurl, clip);
      expect(batch.referenceId).toBe('curl.standing.supinated.v1');
      expect(batch.exerciseId).toBe(bicepCurl.id);
      expect(batch.captures).toHaveLength(40);
      expect(batch.captures.filter((capture) => capture.renderMode === 'beauty')).toHaveLength(20);
      expect(batch.captures.filter((capture) => capture.renderMode === 'silhouette')).toHaveLength(20);
      expect(batch.captures.filter((capture) => capture.renderMode === 'silhouette').every((capture) => capture.silhouette?.sanity.passed)).toBe(true);
      expect(batch.captures.some((capture) => capture.captureId === 'peak__grip_closeup')).toBe(true);
    } finally {
      uninstall();
    }
  });

  it('refuses an exercise/clip mismatch', async () => {
    const clip = { ...generateClip(canonicalSkeleton, bicepCurl), exerciseId: 'wrong_exercise' };
    await expect(
      captureReferenceEvidence(curlReferenceFor(bicepCurl), bicepCurl, clip),
    ).rejects.toThrow(/not exercise/);
  });
});
