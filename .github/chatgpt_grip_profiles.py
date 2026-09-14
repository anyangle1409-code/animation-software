from pathlib import Path

def read(path): return Path(path).read_text()
def write(path,text): Path(path).write_text(text)
def replace_once(text,old,new,label):
    if old not in text: raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old,new,1)

# Shared deterministic hand-shape profiles. Dumbbell reproduces the existing generator exactly.
write('src/exercises/gripProfiles.ts', r'''import type { GripKind } from './types';

export interface GripProfile {
  id: GripKind;
  label: string;
  /** Flexion degrees for MCP / PIP / DIP of the four fingers at closure 1. */
  fingers: readonly [number, number, number];
  /** Thumb Z rotations for its three available segments at closure 1. */
  thumb: readonly [number, number, number];
  /** Thumb-base X rotation used as the rig's limited opposition proxy. */
  thumbOppositionX: number;
}

export const GRIP_PROFILES: Record<GripKind, GripProfile> = {
  none: {
    id: 'none',
    label: 'Open / relaxed',
    fingers: [0, 0, 0],
    thumb: [0, 0, 0],
    thumbOppositionX: 0,
  },
  // Compatibility baseline: these values are the original production curl hand.
  dumbbell: {
    id: 'dumbbell',
    label: 'Dumbbell wrap',
    fingers: [78, 95, 60],
    thumb: [-22, 60, 60],
    thumbOppositionX: -14,
  },
  bar: {
    id: 'bar',
    label: 'Bar / pull-up wrap',
    fingers: [76, 98, 66],
    thumb: [-24, 64, 64],
    thumbOppositionX: -16,
  },
  handle: {
    id: 'handle',
    label: 'Neutral handle',
    fingers: [82, 100, 68],
    thumb: [-26, 68, 65],
    thumbOppositionX: -18,
  },
  rope: {
    id: 'rope',
    label: 'Rope / thick handle',
    fingers: [88, 105, 72],
    thumb: [-28, 70, 68],
    thumbOppositionX: -20,
  },
  // A floor contact is a spread hand, not a cylindrical grip. Existing push-up
  // closure is only 0.05, so this keeps the fingers essentially straight.
  floor: {
    id: 'floor',
    label: 'Floor / open palm',
    fingers: [18, 12, 8],
    thumb: [6, 8, 6],
    thumbOppositionX: -4,
  },
};

export const GRIP_PROFILE_LIST = Object.values(GRIP_PROFILES);

export function gripProfile(grip: GripKind): GripProfile {
  return GRIP_PROFILES[grip];
}
''')

p='src/exercises/types.ts'
s=read(p)
s=replace_once(s, "  grip: GripKind;\n  /** Where the palms face", "  grip: GripKind;\n  /** Optional hand-shape override; semantic equipment grip remains `grip`. */\n  gripPreset?: GripKind;\n  /** Where the palms face", 'grip preset type')
write(p,s)

# Apply profile in generator while preserving exact dumbbell outputs.
p='src/animation/generate.ts'
s=read(p)
s=replace_once(s, "import { tempoDuration } from '../exercises/types';", "import { tempoDuration } from '../exercises/types';\nimport { gripProfile } from '../exercises/gripProfiles';", 'profile import')
old='''export function applyGrip(pose: Pose, hands: HandSpec): void {
  const closure = Math.max(0, Math.min(1, hands.closure));
  if (closure <= 0) return;
  const sides: { side: Side; sign: number }[] = [
    { side: 'l', sign: 1 },
    { side: 'r', sign: -1 },
  ];
  for (const { side, sign } of sides) {
    for (const finger of FINGERS) {
      const isThumb = finger === 'thumb';
      // The thumb does not curl like the other four. This rig starts it at the
      // knuckle, with no carpometacarpal joint to oppose with, so it cannot come
      // back across the palm: extending the base and folding the two segments
      // beyond it lays the thumb along the handle, against the bar and beside
      // the index finger, instead of sweeping it past the palm into the air.
      const segments = isThumb ? [-22, 60, 60] : [78, 95, 60];
      segments.forEach((maximum, index) => {
        const bone = `${finger}_0${index + 1}_${side}` as BoneName;
        const existing = pose.rotations[bone];
        pose.rotations[bone] = {
          x: isThumb && index === 0 ? toRad(-14 * closure) : existing?.x ?? 0,
          y: existing?.y ?? 0,
          z: sign * toRad(maximum * closure),
        };
      });
    }
  }
}'''
new='''export function applyGrip(pose: Pose, hands: HandSpec): void {
  const closure = Math.max(0, Math.min(1, hands.closure));
  if (closure <= 0) return;
  const profile = gripProfile(hands.gripPreset ?? hands.grip);
  const sides: { side: Side; sign: number }[] = [
    { side: 'l', sign: 1 },
    { side: 'r', sign: -1 },
  ];
  for (const { side, sign } of sides) {
    for (const finger of FINGERS) {
      const isThumb = finger === 'thumb';
      const segments = isThumb ? profile.thumb : profile.fingers;
      segments.forEach((maximum, index) => {
        const bone = `${finger}_0${index + 1}_${side}` as BoneName;
        const existing = pose.rotations[bone];
        pose.rotations[bone] = {
          x:
            isThumb && index === 0
              ? toRad(profile.thumbOppositionX * closure)
              : existing?.x ?? 0,
          y: existing?.y ?? 0,
          z: sign * toRad(maximum * closure),
        };
      });
    }
  }
}'''
s=replace_once(s,old,new,'profile driven grip')
write(p,s)

