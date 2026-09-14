from pathlib import Path


def read(path): return Path(path).read_text()
def write(path, text): Path(path).write_text(text)
def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)

# --- exercise schema -------------------------------------------------------
p = 'src/exercises/types.ts'
s = read(p)
s = replace_once(
    s,
    "import type { BoneName } from '../rig/boneNames';",
    "import type { BoneName, Finger } from '../rig/boneNames';",
    'Finger type import',
)
s = replace_once(
    s,
    """  /** How tightly the fingers close, 0 open to 1 fully closed. */
  closure: number;
}""",
    """  /** How tightly the fingers close, 0 open to 1 fully closed. */
  closure: number;
  /** Optional absolute closure for an individual digit; unspecified digits use `closure`. */
  digitClosure?: Partial<Record<Finger, number>>;
}""",
    'digit closure schema',
)
write(p, s)

# --- generator -------------------------------------------------------------
p = 'src/animation/generate.ts'
s = read(p)
s = replace_once(
    s,
    """export function applyGrip(pose: Pose, hands: HandSpec): void {
  const closure = Math.max(0, Math.min(1, hands.closure));
  if (closure <= 0) return;
  const profile = gripProfile(hands.gripPreset ?? hands.grip);""",
    """export function applyGrip(pose: Pose, hands: HandSpec): void {
  const closure = Math.max(0, Math.min(1, hands.closure));
  const profile = gripProfile(hands.gripPreset ?? hands.grip);""",
    'allow digit override with global zero',
)
s = replace_once(
    s,
    """    for (const finger of FINGERS) {
      const isThumb = finger === 'thumb';
      const segments = isThumb ? profile.thumb : profile.fingers;
      segments.forEach((maximum, index) => {""",
    """    for (const finger of FINGERS) {
      const digitClosure = Math.max(0, Math.min(1, hands.digitClosure?.[finger] ?? closure));
      if (digitClosure <= 0) continue;
      const isThumb = finger === 'thumb';
      const segments = isThumb ? profile.thumb : profile.fingers;
      segments.forEach((maximum, index) => {""",
    'per digit closure selection',
)
s = replace_once(
    s,
    """              ? toRad(profile.thumbOppositionX * closure)
              : existing?.x ?? 0,
          y: existing?.y ?? 0,
          z: sign * toRad(maximum * closure),""",
    """              ? toRad(profile.thumbOppositionX * digitClosure)
              : existing?.x ?? 0,
          y: existing?.y ?? 0,
          z: sign * toRad(maximum * digitClosure),""",
    'apply digit closure scale',
)
write(p, s)

# --- store actions ---------------------------------------------------------
p = 'src/editor/store.ts'
s = read(p)
s = replace_once(
    s,
    "import type { BoneName } from '../rig/boneNames';",
    "import type { BoneName, Finger } from '../rig/boneNames';",
    'store Finger import',
)
s = replace_once(
    s,
    "  setGripPreset: (preset: GripKind | null) => void;",
    "  setGripPreset: (preset: GripKind | null) => void;\n  setGripDigitClosure: (finger: Finger, closure: number | null) => void;\n  clearGripDigitClosures: () => void;",
    'store digit closure interface',
)
needle = """    setGripPreset: (preset) =>
      commit((document) => {
        const hands = { ...document.exercise.hands };
        if (preset === null || preset === hands.grip) delete hands.gripPreset;
        else hands.gripPreset = preset;
        const exercise = { ...document.exercise, hands };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),
"""
replacement = needle + r'''

    setGripDigitClosure: (finger, closure) =>
      commit((document) => {
        const hands = { ...document.exercise.hands };
        const digitClosure = { ...(hands.digitClosure ?? {}) };
        const value = closure === null ? null : Math.max(0, Math.min(1, closure));
        if (value === null || Math.abs(value - hands.closure) < 1e-9) delete digitClosure[finger];
        else digitClosure[finger] = value;
        if (Object.keys(digitClosure).length > 0) hands.digitClosure = digitClosure;
        else delete hands.digitClosure;
        const exercise = { ...document.exercise, hands };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),

    clearGripDigitClosures: () =>
      commit((document) => {
        if (!document.exercise.hands.digitClosure) return document;
        const hands = { ...document.exercise.hands };
        delete hands.digitClosure;
        const exercise = { ...document.exercise, hands };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),
'''
s = replace_once(s, needle, replacement, 'store digit closure actions')
write(p, s)

