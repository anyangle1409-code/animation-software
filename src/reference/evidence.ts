import type { CameraPresetId } from '../viewer/cameraTypes';
import type { ReviewMomentId } from './reviewManifest';
import type { SilhouetteMetrics, SilhouetteSanity } from './silhouette';

export type ReviewCropTarget = 'full_body' | 'upper_body' | 'hands' | 'shoulders' | 'feet';
export type ReviewRenderMode = 'beauty' | 'silhouette';

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
  renderMode: ReviewRenderMode;
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
  renderMode: ReviewRenderMode;
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
  silhouette?: {
    metrics: SilhouetteMetrics;
    sanity: SilhouetteSanity;
  };
}

export interface ReviewEvidenceBatch {
  referenceId: string;
  exerciseId: string;
  captures: ReviewImageEvidence[];
}
