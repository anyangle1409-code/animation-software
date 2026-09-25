import type { ReviewManifest } from './reviewManifest';
import type { CaptureViewportProfile, ReviewCaptureRequest, ReviewCropTarget, ReviewRenderMode } from './evidence';

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
  renderMode: ReviewRenderMode = 'beauty',
): ReviewCaptureRequest[] {
  return manifest.captures.map((capture) => ({
    referenceId: manifest.referenceId,
    exerciseId: manifest.exerciseId,
    captureId: capture.id,
    momentId: capture.moment.id,
    time: capture.moment.time,
    normalizedTime: capture.moment.normalizedTime,
    viewId: capture.view.id,
    renderMode,
    camera: {
      preset: capture.view.preset,
      target: cropOf(capture.view.target),
    },
    viewport: { ...viewport },
  }));
}


/**
 * Build an interleaved local evidence pack. Beauty renders are full resolution;
 * silhouette renders default to half resolution because their metrics are
 * resolution-normalized and do not need presentation-quality pixels.
 */
export function buildEvidenceCaptureRequests(
  manifest: ReviewManifest,
  viewport: CaptureViewportProfile = DEFAULT_REVIEW_VIEWPORT,
): ReviewCaptureRequest[] {
  const silhouetteViewport: CaptureViewportProfile = {
    ...viewport,
    width: Math.max(1, Math.round(viewport.width / 2)),
    height: Math.max(1, Math.round(viewport.height / 2)),
  };

  const beauty = buildCaptureRequests(manifest, viewport, 'beauty');
  const silhouettes = buildCaptureRequests(manifest, silhouetteViewport, 'silhouette');

  return beauty.flatMap((request, index) => [request, silhouettes[index]]);
}
