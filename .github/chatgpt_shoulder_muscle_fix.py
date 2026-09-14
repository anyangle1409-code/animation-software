from pathlib import Path

model_path = Path('src/muscles/model.ts')
text = model_path.read_text(encoding='utf-8')


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'expected one match, found {count}: {old[:80]!r}')
    text = text.replace(old, new, 1)

replace_once(
"""  {
    group: 'deltoid_medial',
    origin: at('clavicle_l', 0.016, 0.13, 0),
    insertion: at('upperarm_l', 0.026, 0.14, 0),
    thickness: 0.042,
    bulge: 0.3,
  },
""",
"""  {
    group: 'deltoid_medial',
    // Lateral acromion to deltoid tuberosity. The previous line sat too far
    // inside the shoulder and actually lengthened as the arm abducted.
    origin: at('clavicle_l', 0.03, 0.15, 0),
    insertion: at('upperarm_l', 0.05, 0.11, 0),
    thickness: 0.042,
    bulge: 0.3,
  },
""",
)

replace_once(
"""  {
    group: 'pectoralis',
    origin: at('spine_03', -0.045, 0.04, 0.082),
    // The insertion sits at the head of the humerus rather than down its shaft:
    // with the arm overhead, a belly drawn to mid-humerus cuts straight across
    // the armpit and out through the skin.
    insertion: at('upperarm_l', 0.014, 0.028, 0.012),
    thickness: 0.032,
    bulge: 0.3,
    flatten: 0.6,
    spread: 1.6,
  },
""",
"""  {
    group: 'pectoralis',
    // A high anterior chest line represents the trainer-level pectoral group.
    // It keeps the proximal humeral insertion used for overhead containment,
    // but now shortens in both shoulder flexion and adduction instead of only
    // the latter. More detailed clavicular/sternal heads can be layered later
    // without changing the exercise-level activation group.
    origin: at('spine_03', -0.025, 0.1, 0.12),
    insertion: at('upperarm_l', 0, 0.05, 0.01),
    thickness: 0.032,
    bulge: 0.3,
    flatten: 0.6,
    spread: 1.6,
  },
""",
)

replace_once(
"""  {
    group: 'latissimus',
    origin: at('spine_01', -0.055, 0.02, -0.06),
    insertion: at('upperarm_l', 0.014, 0.028, -0.014),
    thickness: 0.032,
    bulge: 0.25,
    flatten: 0.55,
    spread: 1.5,
  },
""",
"""  {
    group: 'latissimus',
    origin: at('spine_01', -0.055, 0.02, -0.06),
    // The tendon wraps around the proximal humerus to its anterior insertion.
    // This is what lets the same path correctly shorten for both shoulder
    // extension and adduction rather than behaving like a straight back strap.
    via: [at('upperarm_l', 0.04, 0.03, 0.04)],
    insertion: at('upperarm_l', 0.04, 0.04, 0.01),
    thickness: 0.032,
    bulge: 0.25,
    flatten: 0.55,
    spread: 1.5,
  },
""",
)

model_path.write_text(text, encoding='utf-8')

functions = Path('src/muscles/functions.test.ts')
functions.write_text(r'''import { describe, expect, it } from 'vitest';
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
''', encoding='utf-8')

print('Applied shoulder muscle paths and comprehensive isolated-action gates')
