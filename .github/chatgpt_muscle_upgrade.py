from pathlib import Path

MODEL = Path('src/muscles/model.ts')
text = MODEL.read_text(encoding='utf-8')


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'expected exactly one match, found {count}: {old[:80]!r}')
    text = text.replace(old, new, 1)

replace_once(
"""export interface MuscleDefinition {\n  group: MuscleGroupId;\n  origin: { bone: BoneName; offset: Vec3 };\n  insertion: { bone: BoneName; offset: Vec3 };\n""",
"""export interface MuscleAttachment {\n  bone: BoneName;\n  offset: Vec3;\n}\n\nexport interface MuscleDefinition {\n  group: MuscleGroupId;\n  origin: MuscleAttachment;\n  insertion: MuscleAttachment;\n  /**\n   * Optional anatomical wrap/via points between origin and insertion. These\n   * affect functional path length (and therefore shortening/bulging) without\n   * forcing the visible belly to cut straight through a joint.\n   */\n  via?: MuscleAttachment[];\n""",
)

replace_once(
"""  {\n    group: 'triceps',\n    origin: at('upperarm_l', 0.003, 0.055, -0.018),\n    insertion: at('forearm_l', 0.002, 0.018, -0.01),\n    thickness: 0.031,\n    bulge: 0.3,\n  },\n""",
"""  {\n    group: 'triceps',\n    origin: at('upperarm_l', 0.003, 0.055, -0.018),\n    // The tendon wraps behind the elbow. Without this posterior via point a\n    // straight chord incorrectly SHORTENS as the elbow flexes.\n    via: [at('upperarm_l', 0.002, 0.292, -0.035)],\n    insertion: at('forearm_l', 0.002, 0.018, -0.01),\n    thickness: 0.031,\n    bulge: 0.3,\n  },\n""",
)

replace_once(
"""  {\n    group: 'forearm_flexors',\n    origin: at('forearm_l', -0.003, 0.035, 0.015),\n    insertion: at('forearm_l', -0.002, 0.185, 0.005),\n    thickness: 0.025,\n    bulge: 0.2,\n    spread: 1.1,\n  },\n""",
"""  {\n    group: 'forearm_flexors',\n    origin: at('forearm_l', -0.003, 0.035, 0.015),\n    // Cross the wrist onto the hand so wrist flexion changes functional length.\n    // A shorter belly taper keeps the visible muscle mass in the forearm while\n    // the tendon-like end follows the hand.\n    insertion: at('hand_l', -0.02, 0.02, 0.01),\n    thickness: 0.025,\n    bulge: 0.2,\n    spread: 1.1,\n    taper: 0.68,\n  },\n""",
)

replace_once(
"""  {\n    group: 'forearm_extensors',\n    origin: at('forearm_l', 0.004, 0.035, -0.015),\n    insertion: at('forearm_l', 0.003, 0.185, -0.005),\n    thickness: 0.023,\n    bulge: 0.2,\n    spread: 1.1,\n  },\n""",
"""  {\n    group: 'forearm_extensors',\n    origin: at('forearm_l', 0.004, 0.035, -0.015),\n    insertion: at('hand_l', 0.02, 0.02, -0.01),\n    thickness: 0.023,\n    bulge: 0.2,\n    spread: 1.1,\n    taper: 0.68,\n  },\n""",
)

replace_once(
"""  {\n    group: 'quadriceps',\n    origin: at('thigh_l', 0, 0.07, 0.04),\n    insertion: at('shin_l', 0, 0.03, 0.03),\n    thickness: 0.045,\n    bulge: 0.35,\n    spread: 1.2,\n  },\n""",
"""  {\n    group: 'quadriceps',\n    origin: at('thigh_l', 0, 0.07, 0.04),\n    // Approximate the patellar/anterior-knee wrap. The functional path must\n    // lengthen continuously as the knee flexes instead of cutting across it.\n    via: [at('thigh_l', 0, 0.415, 0.05)],\n    insertion: at('shin_l', 0, 0.03, 0.03),\n    thickness: 0.045,\n    bulge: 0.35,\n    spread: 1.2,\n  },\n""",
)

replace_once(
"""export function mirrorMuscle(muscle: MuscleDefinition): MuscleDefinition {\n  return {\n    ...muscle,\n    ...(muscle.outward ? { outward: mirrorOffset(muscle.outward) } : {}),\n    origin: { bone: mirrorBone(muscle.origin.bone), offset: mirrorOffset(muscle.origin.offset) },\n    insertion: {\n      bone: mirrorBone(muscle.insertion.bone),\n      offset: mirrorOffset(muscle.insertion.offset),\n    },\n  };\n}\n""",
"""export function mirrorMuscle(muscle: MuscleDefinition): MuscleDefinition {\n  return {\n    ...muscle,\n    ...(muscle.outward ? { outward: mirrorOffset(muscle.outward) } : {}),\n    ...(muscle.via\n      ? {\n          via: muscle.via.map((attachment) => ({\n            bone: mirrorBone(attachment.bone),\n            offset: mirrorOffset(attachment.offset),\n          })),\n        }\n      : {}),\n    origin: { bone: mirrorBone(muscle.origin.bone), offset: mirrorOffset(muscle.origin.offset) },\n    insertion: {\n      bone: mirrorBone(muscle.insertion.bone),\n      offset: mirrorOffset(muscle.insertion.offset),\n    },\n  };\n}\n""",
)

