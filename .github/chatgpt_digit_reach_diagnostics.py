from pathlib import Path


def read(path): return Path(path).read_text()
def write(path, text): Path(path).write_text(text)
def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)

# --- diagnostic engine ----------------------------------------------------
p = 'src/equipment/gripDiagnostics.ts'
s = read(p)
s = replace_once(
    s,
    "import type { BoneName, Side } from '../rig/boneNames';",
    "import type { BoneName, Finger, Side } from '../rig/boneNames';",
    'Finger diagnostic type import',
)
s = replace_once(
    s,
    """interface GripContactPoint {
  bone: BoneName;
  along: number;
  reach: number;
}""",
    """interface GripContactPoint {
  finger: Finger;
  bone: BoneName;
  along: number;
  reach: number;
}""",
    'tag grip contact with digit',
)
s = replace_once(
    s,
    """  /** Largest measured distance as a fraction of that contact's allowed reach. */
  reachUse: number;
  /** Largest angular opening between neighbouring contacts around the handle. */""",
    """  /** Largest measured distance as a fraction of that contact's allowed reach. */
  reachUse: number;
  /** Largest reach use for each digit; values above 1 exceed the authored geometric envelope. */
  digitReachUse: Record<Finger, number>;
  /** Largest angular opening between neighbouring contacts around the handle. */""",
    'digit reach result schema',
)
old = """export const gripContactPoints = (side: Side): GripContactPoint[] => [
  { bone: `index_02_${side}` as BoneName, along: 0.5, reach: 0.032 },
  { bone: `index_03_${side}` as BoneName, along: 1, reach: 0.04 },
  { bone: `middle_02_${side}` as BoneName, along: 0.5, reach: 0.032 },
  { bone: `middle_03_${side}` as BoneName, along: 1, reach: 0.04 },
  { bone: `ring_02_${side}` as BoneName, along: 0.5, reach: 0.034 },
  { bone: `pinky_02_${side}` as BoneName, along: 0.5, reach: 0.038 },
  { bone: `thumb_02_${side}` as BoneName, along: 0.5, reach: 0.042 },
  { bone: `thumb_03_${side}` as BoneName, along: 1, reach: 0.032 },
];"""
new = """export const gripContactPoints = (side: Side): GripContactPoint[] => [
  { finger: 'index', bone: `index_02_${side}` as BoneName, along: 0.5, reach: 0.032 },
  { finger: 'index', bone: `index_03_${side}` as BoneName, along: 1, reach: 0.04 },
  { finger: 'middle', bone: `middle_02_${side}` as BoneName, along: 0.5, reach: 0.032 },
  { finger: 'middle', bone: `middle_03_${side}` as BoneName, along: 1, reach: 0.04 },
  { finger: 'ring', bone: `ring_02_${side}` as BoneName, along: 0.5, reach: 0.034 },
  { finger: 'pinky', bone: `pinky_02_${side}` as BoneName, along: 0.5, reach: 0.038 },
  { finger: 'thumb', bone: `thumb_02_${side}` as BoneName, along: 0.5, reach: 0.042 },
  { finger: 'thumb', bone: `thumb_03_${side}` as BoneName, along: 1, reach: 0.032 },
];"""
s = replace_once(s, old, new, 'digit tagged contact points')
s = replace_once(
    s,
    """  let reachUse = 0;
  const angles: number[] = [];
  for (const point of gripContactPoints(side)) {
    const offset = pointOf(evaluation, point.bone, point.along).sub(handle);
    offset.addScaledVector(axis, -offset.dot(axis));
    reachUse = Math.max(reachUse, offset.length() / point.reach);
    angles.push(Math.atan2(offset.dot(up), offset.dot(across)));
  }""",
    """  let reachUse = 0;
  const digitReachUse: Record<Finger, number> = {
    thumb: 0,
    index: 0,
    middle: 0,
    ring: 0,
    pinky: 0,
  };
  const angles: number[] = [];
  for (const point of gripContactPoints(side)) {
    const offset = pointOf(evaluation, point.bone, point.along).sub(handle);
    offset.addScaledVector(axis, -offset.dot(axis));
    const contactReachUse = offset.length() / point.reach;
    reachUse = Math.max(reachUse, contactReachUse);
    digitReachUse[point.finger] = Math.max(digitReachUse[point.finger], contactReachUse);
    angles.push(Math.atan2(offset.dot(up), offset.dot(across)));
  }""",
    'aggregate digit reach use',
)
s = replace_once(
    s,
    """    side,
    reachUse,
    widestGapDeg,""",
    """    side,
    reachUse,
    digitReachUse,
    widestGapDeg,""",
    'return digit reach use',
)
write(p, s)

# --- Grip workspace UI ----------------------------------------------------
p = 'src/editor/panels/GripPanel.tsx'
s = read(p)
needle = """              <dl className=\"spec-list\">
                <dt>Contact reach used</dt>
                <dd>{Math.round(fit.reachUse * 100)}%</dd>
                <dt>Wrap coverage</dt>
                <dd>{fit.wrapCoverageDeg.toFixed(1)}°</dd>
                <dt>Largest open gap</dt>
                <dd>{fit.widestGapDeg.toFixed(1)}°</dd>
              </dl>"""
replacement = needle + r'''
              <h4>Digit reach</h4>
              <dl className="spec-list">
                {FINGERS.map((finger) => {
                  const reach = fit.digitReachUse[finger];
                  return (
                    <div key={`digit-reach-${finger}`} className="spec-list__pair">
                      <dt>{finger.charAt(0).toUpperCase() + finger.slice(1)}</dt>
                      <dd className={reach >= 1 ? 'status-warn' : undefined}>
                        {Math.round(reach * 100)}%
                      </dd>
                    </div>
                  );
                })}
              </dl>'''