# Store authoring for profile override/reset.
p='src/editor/store.ts'
s=read(p)
s=replace_once(s, "import type { ExerciseDefinition, PhaseJointTiming, Tempo } from '../exercises/types';", "import type { ExerciseDefinition, GripKind, PhaseJointTiming, Tempo } from '../exercises/types';", 'GripKind store import')
s=replace_once(s, "  setGripClosure: (closure: number) => void;", "  setGripClosure: (closure: number) => void;\n  setGripPreset: (preset: GripKind | null) => void;", 'set grip preset interface')
insert='''

    setGripPreset: (preset) =>
      commit((document) => {
        const hands = { ...document.exercise.hands };
        if (preset === null || preset === hands.grip) delete hands.gripPreset;
        else hands.gripPreset = preset;
        const exercise = { ...document.exercise, hands };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),
'''
s=replace_once(s, "\n    setEquipmentGripOffset: (instanceId, offset) =>", insert+"\n    setEquipmentGripOffset: (instanceId, offset) =>", 'set grip preset implementation')
write(p,s)

# Grip panel profile chooser.
p='src/editor/panels/GripPanel.tsx'
s=read(p)
s=replace_once(s, "import type { Vec3 } from '../../rig/types';", "import type { Vec3 } from '../../rig/types';\nimport { GRIP_PROFILE_LIST } from '../../exercises/gripProfiles';", 'GripPanel profile import')
s=replace_once(s, "  const setGripClosure = useStudio((state) => state.setGripClosure);", "  const setGripClosure = useStudio((state) => state.setGripClosure);\n  const setGripPreset = useStudio((state) => state.setGripPreset);", 'GripPanel setter')
needle='''      <h3>Closure</h3>
      <label className="field">'''
replacement='''      <h3>Hand shape</h3>
      <label className="field">
        <span className="field__label">Grip profile</span>
        <select
          value={exercise.hands.gripPreset ?? exercise.hands.grip}
          onChange={(event) => {
            const value = event.target.value as typeof exercise.hands.grip;
            setGripPreset(value === exercise.hands.grip ? null : value);
          }}
        >
          {GRIP_PROFILE_LIST.map((profile) => (
            <option key={profile.id} value={profile.id}>{profile.label}</option>
          ))}
        </select>
      </label>
      <p className="panel__note">
        The exercise still records its semantic grip as <strong>{exercise.hands.grip}</strong>. This
        selector only overrides the generated finger/thumb shape for authoring.
      </p>

      <h3>Closure</h3>
      <label className="field">'''
s=replace_once(s,needle,replacement,'GripPanel profile selector')
write(p,s)

