import { generateClip } from '../animation/generate';
import type { StudioClip } from '../animation/clip';
import type { CharacterBuild } from '../character';
import type { ExerciseDefinition } from '../exercises/types';
import type { Skeleton } from '../rig/skeleton';
import type { ExerciseIntent, ParsedPrompt } from './intent';
import { generatorFamily } from './families';
import type { GeneratorFamily, Lever } from './families';
import { parsePrompt } from './parse';
import type { CandidateReport, CheckId } from './validate';
import { CHECK_LABELS, validationSteps } from './validate';

/**
 * Prompt → intent → family variant → definition → clip → validation → bounded
 * correction → candidate.
 *
 * ## The correction loop
 *
 * When a check fails, the loop looks for a lever — a family parameter declared
 * in `families.ts` as able to resolve that check — and walks it one step at a
 * time towards its bound, re-validating at each step. The lever answering the
 * most of what fails goes first, so one change is preferred to two. A lever
 * stops the moment a step breaks a check that was passing: trading one failure
 * for another is not a correction. A value is accepted only when the checks it
 * fixed still pass one step further on, because clearance can be a ridge rather
 * than a slope (the reverse curl measured 0.79, 2.39, 4.21, 5.70, 0.47 and
 * −4.76 mm across 4° to 6.5° of abduction), and a value one step from failing
 * is luck, not a fix. Then the whole report is run again.
 *
 * What the loop cannot do is as important. It sees the report, not the
 * limits; it can only write the variant's own fields, through a lever, inside
 * that lever's bound; and it has a fixed budget of validations. Every attempt
 * is recorded with what it measured, so the review can see exactly what was
 * changed and why. A failure no lever addresses is reported, not worked
 * around.
 */

export interface GenerationOptions {
  rig: Skeleton;
  /** For the body checks. Without it they are skipped and the candidate is not certified. */
  character?: { build: CharacterBuild; label: string };
  /** Resolves a library exercise id, for the reference comparison. */
  library: (id: string) => ExerciseDefinition | undefined;
  /** Most validations the loop may spend, the first included. */
  budget?: number;
}

export interface CorrectionAttempt {
  round: number;
  lever: string;
  label: string;
  from: number;
  to: number;
  targets: CheckId[];
  failed: CheckId[];
  /** The targets' deciding measurements at this value. */
  measured: Partial<Record<CheckId, number>>;
  outcome: 'still failing' | 'breaks another check' | 'passes, next step does not' | 'accepted' | 'accepted at bound';
}

export type GenerationStatus =
  /** The request cannot be built as asked; see the parser's issues. */
  | 'blocked'
  /** Every automatic check passed. Ready for human review; not promoted. */
  | 'passed'
  /** No failure, but some checks could not run (no character). */
  | 'unverified'
  /** Failures remain after the loop. */
  | 'failed';

export interface GenerationResult {
  parsed: ParsedPrompt;
  status: GenerationStatus;
  intent?: ExerciseIntent;
  family?: GeneratorFamily;
  /** The family variant that was built — the whole generated source, shown for review and promotion. */
  variant?: object;
  exercise?: ExerciseDefinition;
  clip?: StudioClip;
  reference?: string;
  /** Before any correction. */
  initial?: CandidateReport;
  report?: CandidateReport;
  attempts: CorrectionAttempt[];
  /** Accepted corrections, in words. */
  corrections: string[];
  validations: number;
}

export interface GenerationProgress {
  stage: 'parse' | 'build' | 'validate' | 'correct' | 'done';
  message: string;
}

interface Validated {
  exercise: ExerciseDefinition;
  clip: StudioClip;
  report: CandidateReport;
}

const ROUNDS = 3;
const BUDGET = 40;

/** The checks that need no character: cheap enough to re-run on every attempt, so a lever cannot break one unseen. */
const RIG_CHECKS: CheckId[] = [
  'technique',
  'loop',
  'ik',
  'contacts',
  'grip',
  'twoHandGrip',
  'jointLimits',
  'lockDrift',
  'feetFlat',
  'duration',
  'references',
];

const measuredOf = (report: CandidateReport, targets: CheckId[]) =>
  Object.fromEntries(
    report.checks
      .filter((check) => targets.includes(check.id) && check.measured !== undefined)
      .map((check) => [check.id, check.measured]),
  ) as Partial<Record<CheckId, number>>;

/**
 * The pipeline as a sequence of steps, so a caller can run it straight through
 * (`generateExercise`) or yield to a UI between steps (`generateExerciseAsync`).
 */
