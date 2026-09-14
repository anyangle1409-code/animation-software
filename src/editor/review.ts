import { PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import type { ExerciseDefinition } from '../exercises/types';
import type { StudioClip } from '../animation/clip';
import { sampleClip } from '../animation/clip';
import { validateClip } from '../animation/validate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { contactDiagnostics } from '../constraints/contactDiagnostics';
import { measureGripFit } from '../equipment/gripDiagnostics';

export interface ReviewGate {
  id: 'technique' | 'loop' | 'ik' | 'contacts' | 'grip';
  label: string;
  passed: boolean;
  detail: string;
  warnings?: number;
  applicable?: boolean;
}

export interface ExerciseReview {
  automatedPass: boolean;
  gates: ReviewGate[];
  sampledFrames: number;
}

/**
 * Conservative automated authoring gate. It deliberately does not decide
 * visual quality: it only answers whether the deterministic clip has cleared
 * the checks the Studio can measure honestly.
 */
export function reviewExercise(
  rig: Skeleton,
  exercise: ExerciseDefinition,
  clip: StudioClip,
  samplesPerSecond = 10,
): ExerciseReview {
  const evaluation = new PoseEvaluation(rig);
  const validation = validateClip(rig, evaluation, exercise, clip, samplesPerSecond);
  const techniqueErrors = validation.violations.filter((entry) => entry.severity === 'error').length;
  const techniqueWarnings = validation.violations.filter((entry) => entry.severity === 'warning').length;

  const anchors = lockAnchors(
    new PoseEvaluation(rig),
    sampleClip(clip, 0).pose,
    clip.locks,
  );
  const frames = Math.max(2, Math.round(clip.duration * samplesPerSecond));
  const step = clip.duration / frames;
  let contactFailures = 0;
  let worstContactError = 0;
  let gripFailures = 0;
  let gripChecks = 0;
  let worstReachUse = 0;
  let widestGripGap = 0;

  const supportedGripInstances = clip.equipment.filter(
    (instance) => instance.kind === 'dumbbell' && instance.attachment.mode === 'hand',
  );

  for (let index = 0; index <= frames; index += 1) {
    const time = Math.min(clip.duration, index * step);
    const contacts = contactDiagnostics(rig, new PoseEvaluation(rig), clip, time, anchors);
    for (const contact of contacts) {
      if (!contact.enabled) continue;
      if (contact.error !== null) worstContactError = Math.max(worstContactError, contact.error);
      if (
        contact.status === 'unresolved' ||
        contact.status === 'limited' ||
        contact.status === 'overextended' ||
        (contact.error !== null && contact.error > 0.005)
      ) {
        contactFailures += 1;
      }
    }

    if (supportedGripInstances.length > 0) {
      const gripEvaluation = new PoseEvaluation(rig);
      const frame = resolveFrame(rig, gripEvaluation, clip, time, { anchors });
      gripEvaluation.apply(frame.pose);
      for (const instance of supportedGripInstances) {
        if (instance.attachment.mode !== 'hand') continue;
        const equipment = frame.equipment.get(instance.id);
        if (!equipment) {
          gripFailures += 1;
          continue;
        }
        const fit = measureGripFit(gripEvaluation, equipment, instance.attachment.side);
        gripChecks += 1;
        worstReachUse = Math.max(worstReachUse, fit.reachUse);
        widestGripGap = Math.max(widestGripGap, fit.widestGapDeg);
        if (!fit.withinEnvelope) gripFailures += 1;
      }
    }
  }

  const gates: ReviewGate[] = [
    {
      id: 'technique',
      label: 'Technique rules',
      passed: techniqueErrors === 0,
      detail: techniqueErrors === 0
        ? `${exercise.technique.length} rules checked; ${techniqueWarnings} warning${techniqueWarnings === 1 ? '' : 's'}.`
        : `${techniqueErrors} error rule${techniqueErrors === 1 ? '' : 's'} still fail.`,
      warnings: techniqueWarnings,
    },
    {
      id: 'loop',
      label: 'Loop closure',
      passed: validation.loopClosed,
      detail: validation.loopClosed ? 'First and last poses close cleanly.' : 'The clip does not close cleanly.',
    },
    {
      id: 'ik',
      label: 'IK reachability',
      passed: validation.unreachable.length === 0,
      detail: validation.unreachable.length === 0
        ? 'No unreachable IK samples.'
        : `${validation.unreachable.length} sampled IK targets are unreachable.`,
    },
    {
      id: 'contacts',
      label: 'Locked contacts',
      passed: contactFailures === 0,
      detail: clip.locks.length === 0
        ? 'No explicit contact locks in this exercise.'
        : contactFailures === 0
          ? `All enabled locks stay resolved; worst error ${(worstContactError * 1000).toFixed(1)} mm.`
          : `${contactFailures} sampled lock failures; worst error ${(worstContactError * 1000).toFixed(1)} mm.`,
      applicable: clip.locks.length > 0,
    },
    {
      id: 'grip',
      label: 'Dumbbell grip envelope',
      passed: gripFailures === 0,
      detail: supportedGripInstances.length === 0
        ? 'Not applicable: no supported single-hand dumbbell grip.'
        : gripFailures === 0
          ? `${gripChecks} grip samples pass; max reach ${Math.round(worstReachUse * 100)}%, widest gap ${widestGripGap.toFixed(1)}°.`
          : `${gripFailures} of ${gripChecks} grip samples need review.`,
      applicable: supportedGripInstances.length > 0,
    },
  ];

  return {
    automatedPass: gates.every((gate) => gate.passed),
    gates,
    sampledFrames: frames + 1,
  };
}
