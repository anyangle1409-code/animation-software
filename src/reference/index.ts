export { captureReferenceEvidence } from './reviewSession';
export { browserReviewCaptureAvailable, captureReviewRequests, installBrowserReviewCaptureAdapter } from './browserCapture';
export { captureReviewBatch } from './captureController';
export type { CapturedPng, CaptureBatchProgress, ReviewCaptureAdapter } from './captureController';
export { bodyNormalization, normalizeDelta, normalizePoint } from './normalize';
export type { BodyNormalization } from './normalize';
export { compareNormalizedTrajectories, sampleNormalizedRelativeTrajectory } from './trajectory';
export type { NormalizationScale, NormalizedTrajectoryPoint, TrajectoryComparison } from './trajectory';
export { buildCaptureRequests, DEFAULT_REVIEW_VIEWPORT } from './capturePlan';
export type {
  CaptureCameraRequest,
  CaptureViewportProfile,
  ReviewCaptureRequest,
  ReviewEvidenceBatch,
  ReviewImageEvidence,
  ReviewImageEvidenceMeta,
} from './evidence';
export { sampleLandmarks, sampleLandmarkTrajectory } from './landmarks';
export type { LandmarkFrame } from './landmarks';
export { evaluateProjectedEnvelope, projectWorldPoint, projectedDistance } from './projection';
export type { ProjectedEnvelope, ProjectedEnvelopeResult, ProjectedPoint, ProjectionCamera } from './projection';
export { resolveReviewCamera } from './reviewCamera';
export type { DeterministicCameraSetup, ReviewLandmarks } from './reviewCamera';
export { evaluateReference } from './evaluate';
export type { ReferenceEvaluationOptions } from './evaluate';
export { referenceForFamily } from './library';
export { measureBilateralRotationError, measureJointAxis, measurePhaseTiming, measureRootAxis } from './measure';
export type { AxisMeasurement, PhaseTimingMeasurement } from './measure';
export { formatReferenceReport } from './report';
export { buildReviewManifest } from './reviewManifest';
export type { ReviewCapture, ReviewManifest, ReviewMoment, ReviewMomentId } from './reviewManifest';
export { curlReferenceFor } from './specs/curl';
export { overheadPressReferenceFor } from './specs/overheadPress';
export { squatReferenceFor } from './specs/squat';
export { lungeReferenceFor } from './specs/lunge';
export { hingeReferenceFor } from './specs/hinge';
export { rowReferenceFor } from './specs/row';
export { verticalPullReferenceFor } from './specs/verticalPull';
export { horizontalPressReferenceFor } from './specs/horizontalPress';
export type {
  ReferenceApplicability,
  ReferenceCheckResult,
  ReferenceCheckSpec,
  ReferenceCheckStatus,
  ReferenceFamilyId,
  ReferenceReport,
  ReferenceReviewView,
  ReferenceScale,
  ReferenceSpec,
} from './types';