# Tests for compatibility and distinct deterministic shapes.
write('src/exercises/gripProfiles.test.ts', r'''import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { canonicalSkeleton } from '../rig/skeleton';
import { getExercise } from './library';
import type { GripKind } from './types';

const deg = (radians: number | undefined) => ((radians ?? 0) * 180) / Math.PI;

function poseFor(preset: GripKind) {
  const source = getExercise('dumbbell_bicep_curl');
  const exercise = structuredClone(source);
  exercise.hands.gripPreset = preset;
  return generateClip(canonicalSkeleton, exercise).keyframes[0].pose;
}

describe('equipment-aware grip profiles', () => {
  it('keeps the authored dumbbell curl hand exactly compatible with the original profile', () => {
    const exercise = getExercise('dumbbell_bicep_curl');
    const pose = generateClip(canonicalSkeleton, exercise).keyframes[0].pose;
    expect(deg(pose.rotations.index_01_l?.z)).toBeCloseTo(78 * 0.85, 8);
    expect(deg(pose.rotations.index_02_l?.z)).toBeCloseTo(95 * 0.85, 8);
    expect(deg(pose.rotations.thumb_01_l?.z)).toBeCloseTo(-22 * 0.85, 8);
    expect(deg(pose.rotations.thumb_01_l?.x)).toBeCloseTo(-14 * 0.85, 8);
  });

  it('produces distinct bar, handle and rope hand shapes deterministically', () => {
    const bar = poseFor('bar');
    const handle = poseFor('handle');
    const rope = poseFor('rope');
    expect(deg(bar.rotations.index_01_l?.z)).toBeCloseTo(76 * 0.85, 8);
    expect(deg(handle.rotations.index_01_l?.z)).toBeCloseTo(82 * 0.85, 8);
    expect(deg(rope.rotations.index_01_l?.z)).toBeCloseTo(88 * 0.85, 8);
    expect(deg(rope.rotations.thumb_01_l?.x)).toBeCloseTo(-20 * 0.85, 8);
  });

  it('keeps a floor-contact profile almost open at push-up closure', () => {
    const exercise = getExercise('push_up');
    const pose = generateClip(canonicalSkeleton, exercise).keyframes[0].pose;
    expect(Math.abs(deg(pose.rotations.index_01_l?.z))).toBeLessThan(1);
    expect(Math.abs(deg(pose.rotations.index_02_l?.z))).toBeLessThan(1);
  });
});
''')

p='src/editor/store.test.ts'
s=read(p)
s += r'''


describe('grip profile authoring', () => {
  it('adds an undoable hand-shape override without changing semantic equipment grip', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    expect(useStudio.getState().document.exercise.hands.grip).toBe('dumbbell');
    expect(useStudio.getState().document.exercise.hands.gripPreset).toBeUndefined();
    useStudio.getState().setGripPreset('handle');
    expect(useStudio.getState().document.exercise.hands.grip).toBe('dumbbell');
    expect(useStudio.getState().document.exercise.hands.gripPreset).toBe('handle');
    useStudio.getState().undo();
    expect(useStudio.getState().document.exercise.hands.gripPreset).toBeUndefined();
  });

  it('clears a redundant override when reset to the semantic grip', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    useStudio.getState().setGripPreset('rope');
    useStudio.getState().setGripPreset('dumbbell');
    expect(useStudio.getState().document.exercise.hands.gripPreset).toBeUndefined();
  });
});
'''
write(p,s)

p='docs/STUDIO_CAPABILITY_ROADMAP.md'
s=read(p)
needle='- Dedicated Grip workspace provides undoable closure presets and live measured finger/handle fit using the established regression envelope.'
s=replace_once(s,needle,needle+'\n- Equipment-aware deterministic hand-shape profiles now distinguish dumbbell, bar/pull-up, neutral handle, rope/thick-handle, floor/open-palm and relaxed grips; an optional authoring override changes hand shape without changing the exercise\'s semantic equipment grip.', 'roadmap grip profiles')
write(p,s)

p='AI_CHANGELOG.md'
s=read(p)
entry='''### ChatGPT — 2026-09-14 — equipment-aware deterministic grip profiles\n\nReplaced the one-size-fits-all finger generator with explicit deterministic profiles for `dumbbell`, `bar`, `handle`, `rope`, `floor` and `none`. The **dumbbell profile exactly preserves the previous production values** (`[78,95,60]` finger flexion, `[-22,60,60]` thumb Z and -14° thumb-base X at closure 1), so the accepted bicep-curl hand shape does not silently change. Bar/pull-up, neutral handle and rope profiles now have distinct finger/thumb closure and opposition values; the floor profile is intentionally near-open, matching a planted palm rather than a cylindrical wrap.\n\n`HandSpec.grip` remains the semantic equipment grip. A new optional `gripPreset` is only a generated hand-shape override, allowing authoring experiments without falsely changing exercise/equipment metadata. The Grip workspace exposes this as a profile selector and `setGripPreset` regenerates deterministically through normal undo/redo history. Regressions preserve the exact dumbbell baseline, prove bar/handle/rope generate distinct shapes, keep push-up fingers effectively open at its 5% closure, and verify the override is undoable while semantic grip remains unchanged.\n\n'''
s=replace_once(s,'## Unreleased\n\n','## Unreleased\n\n\n'+entry,'grip profile changelog')
write(p,s)

print('Applied equipment-aware grip profiles')