export function* generationSteps(prompt: string, options: GenerationOptions): Generator<GenerationProgress, GenerationResult> {
  yield { stage: 'parse', message: 'Reading the request' };
  const parsed = parsePrompt(prompt);
  const result: GenerationResult = { parsed, status: 'blocked', attempts: [], corrections: [], validations: 0 };
  if (!parsed.intent || parsed.issues.some((issue) => issue.blocking)) return result;

  const intent = parsed.intent;
  const family = generatorFamily(intent.family);
  const referenceId = family.reference(intent);
  const reference = options.library(referenceId);
  const budget = options.budget ?? BUDGET;
  Object.assign(result, { intent, family, reference: referenceId });

  const clips = new Map<ExerciseDefinition, StudioClip>();
  const clipOf = (exercise: ExerciseDefinition) => {
    let clip = clips.get(exercise);
    if (!clip) {
      clip = generateClip(options.rig, exercise);
      clips.set(exercise, clip);
    }
    return clip;
  };
  /** Build and validate a variant, yielding between the slow measurements. */
  function* validate(variant: object, only?: CheckId[]): Generator<GenerationProgress, Validated> {
    const exercise = family.build(variant as never);
    const clip = generateClip(options.rig, exercise);
    result.validations += 1;
    const steps = validationSteps(
      { rig: options.rig, character: options.character, reference, only },
      exercise,
      clip,
      clipOf,
    );
    for (;;) {
      const step = steps.next();
      if (step.done) return { exercise, clip, report: step.value };
      yield { stage: 'validate', message: step.value };
    }
  }

  let variant: object = family.variant(intent);
  yield { stage: 'build', message: `Building a ${family.label.toLowerCase()} from the family` };
  yield { stage: 'validate', message: options.character ? `Validating on ${options.character.label}` : 'Validating (no character: body checks skipped)' };
  let current = yield* validate(variant);
  result.initial = current.report;

  for (let round = 1; round <= ROUNDS && current.report.failed.length > 0; round += 1) {
    const failing = current.report.failed;
    // The lever that answers the most of what is failing goes first: one change
    // that resolves two checks is a smaller edit than two changes that resolve
    // one each. Ties keep the family's order.
    const covers = (lever: Lever<object>) => lever.resolves.filter((check) => failing.includes(check)).length;
    const levers = (family.levers as Lever<object>[])
      .filter((lever) => covers(lever) > 0)
      .map((lever, index) => ({ lever, index }))
      .sort((a, b) => covers(b.lever) - covers(a.lever) || a.index - b.index)
      .map(({ lever }) => lever);
    let fixed = false;

    for (const lever of levers) {
      const targets = lever.resolves.filter((check) => failing.includes(check));
      const only = [...RIG_CHECKS, ...targets];
      const from = lever.read(variant);
      const direction = Math.sign(lever.step);
      yield { stage: 'correct', message: `${lever.label}: trying from ${from}°` };

      for (let value = from + lever.step; direction * (lever.limit - value) >= -1e-9; value += lever.step) {
        if (result.validations >= budget) break;
        yield { stage: 'correct', message: `${lever.label}: ${value}°` };
        const attempt = yield* validate(lever.write(variant, value), only);
        const record: CorrectionAttempt = {
          round,
          lever: lever.id,
          label: lever.label,
          from,
          to: value,
          targets,
          failed: attempt.report.failed,
          measured: measuredOf(attempt.report, targets),
          outcome: 'still failing',
        };
        result.attempts.push(record);

        const broken = attempt.report.failed.filter((check) => !failing.includes(check));
        if (broken.length > 0) {
          record.outcome = 'breaks another check';
          break;
        }
        if (targets.some((check) => attempt.report.failed.includes(check))) continue;

        const next = value + lever.step;
        if (direction * (lever.limit - next) < -1e-9) {
          record.outcome = 'accepted at bound';
        } else {
          if (result.validations >= budget) break;
          // Only the checks being fixed need to hold at the next step: that is
          // the ridge being guarded against. Another check failing there just
          // marks where the lever's own room ends.
          const confirm = yield* validate(lever.write(variant, next), targets);
          if (targets.some((check) => confirm.report.failed.includes(check))) {
            record.outcome = 'passes, next step does not';
            continue;
          }
          record.outcome = 'accepted';
        }
        variant = lever.write(variant, value);
        result.corrections.push(
          `${lever.label}: ${from}° → ${value}° resolved ${targets.map((check) => CHECK_LABELS[check].toLowerCase()).join(' and ')} ` +
            `(${Object.entries(record.measured)
              .map(([check, measured]) => `${CHECK_LABELS[check as CheckId].toLowerCase()}: ${((measured as number) * 1000).toFixed(2)} mm`)
              .join('; ')}).`,
        );
        fixed = true;
        break;
      }
      if (fixed || result.validations >= budget) break;
    }
    if (!fixed) break;
    yield { stage: 'validate', message: 'Re-validating the corrected candidate' };
    current = yield* validate(variant);
  }

  Object.assign(result, {
    variant,
    exercise: current.exercise,
    clip: current.clip,
    report: current.report,
    status: current.report.failed.length > 0 ? 'failed' : current.report.skipped.length > 0 ? 'unverified' : 'passed',
  });
  yield { stage: 'done', message: 'Done' };
  return result;
}

export function generateExercise(prompt: string, options: GenerationOptions): GenerationResult {
  const steps = generationSteps(prompt, options);
  for (;;) {
    const step = steps.next();
    if (step.done) return step.value;
  }
}

/** The same pipeline, yielding to the event loop between steps so a UI can repaint. */
export async function generateExerciseAsync(
  prompt: string,
  options: GenerationOptions,
  onProgress?: (progress: GenerationProgress) => void,
): Promise<GenerationResult> {
  const steps = generationSteps(prompt, options);
  for (;;) {
    const step = steps.next();
    if (step.done) return step.value;
    onProgress?.(step.value);
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
}
