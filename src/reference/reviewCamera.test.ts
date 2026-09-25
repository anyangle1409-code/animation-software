import { describe, expect, it } from 'vitest';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { shoulderPress } from '../exercises/definitions/shoulderPress';
import { airSquat } from '../exercises/definitions/airSquat';
import { resolveReviewCamera } from './reviewCamera';
import { curlReferenceFor } from './specs/curl';
import { overheadPressReferenceFor } from './specs/overheadPress';
import { squatReferenceFor } from './specs/squat';

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
  it('builds a deterministic shoulder close-up', () => {
    const view = overheadPressReferenceFor(shoulderPress).reviewViews!.find((entry) => entry.id === 'shoulders')!;
    const camera = resolveReviewCamera(view, shoulderPress.camera, {
      upperarm_l: { x: -0.2, y: 1.4, z: 0 },
      upperarm_r: { x: 0.2, y: 1.4, z: 0 },
    });
    expect(camera.target).toEqual({ x: 0, y: 1.4, z: 0 });
    expect(camera.fov).toBe(34);
  });

  it('builds a deterministic feet-and-knees close-up', () => {
    const view = squatReferenceFor(airSquat).reviewViews!.find((entry) => entry.id === 'feet')!;
    const camera = resolveReviewCamera(view, airSquat.camera, {
      foot_l: { x: -0.2, y: 0.08, z: 0 },
      foot_r: { x: 0.2, y: 0.08, z: 0 },
      shin_l: { x: -0.18, y: 0.5, z: 0.1 },
      shin_r: { x: 0.18, y: 0.5, z: 0.1 },
    });
    expect(camera.target.y).toBeCloseTo(0.29, 8);
    expect(camera.fov).toBe(36);
  });

});
