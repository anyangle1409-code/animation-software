import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { shoulderPress } from '../exercises/definitions/shoulderPress';
import { seatedShoulderPress } from '../exercises/definitions/seatedShoulderPress';
import { airSquat } from '../exercises/definitions/airSquat';
import { splitSquat } from '../exercises/definitions/splitSquat';
import { forwardLunge } from '../exercises/definitions/forwardLunge';
import { reverseLunge } from '../exercises/definitions/reverseLunge';
import { romanianDeadlift } from '../exercises/definitions/romanianDeadlift';
import { bentOverRow } from '../exercises/definitions/bentOverRow';
import type { ExerciseDefinition } from '../exercises/types';
import { canonicalSkeleton } from '../rig/skeleton';
import { evaluateReference } from './evaluate';
import { overheadPressReferenceFor } from './specs/overheadPress';
import { squatReferenceFor } from './specs/squat';
import { lungeReferenceFor } from './specs/lunge';
import { hingeReferenceFor } from './specs/hinge';
import { rowReferenceFor } from './specs/row';

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

function review(
  exercise: ExerciseDefinition,
  reference: ReturnType<typeof overheadPressReferenceFor>,
) {
  return evaluateReference(
    reference,
    exercise,
    generateClip(canonicalSkeleton, exercise),
    { rig: canonicalSkeleton, samples: 101 },
  );
}

describe('draft family reference packs', () => {
  it.each([
    ['standing overhead press', shoulderPress, overheadPressReferenceFor],
    ['seated overhead press', seatedShoulderPress, overheadPressReferenceFor],
    ['bodyweight squat', airSquat, squatReferenceFor],
    ['split squat', splitSquat, lungeReferenceFor],
    ['forward lunge', forwardLunge, lungeReferenceFor],
    ['reverse lunge', reverseLunge, lungeReferenceFor],
    ['Romanian deadlift', romanianDeadlift, hingeReferenceFor],
    ['bent-over row', bentOverRow, rowReferenceFor],
  ] as const)('%s clears its draft reference pack', (_name, exercise, spec) => {
    const report = review(exercise, spec(exercise));
    expect(report.skipped, report.checks.filter((check) => check.status === 'skip')).toEqual([]);
    expect(report.failed, report.checks.filter((check) => check.status === 'fail')).toEqual([]);
  });

  it('rejects an overhead press that stops well short of lockout', () => {
    const exercise = clone(shoulderPress);
    exercise.jointTargets = exercise.jointTargets.map((target) =>
      target.bone.startsWith('forearm_') && target.axis === 'x'
        ? { ...target, peak: 45 }
        : target,
    );
    const report = review(exercise, overheadPressReferenceFor(exercise));
    expect(report.failed).toContain('elbow_lockout');
  });

  it('rejects a squat whose authored root no longer reaches depth', () => {
    const exercise = clone(airSquat);
    exercise.peakPose.root = {
      ...(exercise.peakPose.root ?? {}),
      position: {
        x: exercise.peakPose.root?.position?.x ?? 0,
        y: -0.05,
        z: exercise.peakPose.root?.position?.z ?? 0,
      },
    };
    const report = review(exercise, squatReferenceFor(exercise));
    expect(report.failed).toContain('squat_depth_root');
  });

  it('rejects a lunge with an obviously flexed lower back', () => {
    const exercise = clone(splitSquat);
    exercise.startPose.joints.spine_01 = { x: 30 };
    exercise.peakPose.joints.spine_01 = { x: 30 };
    const report = review(exercise, lungeReferenceFor(exercise));
    expect(report.failed).toContain('lunge_spine_neutral');
  });

  it('rejects an RDL that barely hinges', () => {
    const exercise = clone(romanianDeadlift);
    exercise.peakPose.root = {
      ...(exercise.peakPose.root ?? {}),
      rotation: {
        x: 20,
        y: exercise.peakPose.root?.rotation?.y ?? 0,
        z: exercise.peakPose.root?.rotation?.z ?? 0,
      },
    };
    const report = review(exercise, hingeReferenceFor(exercise));
    expect(report.failed).toContain('hinge_root_pitch');
  });

  it('rejects a row whose elbow never drives behind the torso', () => {
    const exercise = clone(bentOverRow);
    exercise.peakPose.joints.upperarm_l = {
      ...(exercise.peakPose.joints.upperarm_l ?? {}),
      x: 20,
    };
    exercise.peakPose.joints.upperarm_r = {
      ...(exercise.peakPose.joints.upperarm_r ?? {}),
      x: 20,
    };
    const report = review(exercise, rowReferenceFor(exercise));
    expect(report.failed).toContain('row_elbow_back');
  });
});