# --- Grip panel ------------------------------------------------------------
p = 'src/editor/panels/GripPanel.tsx'
s = read(p)
s = replace_once(
    s,
    "import type { Vec3 } from '../../rig/types';",
    "import type { Vec3 } from '../../rig/types';\nimport { FINGERS, type Finger } from '../../rig/boneNames';",
    'GripPanel fingers import',
)
s = replace_once(
    s,
    "  const setGripPreset = useStudio((state) => state.setGripPreset);",
    "  const setGripPreset = useStudio((state) => state.setGripPreset);\n  const setGripDigitClosure = useStudio((state) => state.setGripDigitClosure);\n  const clearGripDigitClosures = useStudio((state) => state.clearGripDigitClosures);",
    'GripPanel digit actions',
)
needle = """      <p className=\"panel__note\">
        Presets only change deterministic finger closure; they do not move the wrist, equipment or
        accepted arm animation. Changes remain undoable.
      </p>

      <h3>Current handle fit</h3>"""
replacement = r'''      <p className="panel__note">
        Presets only change deterministic finger closure; they do not move the wrist, equipment or
        accepted arm animation. Changes remain undoable.
      </p>

      <details className="grip-digit-details">
        <summary>Fine-tune individual digits</summary>
        <p className="panel__hint">
          Use these only when one digit needs less or more wrap. Unchanged digits continue to follow
          the global closure above, so the authored grip profile stays deterministic.
        </p>
        {FINGERS.map((finger: Finger) => {
          const overridden = exercise.hands.digitClosure?.[finger];
          const value = overridden ?? exercise.hands.closure;
          return (
            <label className="field" key={finger}>
              <span className="field__label">
                {finger.charAt(0).toUpperCase() + finger.slice(1)} · {Math.round(value * 100)}%
                {overridden !== undefined ? ' · custom' : ''}
              </span>
              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={value}
                onChange={(event) => setGripDigitClosure(finger, Number(event.target.value))}
              />
            </label>
          );
        })}
        <div className="button-row">
          <button
            type="button"
            disabled={!exercise.hands.digitClosure}
            onClick={clearGripDigitClosures}
          >
            Reset all digits to global closure
          </button>
        </div>
      </details>

      <h3>Current handle fit</h3>'''
s = replace_once(s, needle, replacement, 'GripPanel digit controls')
write(p, s)

# --- tests ----------------------------------------------------------------
p = 'src/exercises/gripProfiles.test.ts'
s = read(p)
insert = r'''

  it('can trim one digit without changing the rest of the accepted dumbbell grip', () => {
    const exercise = structuredClone(getExercise('dumbbell_bicep_curl'));
    exercise.hands.digitClosure = { pinky: 0.6 };
    const pose = generateClip(canonicalSkeleton, exercise).keyframes[0].pose;
    expect(deg(pose.rotations.pinky_01_l?.z)).toBeCloseTo(78 * 0.6, 8);
    expect(deg(pose.rotations.pinky_02_l?.z)).toBeCloseTo(95 * 0.6, 8);
    expect(deg(pose.rotations.index_01_l?.z)).toBeCloseTo(78 * 0.85, 8);
    expect(deg(pose.rotations.index_02_l?.z)).toBeCloseTo(95 * 0.85, 8);
  });

  it('uses the individual thumb closure for both opposition and wrap', () => {
    const exercise = structuredClone(getExercise('dumbbell_bicep_curl'));
    exercise.hands.digitClosure = { thumb: 0.7 };
    const pose = generateClip(canonicalSkeleton, exercise).keyframes[0].pose;
    expect(deg(pose.rotations.thumb_01_l?.x)).toBeCloseTo(-14 * 0.7, 8);
    expect(deg(pose.rotations.thumb_01_l?.z)).toBeCloseTo(-22 * 0.7, 8);
    expect(deg(pose.rotations.index_01_l?.z)).toBeCloseTo(78 * 0.85, 8);
  });
'''
s = replace_once(s, '\n});', insert + '\n});', 'digit closure grip tests')
write(p, s)