s = replace_once(s, needle, replacement, 'render per digit reach')
s = replace_once(
    s,
    """        Grip X/Y/Z is the handle centre in hand-local millimetres; orientation is a hand-local Euler calibration in degrees. “Within envelope” uses the same
        finger reach and wrap geometry as the Studio's grip regression. It is an animation-fit diagnostic,
        not a force or injury-safety score.""",
    """        Grip X/Y/Z is the handle centre in hand-local millimetres; orientation is a hand-local Euler calibration in degrees. “Within envelope” and each digit percentage use the same
        contact-reach and wrap geometry as the Studio's grip regression. A digit above 100% has exceeded that authored geometric envelope; this is not a literal mesh-penetration, force or injury-safety score.""",
    'diagnostic caveat wording',
)
write(p, s)

# --- tests ----------------------------------------------------------------
p = 'src/equipment/gripDiagnostics.test.ts'
s = read(p)
s = replace_once(
    s,
    "import { GRIP_CLOSURE_PRESETS, measureGripFit } from './gripDiagnostics';",
    "import { GRIP_CLOSURE_PRESETS, measureGripFit } from './gripDiagnostics';\nimport { FINGERS } from '../rig/boneNames';",
    'test fingers import',
)
needle = """        expect(fit.withinEnvelope, `${side} at ${time.toFixed(2)}s`).toBe(true);
        expect(fit.reachUse).toBeLessThan(1);
        expect(fit.wrapCoverageDeg).toBeGreaterThan(190);"""
replacement = """        expect(fit.withinEnvelope, `${side} at ${time.toFixed(2)}s`).toBe(true);
        expect(fit.reachUse).toBeLessThan(1);
        expect(fit.wrapCoverageDeg).toBeGreaterThan(190);
        expect(Object.keys(fit.digitReachUse).sort()).toEqual([...FINGERS].sort());
        for (const finger of FINGERS) {
          expect(fit.digitReachUse[finger]).toBeGreaterThanOrEqual(0);
          expect(fit.digitReachUse[finger]).toBeLessThan(1);
        }
        expect(fit.reachUse).toBeCloseTo(Math.max(...Object.values(fit.digitReachUse)), 10);"""
s = replace_once(s, needle, replacement, 'digit reach test assertions')

insert = r'''

  it('identifies the digit carrying the largest reach value', () => {
    const exercise = structuredClone(bicepCurl);
    exercise.hands.digitClosure = { pinky: 0.35 };
    const clip = generateClip(skeleton, exercise);
    const evaluation = new PoseEvaluation(skeleton);
    const frame = resolveFrame(skeleton, evaluation, clip, 0);
    evaluation.apply(frame.pose);
    const equipment = frame.equipment.get('dumbbell_l');
    expect(equipment).toBeDefined();
    const fit = measureGripFit(evaluation, equipment!, 'l');
    const largest = FINGERS.reduce((best, finger) =>
      fit.digitReachUse[finger] > fit.digitReachUse[best] ? finger : best,
    );
    expect(fit.reachUse).toBeCloseTo(fit.digitReachUse[largest], 10);
    expect(fit.digitReachUse.pinky).not.toBeCloseTo(fit.digitReachUse.index, 6);
  });
'''
s = replace_once(s, '\n});', insert + '\n});', 'digit diagnosis test')
write(p, s)

# --- docs / changelog ------------------------------------------------------
p = 'docs/STUDIO_CAPABILITY_ROADMAP.md'
s = read(p)
needle = '- Per-digit closure trims can independently adjust thumb/index/middle/ring/pinky on top of the active grip profile while unspecified digits continue to follow global closure. Defaults are absent, so accepted grips remain byte-for-byte generator-compatible until an author opts in.'
s = replace_once(
    s,
    needle,
    needle + '\n- Grip diagnostics now report the established contact-reach envelope per digit as well as globally, so thumb/pinky/index/middle/ring problems can be localized before using per-digit closure trims. Values above 100% mean the authored geometric reach envelope is exceeded; they are not claimed as literal mesh penetration or force.',
    'roadmap digit reach diagnostics',
)
write(p, s)

p = 'AI_CHANGELOG.md'
s = read(p)
entry = '''### ChatGPT — 2026-09-14 — per-digit grip reach diagnostics\n\nExtended the existing geometric grip diagnostic so every contact point is tagged with its owning digit and `GripFitMeasurement` now reports `digitReachUse` for thumb/index/middle/ring/pinky alongside the established overall `reachUse`. Each digit value is the maximum distance-to-handle-centre-line divided by that contact point's existing allowed reach. Overall `reachUse` remains exactly the maximum of those five digit values, so the established envelope and Review gate semantics do not change.\n\nThe Grip workspace now lists live per-digit percentages below each single-hand handle fit. Values at or above 100% are visually flagged and the UI explicitly says this means the authored **geometric contact-reach envelope** has been exceeded; it is not presented as literal mesh penetration, force, or injury risk. This pairs directly with the new per-digit closure sliders: an author can see which digit is the outlier and trim only that digit instead of translating the whole dumbbell or changing unrelated fingers. Regression coverage proves all five digit metrics exist throughout the retained curl/shoulder-press reps, remain inside the current accepted envelope, and that global reach is exactly the maximum digit reach.\n\n'''
s = replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n' + entry, 'digit diagnostics changelog')
write(p, s)

print('Applied per-digit grip reach diagnostics')
