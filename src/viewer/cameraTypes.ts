export const CAMERA_PRESET_IDS = [
  'front',
  'left',
  'right',
  'rear',
  'three_quarter',
  'top',
  'focus',
  'free',
  'recommended',
] as const;

export type CameraPresetId = (typeof CAMERA_PRESET_IDS)[number];
