import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { airSquat } from '../exercises/definitions/airSquat';
import { forwardLunge } from '../exercises/definitions/forwardLunge';
import { canonicalSkeleton } from '../rig/skeleton';
import { buildReviewManifest } from './reviewManifest';
import { curlReferenceFor } from './specs/curl';
import { squatReferenceFor } from './specs/squat';
import { lungeReferenceFor } from './specs/lunge';

describe('local review manifest', () => {
  it('creates five chronological semantic moments for a curl', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const manifest = buildReviewManifest(curlReferenceFor(bicepCurl), clip);

    expect(manifest.moments.map((entry) => entry.id)).toEqual([
      'start',
      'mid_outbound',
      'peak',
      'mid_return',
      'return',
    ]);
    expect(manifest.moments[0].time).toBe(0);
    expect(manifest.moments.at(-1)?.time).toBe(clip.duration);
    expect(manifest.moments.every((entry, index, list) => index === 0 || entry.time >= list[index - 1].time)).toBe(true);
    expect(manifest.moments.every((entry) => entry.normalizedTime >= 0 && entry.normalizedTime <= 1)).toBe(true);
  });

  it('keeps squat review moments chronological even though eccentric comes first', () => {
    const clip = generateClip(canonicalSkeleton, airSquat);
    const manifest = buildReviewManifest(squatReferenceFor(airSquat), clip);

    expect(manifest.moments.map((entry) => entry.id)).toEqual([
      'start',
      'mid_outbound',
      'peak',
      'mid_return',
      'return',
    ]);
    expect(manifest.moments[1].phaseId).toBe('eccentric');
    expect(manifest.moments[3].phaseId).toBe('concentric');
    expect(manifest.moments[1].time).toBeLessThan(manifest.moments[2].time);
    expect(manifest.moments[3].time).toBeGreaterThan(manifest.moments[2].time);
  });

  it('works for stepping lunges whose moving phases are named step and drive', () => {
    const clip = generateClip(canonicalSkeleton, forwardLunge);
    const manifest = buildReviewManifest(lungeReferenceFor(forwardLunge), clip);

    expect(manifest.moments).toHaveLength(5);
    expect(manifest.moments[1].phaseId).toBe('step');
    expect(manifest.moments[3].phaseId).toBe('drive');
    expect(manifest.captures).toHaveLength(20);
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
