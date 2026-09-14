from pathlib import Path

path = Path('src/exercises/definitions/bicepCurl.ts')
text = path.read_text(encoding='utf-8')

# Add explicit anti-shrug rules immediately after the torso-swing guard.
anchor = """    {
      kind: 'jointAngle',
      id: 'upper_arm_clear_l',
"""
rules = """    {
      kind: 'jointAngle',
      id: 'shoulder_relaxed_l',
      label: 'Left shoulder stays relaxed, not shrugged',
      bone: 'clavicle_l',
      axis: 'z',
      min: 0,
      max: 10,
      severity: 'error',
    },
    {
      kind: 'jointAngle',
      id: 'shoulder_relaxed_r',
      label: 'Right shoulder stays relaxed, not shrugged',
      bone: 'clavicle_r',
      axis: 'z',
      min: -10,
      max: 0,
      severity: 'error',
    },
"""
if anchor not in text:
    raise SystemExit('upper-arm technique anchor not found')
if "id: 'shoulder_relaxed_l'" not in text:
    text = text.replace(anchor, rules + anchor, 1)

# Tighten the already-existing shoulder takeover ceiling from 25° to 10°.
text = text.replace(
    "id: 'shoulder_quiet_l',\n      label: 'Left shoulder does not take over the lift',\n      bone: 'upperarm_l',\n      axis: 'x',\n      min: -5,\n      max: 25,",
    "id: 'shoulder_quiet_l',\n      label: 'Left shoulder does not take over the lift',\n      bone: 'upperarm_l',\n      axis: 'x',\n      min: -5,\n      max: 10,",
    1,
)
text = text.replace(
    "id: 'shoulder_quiet_r',\n      label: 'Right shoulder does not take over the lift',\n      bone: 'upperarm_r',\n      axis: 'x',\n      min: -5,\n      max: 25,",
    "id: 'shoulder_quiet_r',\n      label: 'Right shoulder does not take over the lift',\n      bone: 'upperarm_r',\n      axis: 'x',\n      min: -5,\n      max: 10,",
    1,
)

# Add supination and side-to-side wrist deviation checks before the existing
# wrist-flexion rules. The accepted curl lives comfortably inside these ranges.
anchor = """    {
      kind: 'jointAngle',
      id: 'wrist_neutral_l',
"""
rules = """    {
      kind: 'jointAngle',
      id: 'supinated_grip_l',
      label: 'Left palm stays supinated',
      bone: 'forearm_l',
      axis: 'y',
      min: 65,
      max: 90,
    },
    {
      kind: 'jointAngle',
      id: 'supinated_grip_r',
      label: 'Right palm stays supinated',
      bone: 'forearm_r',
      axis: 'y',
      min: -90,
      max: -65,
    },
    {
      kind: 'jointAngle',
      id: 'wrist_deviation_l',
      label: 'Left wrist does not deviate sideways',
      bone: 'hand_l',
      axis: 'x',
      min: -10,
      max: 10,
    },
    {
      kind: 'jointAngle',
      id: 'wrist_deviation_r',
      label: 'Right wrist does not deviate sideways',
      bone: 'hand_r',
      axis: 'x',
      min: -10,
      max: 10,
    },
"""
if anchor not in text:
    raise SystemExit('wrist technique anchor not found')
if "id: 'supinated_grip_l'" not in text:
    text = text.replace(anchor, rules + anchor, 1)

# Surface the shrug as a user-facing common error, tied to the validator rule.
anchor = """    {
      id: 'elbow_drift',
"""
error = """    {
      id: 'shrugging_shoulders',
      label: 'Shrugging the shoulders',
      description: 'Lifting the shoulders towards the ears as the dumbbells rise.',
      ruleId: 'shoulder_relaxed_l',
      correction: 'Keep the shoulders down and relaxed while the elbows do the work.',
    },
"""
if anchor not in text:
    raise SystemExit('common-error anchor not found')
if "id: 'shrugging_shoulders'" not in text:
    text = text.replace(anchor, error + anchor, 1)

path.write_text(text, encoding='utf-8')

# Targeted negative tests prove the new rules catch actual bad motion rather
# than merely existing in the definition.
Path('src/exercises/bicepCurlTechnique.test.ts').write_text("""import { describe, expect, it } from 'vitest';
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
    expect(violations(exercise)).toContain('supinated_grip_l');
  });

  it('rejects sideways wrist deviation', () => {
    expect(violations(withPeakJoint('hand_l', { x: 20 }))).toContain('wrist_deviation_l');
  });
});
""", encoding='utf-8')