replace_once(
"""export interface MuscleInstance extends MuscleDefinition {\n  id: string;\n  side: Side | null;\n  /** Origin-to-insertion distance in the rest pose, for the bulge calculation. */\n  restLength: number;\n""",
"""export interface MuscleInstance extends MuscleDefinition {\n  id: string;\n  side: Side | null;\n  /** Full functional origin -> via point(s) -> insertion path. */\n  path: readonly MuscleAttachment[];\n  /** Functional path length in the rest pose, for the bulge calculation. */\n  restLength: number;\n""",
)

replace_once(
"""const restScratch = { origin: new Vector3(), insertion: new Vector3() };\nlet restEvaluation: PoseEvaluation | undefined;\n""",
"""const restScratch = { origin: new Vector3(), insertion: new Vector3() };\nconst pathScratchA = new Vector3();\nconst pathScratchB = new Vector3();\nlet restEvaluation: PoseEvaluation | undefined;\n\nfunction measurePath(evaluation: PoseEvaluation, path: readonly MuscleAttachment[]): number {\n  if (path.length < 2) return 0;\n  evaluation.localToWorld(path[0].bone, path[0].offset, pathScratchA);\n  let total = 0;\n  for (let index = 1; index < path.length; index += 1) {\n    const attachment = path[index];\n    evaluation.localToWorld(attachment.bone, attachment.offset, pathScratchB);\n    total += pathScratchA.distanceTo(pathScratchB);\n    pathScratchA.copy(pathScratchB);\n  }\n  return total;\n}\n""",
)

replace_once(
"""export function muscleInstance(muscle: MuscleDefinition, side: Side | null): MuscleInstance {\n  const evaluation = (restEvaluation ??= new PoseEvaluation(canonicalSkeleton).apply(restPose()));\n  const { origin, insertion } = restScratch;\n  evaluation.localToWorld(muscle.origin.bone, muscle.origin.offset, origin);\n  evaluation.localToWorld(muscle.insertion.bone, muscle.insertion.offset, insertion);\n  const authored = muscle.outward ?? vec3(muscle.origin.offset.x, 0, muscle.origin.offset.z);\n  const outwardAxis = new Vector3(authored.x, authored.y, authored.z);\n  if (outwardAxis.lengthSq() < 1e-8) outwardAxis.set(0, 0, 1);\n  const bones = new Set<string>([muscle.origin.bone, muscle.insertion.bone]);\n  for (const bone of [muscle.origin.bone, muscle.insertion.bone]) {\n    const parent = canonicalSkeleton.bone(bone).parent;\n    if (parent && parent !== 'root') bones.add(parent);\n  }\n  return {\n    ...muscle,\n    id: side ? `${muscle.group}_${side}` : muscle.group,\n    side,\n    restLength: Math.max(0.02, origin.distanceTo(insertion)),\n    outwardAxis: outwardAxis.normalize(),\n    fitBones: bones,\n  };\n}\n""",
"""export function muscleInstance(muscle: MuscleDefinition, side: Side | null): MuscleInstance {\n  const evaluation = (restEvaluation ??= new PoseEvaluation(canonicalSkeleton).apply(restPose()));\n  const { origin, insertion } = restScratch;\n  const path: readonly MuscleAttachment[] = [\n    muscle.origin,\n    ...(muscle.via ?? []),\n    muscle.insertion,\n  ];\n  evaluation.localToWorld(muscle.origin.bone, muscle.origin.offset, origin);\n  evaluation.localToWorld(muscle.insertion.bone, muscle.insertion.offset, insertion);\n  const authored = muscle.outward ?? vec3(muscle.origin.offset.x, 0, muscle.origin.offset.z);\n  const outwardAxis = new Vector3(authored.x, authored.y, authored.z);\n  if (outwardAxis.lengthSq() < 1e-8) outwardAxis.set(0, 0, 1);\n  const bones = new Set<string>(path.map((attachment) => attachment.bone));\n  for (const attachment of path) {\n    const parent = canonicalSkeleton.bone(attachment.bone).parent;\n    if (parent && parent !== 'root') bones.add(parent);\n  }\n  return {\n    ...muscle,\n    id: side ? `${muscle.group}_${side}` : muscle.group,\n    side,\n    path,\n    restLength: Math.max(0.02, measurePath(evaluation, path)),\n    outwardAxis: outwardAxis.normalize(),\n    fitBones: bones,\n  };\n}\n""",
)

