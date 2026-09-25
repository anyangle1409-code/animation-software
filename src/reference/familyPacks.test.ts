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
import { pullUp } from '../exercises/definitions/pullUp';
import { lateralRaise } from '../exercises/definitions/lateralRaise';
import { frontRaise } from '../exercises/definitions/frontRaise';
import { overheadExtension } from '../exercises/definitions/overheadExtension';
import { pushUp } from '../exercises/definitions/pushUp';
import { calfRaise } from '../exercises/definitions/calfRaise';
import { dumbbellCalfRaise } from '../exercises/definitions/dumbbellCalfRaise';
import { crunch } from '../exercises/definitions/crunch';
import { sitUp } from '../exercises/definitions/sitUp';
import { dumbbellBenchPress } from '../exercises/definitions/dumbbellBenchPress';
import { dumbbellFly } from '../exercises/definitions/dumbbellFly';
import { farmersWalk } from '../exercises/definitions/farmersWalk';
import type { ExerciseDefinition } from '../exercises/types';
import { canonicalSkeleton } from '../rig/skeleton';
import { evaluateReference } from './evaluate';
import { overheadPressReferenceFor } from './specs/overheadPress';
import { squatReferenceFor } from './specs/squat';
import { lungeReferenceFor } from './specs/lunge';
import { hingeReferenceFor } from './specs/hinge';
import { rowReferenceFor } from './specs/row';
import { verticalPullReferenceFor } from './specs/verticalPull';
import { raiseReferenceFor } from './specs/raise';
import { extensionReferenceFor } from './specs/extension';
import { horizontalPressReferenceFor } from './specs/horizontalPress';
import { calfReferenceFor } from './specs/calf';
import { trunkFlexionReferenceFor } from './specs/trunkFlexion';
import { supineReferenceFor } from './specs/supine';
import { carryReferenceFor } from './specs/carry';

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
    ['strict pull-up', pullUp, verticalPullReferenceFor],
    ['lateral raise', lateralRaise, raiseReferenceFor],
    ['front raise', frontRaise, raiseReferenceFor],
    ['overhead triceps extension', overheadExtension, extensionReferenceFor],
    ['standard push-up', pushUp, horizontalPressReferenceFor],
    ['bodyweight calf raise', calfRaise, calfReferenceFor],
    ['dumbbell calf raise', dumbbellCalfRaise, calfReferenceFor],
    ['crunch', crunch, trunkFlexionReferenceFor],
    ['sit-up', sitUp, trunkFlexionReferenceFor],
    ['dumbbell bench press', dumbbellBenchPress, supineReferenceFor],
    ['dumbbell fly', dumbbellFly, supineReferenceFor],
    ["farmer's walk", farmersWalk, carryReferenceFor],
  ] as const)('%s clears its draft reference pack', (_name, exercise, spec) => {
    const report = review(exercise, spec(exercise));
    expect(report.skipped, JSON.stringify(report.checks.filter((check) => check.status === 'skip'))).toEqual([]);
    expect(report.failed, JSON.stringify(report.checks.filter((check) => check.status === 'fail'))).toEqual([]);
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
    exercise.jointTargets = exercise.jointTargets.map((target) =>
      target.bone.startsWith('upperarm_') && target.axis === 'x'
        ? { ...target, peak: 20 }
        : target,
    );
    const report = review(exercise, rowReferenceFor(exercise));
    expect(report.failed).toContain('row_elbow_back');
  });

  it('rejects a pull-up that never reaches strong elbow flexion', () => {
    const exercise = clone(pullUp);
    exercise.jointTargets = exercise.jointTargets.map((target) =>
      target.bone.startsWith('forearm_') && target.axis === 'x'
        ? { ...target, peak: 70 }
        : target,
    );
    const report = review(exercise, verticalPullReferenceFor(exercise));
    expect(report.failed).toContain('pull_top_flexion');
  });

  it('rejects a raise that stops far below shoulder height', () => {
    const exercise = clone(lateralRaise);
    exercise.jointTargets = exercise.jointTargets.map((target) =>
      target.bone.startsWith('upperarm_') && target.axis === 'z'
        ? { ...target, peak: -35 }
        : target,
    );
    const report = review(exercise, raiseReferenceFor(exercise));
    expect(report.failed).toContain('raise_top_height');
  });

  it('rejects an overhead extension without a deep elbow stretch', () => {
    const exercise = clone(overheadExtension);
    exercise.jointTargets = exercise.jointTargets.map((target) =>
      target.bone.startsWith('forearm_') && target.axis === 'x'
        ? { ...target, peak: 70 }
        : target,
    );
    const report = review(exercise, extensionReferenceFor(exercise));
    expect(report.failed).toContain('extension_stretch');
  });


  it('rejects a push-up that never reaches bottom elbow flexion', () => {
    const exercise = clone(pushUp);
    exercise.jointTargets = exercise.jointTargets.map((target) =>
      target.bone.startsWith('forearm_') && target.axis === 'x'
        ? { ...target, peak: 45 }
        : target,
    );
    const report = review(exercise, horizontalPressReferenceFor(exercise));
    expect(report.failed).toContain('pushup_bottom_elbow');
  });

  it('rejects a calf raise whose root no longer rises', () => {
    const exercise = clone(calfRaise);
    exercise.peakPose.root = { position: { y: 0, z: 0 } };
    const report = review(exercise, calfReferenceFor(exercise));
    expect(report.failed).toContain('calf_top_plantarflexion');
  });

  it('rejects a sit-up that stops far from upright', () => {
    const exercise = clone(sitUp);
    exercise.peakPose.root = {
      ...(exercise.peakPose.root ?? {}),
      rotation: { x: -65, y: 0, z: 0 },
    };
    const report = review(exercise, trunkFlexionReferenceFor(exercise));
    expect(report.failed).toContain('situp_top_angle');
  });


  it('rejects a fly whose elbow is no longer softly fixed', () => {
    const exercise = clone(dumbbellFly);
    exercise.startPose.joints.forearm_l = { ...(exercise.startPose.joints.forearm_l ?? {}), x: 55 };
    exercise.startPose.joints.forearm_r = { ...(exercise.startPose.joints.forearm_r ?? {}), x: 55 };
    exercise.peakPose.joints.forearm_l = { ...(exercise.peakPose.joints.forearm_l ?? {}), x: 55 };
    exercise.peakPose.joints.forearm_r = { ...(exercise.peakPose.joints.forearm_r ?? {}), x: 55 };
    const report = review(exercise, supineReferenceFor(exercise));
    expect(report.failed).toContain('fly_soft_elbow');
  });

  it("rejects a farmer's walk with bent carried arms", () => {
    const exercise = clone(farmersWalk);
    exercise.startPose.joints.forearm_l = { ...(exercise.startPose.joints.forearm_l ?? {}), x: 45 };
    exercise.startPose.joints.forearm_r = { ...(exercise.startPose.joints.forearm_r ?? {}), x: 45 };
    exercise.peakPose.joints.forearm_l = { ...(exercise.peakPose.joints.forearm_l ?? {}), x: 45 };
    exercise.peakPose.joints.forearm_r = { ...(exercise.peakPose.joints.forearm_r ?? {}), x: 45 };
    const report = review(exercise, carryReferenceFor(exercise));
    expect(report.failed).toContain('carry_arm_long');
  });

});
