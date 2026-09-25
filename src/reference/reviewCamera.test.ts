import { describe, expect, it } from 'vitest';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { resolveReviewCamera } from './reviewCamera';
import { curlReferenceFor } from './specs/curl';

describe('deterministic review camera resolution', () => {
  const reference = curlReferenceFor(bicepCurl);

  it('reuses the existing fixed front camera for full-body review', () => {
    const view = reference.reviewViews!.find((entry) => entry.id === 'front')!;
    const camera = resolveReviewCamera(view, bicepCurl.camera);
    expect(camera.position).toEqual({ x: 0, y: 1.05, z: 3.4 });
    expect(camera.target).toEqual({ x: 0, y: 1, z: 0 });
  });

  it('builds a deterministic hand close-up around the hand midpoint', () => {
    const view = reference.reviewViews!.find((entry) => entry.id === 'grip_closeup')!;
    const camera = resolveReviewCamera(view, bicepCurl.camera, {
      hand_l: { x: -0.2, y: 0.9, z: 0.1 },
      hand_r: { x: 0.2, y: 0.9, z: 0.1 },
    });
    expect(camera.target).toEqual({ x: 0, y: 0.9, z: 0.1 });
    expect(camera.position).toEqual({ x: 0.7, y: 1.15, z: 1 });
    expect(camera.fov).toBe(32);
  });

  it('refuses a hand close-up without the required landmarks', () => {
    const view = reference.reviewViews!.find((entry) => entry.id === 'grip_closeup')!;
    expect(() => resolveReviewCamera(view, bicepCurl.camera)).toThrow(/requires hand_l and hand_r/);
  });
});
