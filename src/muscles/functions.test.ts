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

function muscle(group: MuscleInstance['group'], side: MuscleInstance['side'] = 'l'): MuscleInstance {
  const found = MUSCLES.find((entry) => entry.group === group && entry.side === side);
  if (!found) throw new Error(`Missing ${group}_${side ?? 'centre'}`);
  return found;
}

function stretch(entry: MuscleInstance, rotations: Parameters<typeof poseFromDegrees>[0]): number {
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
    const biceps = muscle('biceps');
    const triceps = muscle('triceps');
    expect(stretch(biceps, { forearm_l: { x: 120 } })).toBeLessThan(0.9);
    expect(stretch(triceps, { forearm_l: { x: 120 } })).toBeGreaterThan(1.04);
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
    const quadriceps = muscle('quadriceps');
    const hamstrings = muscle('hamstrings');
    expect(stretch(quadriceps, { shin_l: { x: -110 } })).toBeGreaterThan(1.08);
    expect(stretch(hamstrings, { shin_l: { x: -110 } })).toBeLessThan(0.9);
  });
});
