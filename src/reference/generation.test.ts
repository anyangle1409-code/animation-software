import { describe, expect, it } from 'vitest';
import { EXERCISE_BY_ID } from '../exercises/library';
import { generateExercise } from '../generation/generate';
import { canonicalSkeleton } from '../rig/skeleton';
import { evaluateReference } from './evaluate';
import { curlReferenceFor } from './specs/curl';

const library = (id: string) => EXERCISE_BY_ID.get(id);

describe('reference QA beside prompt generation', () => {
  it('can review a prompt-generated curl without changing generator behaviour', () => {
    const generated = generateExercise(
      'Create a standing dumbbell curl with 10 kg dumbbells.',
      { rig: canonicalSkeleton, library },
    );

    expect(generated.family?.id).toBe('curl');
    expect(generated.exercise).toBeDefined();
    expect(generated.clip).toBeDefined();
    // No production character was supplied, so the generator correctly refuses
    // to call its body-dependent QA certified.
    expect(generated.status).toBe('unverified');
    expect(generated.referenceQA?.passed).toBe(true);

    const reference = curlReferenceFor(generated.exercise!);
    const report = evaluateReference(reference, generated.exercise!, generated.clip!, {
      rig: canonicalSkeleton,
      samples: 101,
    });

    expect(report.failed).toEqual([]);
    expect(report.skipped).toEqual([]);
    expect(report.passed).toBe(true);
  });

  it('does not replace the existing mechanical/body gates', () => {
    const generated = generateExercise(
      'Create a standing hammer curl with 12 kg dumbbells and controlled tempo.',
      { rig: canonicalSkeleton, library },
    );

    expect(generated.family?.id).toBe('curl');
    expect(generated.status).toBe('unverified');
    expect(generated.report?.skipped).toContain('equipmentClearance');
    expect(generated.report?.skipped).toContain('armTrunk');
    expect(generated.referenceQA?.passed).toBe(true);

    const report = evaluateReference(
      curlReferenceFor(generated.exercise!),
      generated.exercise!,
      generated.clip!,
      { rig: canonicalSkeleton, samples: 101 },
    );

    // Reference QA answers a different question: whether the movement shape is
    // inside the independent curl envelope. It must never turn skipped body
    // collision checks into a certified generator result.
    expect(report.failed).toEqual([]);
    expect(generated.status).not.toBe('passed');
    // Read-only integration: reference evidence cannot promote an unverified mechanical result.
    expect(generated.referenceQA?.passed).toBe(true);
  });
});
