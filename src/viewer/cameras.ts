import { Vector3 } from 'three';
import type { CameraPresetId } from './cameraTypes';
import type { CameraRecommendation } from '../exercises/types';

export interface CameraSetup {
  position: Vector3;
  target: Vector3;
  fov: number;
}

const setup = (position: [number, number, number], target: [number, number, number], fov = 40): CameraSetup => ({
  position: new Vector3(...position),
  target: new Vector3(...target),
  fov,
});

/**
 * Framing presets. Every one keeps the whole figure and its equipment in shot,
 * which is what an app demonstration needs — a tight crop on the working joint
 * is useless for showing someone how a lift looks.
 */
export const CAMERA_PRESETS: Record<Exclude<CameraPresetId, 'recommended' | 'free' | 'focus'>, CameraSetup> = {
  front: setup([0, 1.05, 3.4], [0, 1.0, 0]),
  left: setup([-3.4, 1.05, 0], [0, 1.0, 0]),
  right: setup([3.4, 1.05, 0], [0, 1.0, 0]),
  rear: setup([0, 1.05, -3.4], [0, 1.0, 0]),
  three_quarter: setup([2.3, 1.35, 2.7], [0, 1.02, 0], 38),
  top: setup([0, 4.2, 0.6], [0, 0.9, 0], 42),
};

export const CAMERA_LABELS: Record<CameraPresetId, string> = {
  front: 'Front',
  left: 'Left',
  right: 'Right',
  rear: 'Rear',
  three_quarter: '3/4',
  top: 'Top',
  focus: 'Focus selected',
  free: 'Free orbit',
  recommended: 'Recommended',
};

/** Resolve a preset, falling back to the exercise's saved camera. */
export function resolveCamera(
  preset: CameraPresetId,
  recommendation: CameraRecommendation,
): CameraSetup | null {
  if (preset === 'free' || preset === 'focus') return null;
  if (preset === 'recommended') {
    if (recommendation.position && recommendation.target) {
      return {
        position: new Vector3(
          recommendation.position.x,
          recommendation.position.y,
          recommendation.position.z,
        ),
        target: new Vector3(
          recommendation.target.x,
          recommendation.target.y,
          recommendation.target.z,
        ),
        fov: recommendation.fov ?? 40,
      };
    }
    return CAMERA_PRESETS[
      (recommendation.preset === 'recommended' || recommendation.preset === 'free'
        ? 'three_quarter'
        : recommendation.preset) as keyof typeof CAMERA_PRESETS
    ];
  }
  return CAMERA_PRESETS[preset];
}
