import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { buildReviewManifest } from './reviewManifest';
import { curlReferenceFor } from './specs/curl';

describe('local review manifest', () => {
  it('creates semantic curl moments across the whole repetition', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const manifest = buildReviewManifest(curlReferenceFor(bicepCurl), clip);

    expect(manifest.moments.map((moment) => moment.id)).toEqual([
      'start',
      'mid_concentric',
      'peak',
      'mid_eccentric',
      'return',
    ]);
    expect(manifest.moments[0].time).toBe(0);
    expect(manifest.moments.at(-1)?.time).toBe(clip.duration);
    expect(manifest.moments.every((moment) => moment.normalizedTime >= 0 && moment.normalizedTime <= 1)).toBe(true);
  });

  it('crosses every semantic moment with the family review cameras', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const reference = curlReferenceFor(bicepCurl);
    const manifest = buildReviewManifest(reference, clip);
    const views = reference.reviewViews ?? [];

    expect(views.map((view) => view.id)).toEqual(['front', 'side', 'three_quarter', 'grip_closeup']);
    expect(manifest.captures).toHaveLength(manifest.moments.length * views.length);
    expect(new Set(manifest.captures.map((capture) => capture.id)).size).toBe(manifest.captures.length);
    expect(manifest.captures.some((capture) => capture.id === 'peak__grip_closeup')).toBe(true);
  });
});
