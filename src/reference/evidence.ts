import type { CameraPresetId } from '../viewer/cameraTypes';
import type { ReviewMomentId } from './reviewManifest';

export type ReviewCropTarget = 'full_body' | 'upper_body' | 'hands' | 'shoulders' | 'feet';

export interface CaptureViewportProfile {
  width: number;
  height: number;
  dpr: number;
  backdrop: 'review_neutral';
  showGrid: false;
  showGizmos: false;
  showIkHandles: false;
  viewMode: 'character';
}

export interface CaptureCameraRequest {
  preset: CameraPresetId;
  target: ReviewCropTarget;
}

export interface ReviewCaptureRequest {
  referenceId: string;
  exerciseId: string;
  captureId: string;
  momentId: ReviewMomentId;
  time: number;
  normalizedTime: number;
  viewId: string;
  camera: CaptureCameraRequest;
  viewport: CaptureViewportProfile;
}

export interface ReviewImageEvidenceMeta {
  referenceId: string;
  exerciseId: string;
  captureId: string;
  momentId: ReviewMomentId;
  time: number;
  normalizedTime: number;
  viewId: string;
  width: number;
  height: number;
  mimeType: 'image/png';
}

/**
 * Runtime-only image evidence. Blob is intentionally not used in the planning
 * layer so this type can also be imported by tests and non-browser tooling.
 */
export interface ReviewImageEvidence extends ReviewImageEvidenceMeta {
  image: Uint8Array | ArrayBuffer | Blob;
}

export interface ReviewEvidenceBatch {
  referenceId: string;
  exerciseId: string;
  captures: ReviewImageEvidence[];
}
