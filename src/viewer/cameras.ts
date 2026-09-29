import type { CameraPresetId } from './cameraTypes';
import type { CameraRecommendation } from '../exercises/types';
import {
  HG_CAMERA_PRESETS,
  resolveHgCamera,
  type HgCameraSetup,
} from './firstPartyCameras';

export type CameraSetup = HgCameraSetup;

/**
 * Framing presets. Every one keeps the whole figure and its equipment in shot,
 * which is what an app demonstration needs — a tight crop on the working joint
 * is useless for showing someone how a lift looks.
 */
export const CAMERA_PRESETS: Record<
  Exclude<CameraPresetId, 'recommended' | 'free' | 'focus'>,
  CameraSetup
> = HG_CAMERA_PRESETS;

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
  return resolveHgCamera(preset, recommendation);
}