replace_once(
"""  directionScratch.subVectors(insertionScratch, originScratch);\n\n  const length = Math.max(0.01, directionScratch.length());\n  const stretch = length / muscle.restLength;\n  const bulge = 1 + (muscle.bulge ?? 0.25) * Math.max(-0.5, Math.min(0.9, 1 / stretch - 1));\n\n  out.position.copy(originScratch).addScaledVector(directionScratch, 0.5);\n  directionScratch.divideScalar(length);\n""",
"""  directionScratch.subVectors(insertionScratch, originScratch);\n\n  // Keep the visible belly aligned between its authored end points, but drive\n  // contraction from the full anatomical path. This lets a tendon wrap around\n  // an elbow/knee while retaining the inexpensive fitted ellipsoid renderer.\n  const length = Math.max(0.01, directionScratch.length());\n  const functionalLength = Math.max(0.01, measurePath(evaluation, muscle.path));\n  const stretch = functionalLength / muscle.restLength;\n  const bulge = 1 + (muscle.bulge ?? 0.25) * Math.max(-0.5, Math.min(0.9, 1 / stretch - 1));\n\n  out.position.copy(originScratch).addScaledVector(directionScratch, 0.5);\n  directionScratch.divideScalar(length);\n""",
)

MODEL.write_text(text, encoding='utf-8')

Path('src/muscles/functions.test.ts').write_text(r'''import { describe, expect, it } from 'vitest';
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
''', encoding='utf-8')

Path('docs/STUDIO_CAPABILITY_ROADMAP.md').write_text(r'''# Animation Studio capability roadmap

The target is **not a clone of Blender**. It is a specialist exercise-animation authoring studio with Blender-like control where biomechanics needs it, while keeping the runtime deterministic and exportable to Home Gym PT.

## Acceptance target

An exercise is ready for the PT app only when the Studio can author, inspect and automatically validate the movement without relying on hidden manual fixes. The character, equipment, contacts, joint motion, grip, muscle behaviour and corrective deformation must all remain deterministic when the clip is regenerated.

## 1. Biomechanical core — first priority

- Joint-spanning muscle paths with wrap/via points where a straight chord is anatomically wrong.
- Functional tests for agonist/antagonist behaviour at elbow, wrist, knee, ankle, hip, shoulder/scapula and spine.
- Muscle containment and bilateral symmetry remain hard regression gates.
- Preserve-source-skeleton imported-character retargeting remains mandatory.
- Corrective deformation stays explicit, bounded and joint-driven.

## 2. Rig / pose workspace

- Select any anatomical joint in the viewport.
- FK rotation gizmos plus exact numeric angles and anatomical limits.
- IK handles for hands/feet with visible pole targets and contact error.
- Skeleton-inside-character diagnostic mode.
- Pose copy/mirror/reset and side-to-side comparison.
- Finger and thumb selection down to individual joints.

## 3. Animation workspace

- Dope-sheet style phase/keyframe lane rather than a general Blender timeline.
- Frame stepping, normal / 1/2 / 1/4 speed and loop-range playback.
- Per-joint timing, delay, finish and easing controls.
- Pose markers for start / transition / peak / return.
- Side-by-side candidate comparison without changing the accepted clip.

## 4. Hand / grip workspace

- Grip presets for dumbbell, barbell, cable handle, pull-up bar, neutral handle and floor contact.
- Whole-hand closure plus individual finger and thumb opposition controls.
- Handle position/orientation calibration with penetration measurement.
- Rigid equipment attachment and bilateral symmetry checks.

## 5. Equipment / contact workspace

- Selectable equipment objects and sockets.
- Move/rotate authoring gizmos for equipment setup.
- Explicit world/equipment/floor contact locks.
- Live contact-distance and reachability diagnostics.

## 6. Corrective deformation workspace

- Joint-angle-driven corrective shapes for elbow, shoulder, hip, knee and wrist when skinning alone is insufficient.
- Safe displacement caps and zero-at-neutral guarantees.
- Before/after A/B view plus mesh-strain diagnostics.
- No destructive rebinding of imported characters.

## 7. Diagnostics and approval

- Focus-selected camera and joint-angle readout.
- Muscle path/stretch readout.
- Grip penetration, equipment drift, contact error, symmetry and mesh strain.
- Exercise-specific technique validators.
- One explicit Approved state only after automated checks and visual review pass.

## 8. Template-driven scale

- Reusable movement families (curl, press, row/pull, squat, hinge, lunge, calf raise, core, locomotion).
- Shared grip/contact/equipment presets.
- Exercise definitions supply the movement data; the engine supplies the solver/validation.
- New exercises should usually be data authoring, not new bespoke animation code.

## Deliberately out of scope

Sculpting, UV editing, texture painting, compositing, particles, general scene modelling and arbitrary renderer/node systems stay in Blender or another DCC. The Studio should own everything needed to pose, animate, validate and export exercise demonstrations.
''', encoding='utf-8')

print('Applied muscle-path upgrade, functional tests, and capability roadmap')
