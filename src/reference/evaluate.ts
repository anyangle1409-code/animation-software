import { Vector3 } from 'three';
import { sampleClip, sortedKeyframes } from '../animation/clip';
import type { StudioClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { toDeg } from '../core/math';
import type { ExerciseDefinition } from '../exercises/types';
import { PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import type {
  NumericEnvelope,
  ReferenceCheckResult,
  ReferenceCheckSpec,
  ReferenceReport,
  ReferenceSpec,
} from './types';

export interface ReferenceEvaluationOptions {
  /** Required only by world-landmark checks. Bone-local checks remain offline. */
  rig?: Skeleton;
  /** Uniform samples over [0, duration). */
  samples?: number;
}

interface Sample {
  time: number;
  phaseId?: string;
  pose: ReturnType<typeof sampleClip>['pose'];
}

const DEFAULT_SAMPLES = 81;

const inPhases = (sample: Sample, phases?: string[]) =>
  !phases || phases.length === 0 || (sample.phaseId !== undefined && phases.includes(sample.phaseId));

const rangeText = (envelope: NumericEnvelope, unit: string) => {
  if (envelope.min !== undefined && envelope.max !== undefined) {
    return `${envelope.min.toFixed(2)}–${envelope.max.toFixed(2)} ${unit}`;
  }
  if (envelope.min !== undefined) return `≥ ${envelope.min.toFixed(2)} ${unit}`;
  if (envelope.max !== undefined) return `≤ ${envelope.max.toFixed(2)} ${unit}`;
  return 'unbounded';
};

const outside = (value: number, envelope: NumericEnvelope): number => {
  if (envelope.min !== undefined && value < envelope.min) return envelope.min - value;
  if (envelope.max !== undefined && value > envelope.max) return value - envelope.max;
  return 0;
};

function envelopeResult(
  check: Extract<ReferenceCheckSpec, { kind: 'jointEnvelope' | 'rootEnvelope' }>,
  values: { value: number; time: number }[],
): ReferenceCheckResult {
  const severity = check.severity ?? 'error';
  if (values.length === 0) {
    return {
      id: check.id,
      label: check.label,
      kind: check.kind,
      severity,
      status: 'skip',
      detail: 'No samples matched the requested phases.',
      expected: rangeText(check.envelope, 'deg'),
    };
  }

  const worst = values.reduce(
    (best, entry) => {
      const violation = outside(entry.value, check.envelope);
      return violation > best.violation ? { ...entry, violation } : best;
    },
    { ...values[0], violation: outside(values[0].value, check.envelope) },
  );
  const min = Math.min(...values.map((entry) => entry.value));
  const max = Math.max(...values.map((entry) => entry.value));
  const expected = rangeText(check.envelope, 'deg');

  return {
    id: check.id,
    label: check.label,
    kind: check.kind,
    severity,
    status: worst.violation > 1e-9 ? 'fail' : 'pass',
    detail:
      worst.violation > 1e-9
        ? `Observed ${min.toFixed(2)}–${max.toFixed(2)}°, outside ${expected}; worst excess ${worst.violation.toFixed(2)}°.`
        : `Observed ${min.toFixed(2)}–${max.toFixed(2)}°, inside ${expected}.`,
    measured: worst.violation > 1e-9 ? worst.value : Math.max(Math.abs(min), Math.abs(max)),
    expected,
    worstTime: worst.time,
  };
}

function phaseOrder(clip: StudioClip): string[] {
  const phases = sortedKeyframes(clip)
    .slice(0, -1)
    .map((keyframe) => keyframe.phaseId)
    .filter((phase): phase is string => Boolean(phase));
  return phases.filter((phase, index) => index === 0 || phase !== phases[index - 1]);
}

export function evaluateReference(
  reference: ReferenceSpec,
  exercise: ExerciseDefinition,
  clip: StudioClip,
  options: ReferenceEvaluationOptions = {},
): ReferenceReport {
  const count = Math.max(8, options.samples ?? DEFAULT_SAMPLES);
  const samples: Sample[] = Array.from({ length: count }, (_, index) => {
    const time = (index / count) * clip.duration;
    const sample = sampleClip(clip, time);
    return { time, phaseId: sample.phaseId, pose: sample.pose };
  });

  let anchors: ReturnType<typeof lockAnchors> | undefined;
  if (options.rig) {
    const evaluation = new PoseEvaluation(options.rig);
    anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  }

  const results: ReferenceCheckResult[] = reference.checks.map((check) => {
    const selected = samples.filter((sample) => inPhases(sample, check.phases));
    const severity = check.severity ?? 'error';

    switch (check.kind) {
      case 'jointEnvelope': {
        const values = selected.map((sample) => ({
          value: toDeg(sample.pose.rotations[check.bone]?.[check.axis] ?? 0),
          time: sample.time,
        }));
        return envelopeResult(check, values);
      }

      case 'jointExcursion': {
        if (selected.length === 0) {
          return {
            id: check.id,
            label: check.label,
            kind: check.kind,
            severity,
            status: 'skip',
            detail: 'No samples matched the requested phases.',
            expected: rangeText(check.envelope, 'deg'),
          };
        }
        const values = selected.map((sample) => toDeg(sample.pose.rotations[check.bone]?.[check.axis] ?? 0));
        const excursion = Math.max(...values) - Math.min(...values);
        const violation = outside(excursion, check.envelope);
        const expected = rangeText(check.envelope, 'deg');
        return {
          id: check.id,
          label: check.label,
          kind: check.kind,
          severity,
          status: violation > 1e-9 ? 'fail' : 'pass',
          detail:
            violation > 1e-9
              ? `Excursion ${excursion.toFixed(2)}°, outside ${expected} by ${violation.toFixed(2)}°.`
              : `Excursion ${excursion.toFixed(2)}°, inside ${expected}.`,
          measured: excursion,
          expected,
        };
      }

      case 'rootEnvelope': {
        const values = selected.map((sample) => ({
          value: toDeg(sample.pose.rootRotation[check.axis]),
          time: sample.time,
        }));
        return envelopeResult(check, values);
      }

      case 'bilateralSymmetry': {
        if (selected.length === 0) {
          return {
            id: check.id,
            label: check.label,
            kind: check.kind,
            severity,
            status: 'skip',
            detail: 'No samples matched the requested phases.',
            expected: `≤ ${check.toleranceDeg.toFixed(2)}° mirrored difference`,
          };
        }
        let worst = 0;
        let worstTime = 0;
        for (const sample of selected) {
          const left = toDeg(sample.pose.rotations[check.left]?.[check.axis] ?? 0);
          const right = toDeg(sample.pose.rotations[check.right]?.[check.axis] ?? 0);
          const expectedRight = check.axis === 'x' ? left : -left;
          const error = Math.abs(right - expectedRight);
          if (error > worst) {
            worst = error;
            worstTime = sample.time;
          }
        }
        return {
          id: check.id,
          label: check.label,
          kind: check.kind,
          severity,
          status: worst > check.toleranceDeg + 1e-9 ? 'fail' : 'pass',
          detail:
            worst > check.toleranceDeg + 1e-9
              ? `Worst mirrored difference ${worst.toFixed(2)}° exceeds ${check.toleranceDeg.toFixed(2)}°.`
              : `Worst mirrored difference ${worst.toFixed(2)}° is within ${check.toleranceDeg.toFixed(2)}°.`,
          measured: worst,
          expected: `≤ ${check.toleranceDeg.toFixed(2)}°`,
          worstTime,
        };
      }

      case 'phaseOrder': {
        const observed = phaseOrder(clip);
        const pass = observed.length === check.order.length && observed.every((phase, index) => phase === check.order[index]);
        return {
          id: check.id,
          label: check.label,
          kind: check.kind,
          severity,
          status: pass ? 'pass' : 'fail',
          detail: pass
            ? `Phase order: ${observed.join(' → ')}.`
            : `Observed ${observed.join(' → ') || '(none)'}; expected ${check.order.join(' → ')}.`,
          expected: check.order.join(' → '),
        };
      }

      case 'landmarkMonotonic': {
        if (!options.rig || !anchors) {
          return {
            id: check.id,
            label: check.label,
            kind: check.kind,
            severity,
            status: 'skip',
            detail: 'A canonical rig is required for world-landmark evaluation.',
            expected: `${check.direction}, reverse step ≤ ${(check.tolerance * 1000).toFixed(1)} mm`,
          };
        }
        const phaseSamples = samples.filter((sample) => sample.phaseId === check.phase);
        if (phaseSamples.length < 2) {
          return {
            id: check.id,
            label: check.label,
            kind: check.kind,
            severity,
            status: 'skip',
            detail: `Fewer than two samples landed in phase "${check.phase}".`,
          };
        }

        const positions = phaseSamples.map((sample) => {
          const evaluation = new PoseEvaluation(options.rig!);
          resolveFrame(options.rig!, evaluation, clip, sample.time, { anchors });
          const point = evaluation.head(check.bone, new Vector3());
          return { time: sample.time, value: point[check.axis] };
        });

        let worstReverse = 0;
        let worstTime = positions[0].time;
        for (let index = 1; index < positions.length; index += 1) {
          const previous = positions[index - 1].value;
          const current = positions[index].value;
          const reverse =
            check.direction === 'increasing'
              ? Math.max(0, previous - current)
              : Math.max(0, current - previous);
          if (reverse > worstReverse) {
            worstReverse = reverse;
            worstTime = positions[index].time;
          }
        }

        const pass = worstReverse <= check.tolerance + 1e-9;
        return {
          id: check.id,
          label: check.label,
          kind: check.kind,
          severity,
          status: pass ? 'pass' : 'fail',
          detail: pass
            ? `Largest backwards step ${(worstReverse * 1000).toFixed(2)} mm; allowed ${(check.tolerance * 1000).toFixed(2)} mm.`
            : `Reversed ${(worstReverse * 1000).toFixed(2)} mm between adjacent samples; allowed ${(check.tolerance * 1000).toFixed(2)} mm.`,
          measured: worstReverse,
          expected: `≤ ${(check.tolerance * 1000).toFixed(2)} mm reverse step`,
          worstTime,
        };
      }
    }
  });

  const failed = results
    .filter((result) => result.status === 'fail' && result.severity === 'error')
    .map((result) => result.id);
  const skipped = results.filter((result) => result.status === 'skip').map((result) => result.id);

  return {
    referenceId: reference.id,
    referenceVersion: reference.referenceVersion,
    exerciseId: exercise.id,
    passed: failed.length === 0 && skipped.length === 0,
    checks: results,
    failed,
    skipped,
    samples: count,
  };
}
