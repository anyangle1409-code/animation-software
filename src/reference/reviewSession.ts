import type { ExerciseDefinition } from '../exercises/types';
import type { StudioClip } from '../animation/clip';
import { buildCaptureRequests } from './capturePlan';
import { captureReviewRequests } from './browserCapture';
import type { ReviewEvidenceBatch } from './evidence';
import { buildReviewManifest } from './reviewManifest';
import type { ReferenceSpec } from './types';

/**
 * High-level local evidence capture for one already-open candidate.
 *
 * It deliberately does not choose the reference or load an exercise into the
 * Studio. Those are caller decisions. This function only turns a known
 * reference + clip into the deterministic review evidence that reference asks
 * for.
 */
export async function captureReferenceEvidence(
  reference: ReferenceSpec,
  exercise: ExerciseDefinition,
  clip: StudioClip,
): Promise<ReviewEvidenceBatch> {
  if (clip.exerciseId !== exercise.id) {
    throw new Error(
      `Review clip belongs to "${clip.exerciseId}", not exercise "${exercise.id}".`,
    );
  }

  const manifest = buildReviewManifest(reference, clip);
  const requests = buildCaptureRequests(manifest);
  const captures = await captureReviewRequests(requests);
  return {
    referenceId: reference.id,
    exerciseId: exercise.id,
    captures,
  };
}
