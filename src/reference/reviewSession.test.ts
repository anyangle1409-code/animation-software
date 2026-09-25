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
      capturePng: () => ({ bytes: new Uint8Array([1]), width: 960, height: 960 }),
      restore: () => undefined,
    });

    try {
      const batch = await captureReferenceEvidence(curlReferenceFor(bicepCurl), bicepCurl, clip);
      expect(batch.referenceId).toBe('curl.standing.supinated.v1');
      expect(batch.exerciseId).toBe(bicepCurl.id);
      expect(batch.captures).toHaveLength(20);
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
