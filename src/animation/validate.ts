import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { ExerciseDefinition } from '../exercises/types';
import { evaluateRules, summariseViolations } from '../constraints/rules';
import type { RuleViolation } from '../constraints/types';
import { closesLoop, sampleClip } from './clip';
import type { StudioClip } from './clip';
import { resolveFrame } from './pipeline';
import { lockAnchors } from '../constraints/locks';
import { PoseEvaluation as Evaluation } from '../rig/skeleton';

export interface UnreachableTarget {
  time: number;
  chain: string;
  error: number;
}

export interface ClipValidation {
  /** Worst frame per rule, most severe first. */
  violations: RuleViolation[];
  /** Every frame's violations, for the timeline's warning track. */
  perFrame: { time: number; violations: RuleViolation[] }[];
  loopClosed: boolean;
  unreachable: UnreachableTarget[];
  frames: number;
}

/**
 * Run the exercise's own technique rules across the whole clip.
 *
 * This is what stops a generated animation from quietly exporting bad form: the
 * rules come from the exercise definition, so the checker and the documentation
 * can never disagree.
 */
export function validateClip(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  exercise: ExerciseDefinition,
  clip: StudioClip,
  samplesPerSecond = 15,
): ClipValidation {
  const frames = Math.max(2, Math.round(clip.duration * samplesPerSecond));
  const step = clip.duration / frames;

  // The opening frame fixes both the contact anchors and the reference pose for
  // "stays where it started" rules.
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  const reference = new Evaluation(skeleton);
  const first = resolveFrame(skeleton, evaluation, clip, 0, { anchors });
  reference.apply(first.pose);

  const perFrame: ClipValidation['perFrame'] = [];
  const all: RuleViolation[] = [];
  const unreachable: UnreachableTarget[] = [];

  for (let index = 0; index <= frames; index += 1) {
    const time = Math.min(clip.duration, index * step);
    const frame = resolveFrame(skeleton, evaluation, clip, time, { anchors });
    evaluation.apply(frame.pose);

    const violations = evaluateRules(evaluation, frame.pose, exercise.technique, {
      time,
      phase: frame.phaseId,
      reference,
    });
    if (violations.length > 0) perFrame.push({ time, violations });
    all.push(...violations);

    for (const result of frame.ikResults) {
      if (!result.reached && result.error > 5e-3) {
        unreachable.push({ time, chain: result.chain, error: result.error });
      }
    }
  }

  return {
    violations: summariseViolations(all),
    perFrame,
    loopClosed: closesLoop(clip),
    unreachable,
    frames,
  };
}
