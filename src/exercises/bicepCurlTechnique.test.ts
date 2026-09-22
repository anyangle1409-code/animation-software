import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { validateClip } from '../animation/validate';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { ExerciseDefinition } from './types';
import { bicepCurl } from './definitions/bicepCurl';

const skeleton = canonicalSkeleton;

function violations(exercise: ExerciseDefinition): string[] {
  const clip = generateClip(skeleton, exercise);
  return validateClip(skeleton, new PoseEvaluation(skeleton), exercise, clip, 20)
    .violations.map((violation) => violation.ruleId);
}

function withPeakJoint(bone: string, patch: Record<string, number>): ExerciseDefinition {
  return {
    ...bicepCurl,
    peakPose: {
      ...bicepCurl.peakPose,
      joints: {
        ...bicepCurl.peakPose.joints,
        [bone]: { ...(bicepCurl.peakPose.joints as Record<string, Record<string, number>>)[bone], ...patch },
      },
    },
  } as ExerciseDefinition;
}

describe('bicep curl realism guardrails', () => {
  it('rejects a shrugging clavicle', () => {
    expect(violations(withPeakJoint('clavicle_l', { z: -5 }))).toContain('shoulder_relaxed_l');
  });

  it('rejects upper-arm takeover that the accepted 4-degree drift never reaches', () => {
    expect(violations(withPeakJoint('upperarm_l', { x: 18 }))).toContain('shoulder_quiet_l');
  });

  it('rejects losing the supinated dumbbell grip', () => {
    const exercise: ExerciseDefinition = {
      ...bicepCurl,
      jointTargets: bicepCurl.jointTargets.map((target) =>
        target.bone === 'forearm_l' && target.axis === 'y'
          ? { ...target, start: 35, peak: 35 }
          : target,
      ),
    };
    // `grip_held_l` was `supinated_grip_l` until the curl family made the grip a
    // parameter: the rule now checks whichever grip the variant declares, so a
    // hammer curl is held to neutral by the same id rather than to a name that
    // only fits one variant.
    expect(violations(exercise)).toContain('grip_held_l');
  });

  it('rejects sideways wrist deviation', () => {
    expect(violations(withPeakJoint('hand_l', { x: 20 }))).toContain('wrist_deviation_l');
  });
});
