import { describe, expect, it } from 'vitest';
import type { BoneName } from '../rig/boneNames';
import { poseFromDegrees } from '../rig/pose';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { MUSCLE_GROUPS, MUSCLE_GROUP_IDS } from './groups';
import { MUSCLES, createMuscleTransform, resolveMuscle } from './model';
import type { MuscleInstance } from './model';

const skeleton = canonicalSkeleton;
const evaluation = new PoseEvaluation(skeleton);
const transform = createMuscleTransform();
type Degrees = Parameters<typeof poseFromDegrees>[0];

function muscle(group: MuscleInstance['group'], side: MuscleInstance['side'] = 'l'): MuscleInstance {
  const found = MUSCLES.find((entry) => entry.group === group && entry.side === side);
  if (!found) throw new Error(`Missing ${group}_${side ?? 'centre'}`);
  return found;
}

function stretch(entry: MuscleInstance, rotations: Degrees): number {
  evaluation.apply(poseFromDegrees(rotations));
  resolveMuscle(evaluation, entry, transform);
  return transform.stretch;
}

function inSubtree(root: BoneName, bone: BoneName): boolean {
  return root === bone || skeleton.isAncestorOf(root, bone);
}

describe('functional muscle paths', () => {
  it('crosses every joint each muscle group declares that it acts on', () => {
    for (const group of MUSCLE_GROUP_IDS) {
      const meta = MUSCLE_GROUPS[group];
      for (const actsOn of meta.actsOn) {
        const side = actsOn.endsWith('_l') ? 'l' : actsOn.endsWith('_r') ? 'r' : null;
        const candidates = MUSCLES.filter(
          (entry) => entry.group === group && (side === null || entry.side === side),
        );
        const spans = candidates.some((entry) => {
          const states = entry.path.map((point) => inSubtree(actsOn, point.bone));
          return states.some(Boolean) && states.some((value) => !value);
        });
        expect(spans, `${group} must cross ${actsOn}`).toBe(true);
      }
    }
  });

  it('makes biceps shorten and triceps lengthen during isolated elbow flexion', () => {
    expect(stretch(muscle('biceps'), { forearm_l: { x: 120 } })).toBeLessThan(0.9);
    expect(stretch(muscle('triceps'), { forearm_l: { x: 120 } })).toBeGreaterThan(1.04);
  });

  it('makes forearm flexors/extensors oppose one another through wrist flexion', () => {
    const flexors = muscle('forearm_flexors');
    const extensors = muscle('forearm_extensors');
    const flexorFlexed = stretch(flexors, { hand_l: { z: 60 } });
    const extensorFlexed = stretch(extensors, { hand_l: { z: 60 } });
    const flexorExtended = stretch(flexors, { hand_l: { z: -60 } });
    const extensorExtended = stretch(extensors, { hand_l: { z: -60 } });

    expect(flexorFlexed).toBeLessThan(0.94);
    expect(extensorFlexed).toBeGreaterThan(1.015);
    expect(flexorExtended).toBeGreaterThan(1.015);
    expect(extensorExtended).toBeLessThan(0.94);
  });

  it('makes quadriceps lengthen and hamstrings shorten through knee flexion', () => {
    expect(stretch(muscle('quadriceps'), { shin_l: { x: -110 } })).toBeGreaterThan(1.08);
    expect(stretch(muscle('hamstrings'), { shin_l: { x: -110 } })).toBeLessThan(0.9);
  });

  it('shortens the shoulder movers in their isolated trainer-level actions', () => {
    expect(stretch(muscle('pectoralis'), { upperarm_l: { x: 60 } })).toBeLessThan(0.98);
    expect(stretch(muscle('pectoralis'), { upperarm_l: { z: 30 } })).toBeLessThan(0.98);
    expect(stretch(muscle('deltoid_anterior'), { upperarm_l: { x: 60 } })).toBeLessThan(0.98);
    expect(stretch(muscle('deltoid_medial'), { upperarm_l: { z: -60 } })).toBeLessThan(0.98);
    expect(stretch(muscle('deltoid_posterior'), { upperarm_l: { x: -30 } })).toBeLessThan(0.98);
    expect(stretch(muscle('latissimus'), { upperarm_l: { x: -30 } })).toBeLessThan(0.98);
    expect(stretch(muscle('latissimus'), { upperarm_l: { z: 30 } })).toBeLessThan(0.98);
  });

  it('shortens the scapular and trunk groups in their isolated actions', () => {
    expect(stretch(muscle('trapezius_upper'), { clavicle_l: { z: -10 } })).toBeLessThan(0.995);
    expect(stretch(muscle('trapezius_mid'), { clavicle_l: { x: -12 } })).toBeLessThan(0.98);
    expect(stretch(muscle('erector_upper'), { spine_03: { x: -10 } })).toBeLessThan(0.98);
    expect(stretch(muscle('erector_mid'), { spine_02: { x: -10 } })).toBeLessThan(0.98);
    expect(stretch(muscle('erector_lower'), { spine_01: { x: -10 } })).toBeLessThan(0.98);
    expect(
      stretch(muscle('rectus_abdominis', null), {
        spine_01: { x: 20 }, spine_02: { x: 15 }, spine_03: { x: 10 },
      }),
    ).toBeLessThan(0.9);
    expect(
      stretch(muscle('obliques'), { spine_01: { z: 12 }, spine_02: { z: 12 } }),
    ).toBeLessThan(0.9);
  });

  it('shortens the hip and ankle movers in their isolated actions', () => {
    expect(stretch(muscle('gluteus'), { thigh_l: { x: -20 } })).toBeLessThan(0.95);
    expect(stretch(muscle('calves'), { foot_l: { x: -30 } })).toBeLessThan(0.995);
    expect(stretch(muscle('hip_adductors'), { thigh_l: { z: 20 } })).toBeLessThan(0.95);
    expect(stretch(muscle('hip_abductors'), { thigh_l: { z: -30 } })).toBeLessThan(0.95);
  });
});
