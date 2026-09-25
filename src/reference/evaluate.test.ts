import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { hammerCurl } from '../exercises/definitions/hammerCurl';
import { inclineCurl } from '../exercises/definitions/inclineCurl';
import { reverseCurl } from '../exercises/definitions/reverseCurl';
import type { ExerciseDefinition } from '../exercises/types';
import { canonicalSkeleton } from '../rig/skeleton';
import { evaluateReference } from './evaluate';
import { curlReferenceFor } from './specs/curl';

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

function review(exercise: ExerciseDefinition) {
  return evaluateReference(
    curlReferenceFor(exercise),
    exercise,
    generateClip(canonicalSkeleton, exercise),
    { rig: canonicalSkeleton, samples: 101 },
  );
}

const failureIds = (exercise: ExerciseDefinition) => review(exercise).failed;

describe('the offline curl reference', () => {
  it.each([
    ['standing supinated curl', bicepCurl],
    ['standing neutral hammer curl', hammerCurl],
    ['standing pronated reverse curl', reverseCurl],
    ['45 degree incline curl', inclineCurl],
  ] as const)('%s clears the draft independent envelope', (_name, exercise) => {
    const report = review(exercise);
    expect(report.skipped).toEqual([]);
    expect(report.failed, JSON.stringify(report.checks.filter((check) => check.status === 'fail'))).toEqual([]);
    expect(report.passed).toBe(true);
  });

  it('does not use the exercise technique rules as its answer key', () => {
    const stripped: ExerciseDefinition = {
      ...clone(bicepCurl),
      technique: [],
      commonErrors: [],
    };
    // If reference QA were merely re-running the exercise's own rules, removing
    // them would make this test vacuous. The separate reference still runs all
    // of its own checks and reaches the same verdict.
    const report = review(stripped);
    expect(report.checks.length).toBeGreaterThan(10);
    expect(report.failed).toEqual([]);
  });

  it('rejects a curl with too little elbow range', () => {
    const exercise = clone(bicepCurl);
    exercise.jointTargets = exercise.jointTargets.map((target) =>
      target.bone.startsWith('forearm_') && target.axis === 'x'
        ? { ...target, start: 50, peak: 80 }
        : target,
    );
    const failed = failureIds(exercise);
    expect(failed).toContain('elbow_bottom');
    expect(failed).toContain('elbow_peak');
    expect(failed).toContain('elbow_rom');
  });

  it('rejects a supinated curl whose forearms are actually neutral', () => {
    const exercise = clone(bicepCurl);
    exercise.jointTargets = exercise.jointTargets.map((target) =>
      target.bone.startsWith('forearm_') && target.axis === 'y'
        ? { ...target, start: 0, peak: 0 }
        : target,
    );
    expect(failureIds(exercise)).toContain('grip_orientation');
  });

  it('rejects excessive upper-arm involvement independently of the elbow motion', () => {
    const exercise = clone(bicepCurl);
    for (const pose of [exercise.startPose, exercise.peakPose]) {
      pose.joints.upperarm_l = { ...(pose.joints.upperarm_l ?? {}), x: 32 };
      pose.joints.upperarm_r = { ...(pose.joints.upperarm_r ?? {}), x: 32 };
    }
    expect(failureIds(exercise)).toContain('upper_arm_sagittal');
  });

  it('detects left/right motion corruption', () => {
    const exercise = clone(bicepCurl);
    exercise.peakPose.joints.upperarm_r = {
      ...(exercise.peakPose.joints.upperarm_r ?? {}),
      x: 20,
    };
    expect(failureIds(exercise)).toContain('upper_arm_symmetry');
  });

  it('checks semantic movement order rather than accepting any closed loop', () => {
    const exercise = clone(bicepCurl);
    [exercise.phases[0], exercise.phases[1]] = [exercise.phases[1], exercise.phases[0]];
    expect(failureIds(exercise)).toContain('curl_phase_order');
  });
});
