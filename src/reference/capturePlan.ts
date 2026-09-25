import type { ReviewManifest } from './reviewManifest';
import type { CaptureViewportProfile, ReviewCaptureRequest, ReviewCropTarget } from './evidence';

export const DEFAULT_REVIEW_VIEWPORT: CaptureViewportProfile = {
  width: 960,
  height: 960,
  dpr: 1,
  backdrop: 'review_neutral',
  showGrid: false,
  showGizmos: false,
  showIkHandles: false,
  viewMode: 'character',
};

const cropOf = (target: ReviewCropTarget | undefined): ReviewCropTarget => target ?? 'full_body';

/**
 * Turn semantic review captures into renderer-ready requests.
 *
 * This layer owns deterministic capture settings, not React or WebGL. A future
 * bridge can consume the requests using the existing viewer.
 */
export function buildCaptureRequests(
  manifest: ReviewManifest,
  viewport: CaptureViewportProfile = DEFAULT_REVIEW_VIEWPORT,
): ReviewCaptureRequest[] {
  return manifest.captures.map((capture) => ({
    referenceId: manifest.referenceId,
    exerciseId: manifest.exerciseId,
    captureId: capture.id,
    momentId: capture.moment.id,
    time: capture.moment.time,
    normalizedTime: capture.moment.normalizedTime,
    viewId: capture.view.id,
    camera: {
      preset: capture.view.preset,
      target: cropOf(capture.view.target),
    },
    viewport: { ...viewport },
  }));
}
