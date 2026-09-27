import type { CameraPresetId } from './cameraTypes';
import type { CameraRecommendation } from '../exercises/types';
import { HgVec3 } from '../core/linearMath';

export interface HgCameraSetup {
  position: HgVec3;
  target: HgVec3;
  fov: number;
}

const setup = (
  position: [number, number, number],
  target: [number, number, number],
  fov = 40,
): HgCameraSetup => ({
  position: new HgVec3(...position),
  target: new HgVec3(...target),
  fov,
});

export const HG_CAMERA_PRESETS: Record<
  Exclude<CameraPresetId, 'recommended' | 'free' | 'focus'>,
  HgCameraSetup
> = {
  front: setup([0, 1.05, 3.4], [0, 1.0, 0]),
  left: setup([-3.4, 1.05, 0], [0, 1.0, 0]),
  right: setup([3.4, 1.05, 0], [0, 1.0, 0]),
  rear: setup([0, 1.05, -3.4], [0, 1.0, 0]),
  three_quarter: setup([2.3, 1.35, 2.7], [0, 1.02, 0], 38),
  top: setup([0, 4.2, 0.6], [0, 0.9, 0], 42),
};

export function resolveHgCamera(
  preset: CameraPresetId,
  recommendation: CameraRecommendation,
): HgCameraSetup | null {
  if (preset === 'free' || preset === 'focus') return null;

  if (preset === 'recommended') {
    if (recommendation.position && recommendation.target) {
      return {
        position: new HgVec3(
          recommendation.position.x,
          recommendation.position.y,
          recommendation.position.z,
        ),
        target: new HgVec3(
          recommendation.target.x,
          recommendation.target.y,
          recommendation.target.z,
        ),
        fov: recommendation.fov ?? 40,
      };
    }

    return HG_CAMERA_PRESETS[
      (recommendation.preset === 'recommended' || recommendation.preset === 'free'
        ? 'three_quarter'
        : recommendation.preset) as keyof typeof HG_CAMERA_PRESETS
    ];
  }

  return HG_CAMERA_PRESETS[preset];
}