p = 'src/editor/store.test.ts'
s = read(p)
s += r'''


describe('per-digit grip closure authoring', () => {
  it('adds an undoable symmetric digit override and removes redundant values', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    expect(useStudio.getState().document.exercise.hands.digitClosure).toBeUndefined();
    useStudio.getState().setGripDigitClosure('pinky', 0.62);
    expect(useStudio.getState().document.exercise.hands.digitClosure?.pinky).toBeCloseTo(0.62, 8);
    useStudio.getState().undo();
    expect(useStudio.getState().document.exercise.hands.digitClosure).toBeUndefined();
    useStudio.getState().redo();
    expect(useStudio.getState().document.exercise.hands.digitClosure?.pinky).toBeCloseTo(0.62, 8);
    useStudio.getState().setGripDigitClosure('pinky', 0.85);
    expect(useStudio.getState().document.exercise.hands.digitClosure).toBeUndefined();
  });

  it('clears all digit trims in one undoable edit', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    useStudio.getState().setGripDigitClosure('thumb', 0.7);
    useStudio.getState().setGripDigitClosure('pinky', 0.6);
    useStudio.getState().clearGripDigitClosures();
    expect(useStudio.getState().document.exercise.hands.digitClosure).toBeUndefined();
    useStudio.getState().undo();
    expect(useStudio.getState().document.exercise.hands.digitClosure?.thumb).toBeCloseTo(0.7, 8);
    expect(useStudio.getState().document.exercise.hands.digitClosure?.pinky).toBeCloseTo(0.6, 8);
  });
});
'''
write(p, s)

# --- docs / Claude handoff -------------------------------------------------
p = 'docs/STUDIO_CAPABILITY_ROADMAP.md'
s = read(p)
needle = '- Equipment-aware deterministic hand-shape profiles now distinguish dumbbell, bar/pull-up, neutral handle, rope/thick-handle, floor/open-palm and relaxed grips; an optional authoring override changes hand shape without changing the exercise\'s semantic equipment grip.'
s = replace_once(
    s,
    needle,
    needle + '\n- Per-digit closure trims can independently adjust thumb/index/middle/ring/pinky on top of the active grip profile while unspecified digits continue to follow global closure. Defaults are absent, so accepted grips remain byte-for-byte generator-compatible until an author opts in.',
    'roadmap digit closure',
)
write(p, s)

p = 'AI_CHANGELOG.md'
s = read(p)
entry = '''### ChatGPT — 2026-09-14 — per-digit deterministic grip closure\n\nAdded optional `HandSpec.digitClosure` overrides for `thumb`, `index`, `middle`, `ring` and `pinky`. Each value is an absolute 0..1 closure for that digit; unspecified digits continue to use the existing global `hands.closure`. `applyGrip()` now chooses the digit-specific value before applying the active equipment-aware grip profile, including the thumb opposition proxy. The field is absent by default, so the accepted 85% dumbbell curl remains numerically identical until an author explicitly trims a digit.\n\nThe Grip workspace now contains a collapsed `Fine-tune individual digits` section with five deterministic sliders and one-shot reset. `setGripDigitClosure()` and `clearGripDigitClosures()` regenerate through normal undo/redo history; setting a digit back to the global closure removes the redundant override rather than persisting noise. Regression coverage proves a pinky-only trim leaves index closure at the accepted baseline, thumb trim drives both thumb-base opposition and thumb wrap, and store edits/reset/undo behave correctly. This is the intended next tool for thumb/pinky intersection cleanup before considering any whole-dumbbell translation.\n\n'''
s = replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n' + entry, 'digit closure changelog')
write(p, s)

print('Applied per-digit deterministic grip closure')
