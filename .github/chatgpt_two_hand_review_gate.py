from pathlib import Path


def read(path):
    return Path(path).read_text()


def write(path, text):
    Path(path).write_text(text)


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)


# --- automated review gate -------------------------------------------------
p = 'src/editor/review.ts'
s = read(p)
s = replace_once(
    s,
    "import { measureGripFit } from '../equipment/gripDiagnostics';",
    "import { measureGripFit, measureTwoHandFit } from '../equipment/gripDiagnostics';",
    'review diagnostic import',
)
s = replace_once(
    s,
    "  id: 'technique' | 'loop' | 'ik' | 'contacts' | 'grip';",
    "  id: 'technique' | 'loop' | 'ik' | 'contacts' | 'grip' | 'twoHandGrip';",
    'review gate id',
)
s = replace_once(
    s,
    """  let widestGripGap = 0;

  const supportedGripInstances = clip.equipment.filter(""",
    """  let widestGripGap = 0;
  let twoHandFailures = 0;
  let twoHandChecks = 0;
  let worstTwoHandError = 0;
  let worstTwoHandSpacingError = 0;

  const supportedGripInstances = clip.equipment.filter(""",
    'review two hand counters',
)
s = replace_once(
    s,
    """  const supportedGripInstances = clip.equipment.filter(
    (instance) => instance.kind === 'dumbbell' && instance.attachment.mode === 'hand',
  );

  for (let index = 0; index <= frames; index += 1) {""",
    """  const supportedGripInstances = clip.equipment.filter(
    (instance) => instance.kind === 'dumbbell' && instance.attachment.mode === 'hand',
  );
  const twoHandInstances = clip.equipment.filter(
    (instance) => instance.attachment.mode === 'hands',
  );

  for (let index = 0; index <= frames; index += 1) {""",
    'review two hand instances',
)
old = """    if (supportedGripInstances.length > 0) {
      const gripEvaluation = new PoseEvaluation(rig);
      const frame = resolveFrame(rig, gripEvaluation, clip, time, { anchors });
      gripEvaluation.apply(frame.pose);
      for (const instance of supportedGripInstances) {
        if (instance.attachment.mode !== 'hand') continue;
        const equipment = frame.equipment.get(instance.id);
        if (!equipment) {
          gripFailures += 1;
          continue;
        }
        const fit = measureGripFit(gripEvaluation, equipment, instance.attachment.side);
        gripChecks += 1;
        worstReachUse = Math.max(worstReachUse, fit.reachUse);
        widestGripGap = Math.max(widestGripGap, fit.widestGapDeg);
        if (!fit.withinEnvelope) gripFailures += 1;
      }
    }
"""
new = """    if (supportedGripInstances.length > 0 || twoHandInstances.length > 0) {
      const gripEvaluation = new PoseEvaluation(rig);
      const frame = resolveFrame(rig, gripEvaluation, clip, time, { anchors });
      gripEvaluation.apply(frame.pose);
      for (const instance of supportedGripInstances) {
        if (instance.attachment.mode !== 'hand') continue;
        const equipment = frame.equipment.get(instance.id);
        if (!equipment) {
          gripFailures += 1;
          continue;
        }
        const fit = measureGripFit(gripEvaluation, equipment, instance.attachment.side);
        gripChecks += 1;
        worstReachUse = Math.max(worstReachUse, fit.reachUse);
        widestGripGap = Math.max(widestGripGap, fit.widestGapDeg);
        if (!fit.withinEnvelope) gripFailures += 1;
      }
      for (const instance of twoHandInstances) {
        if (instance.attachment.mode !== 'hands') continue;
        const equipment = frame.equipment.get(instance.id);
        if (!equipment) {
          twoHandFailures += 1;
          continue;
        }
        const fit = measureTwoHandFit(gripEvaluation, instance, equipment);
        if (!fit) {
          twoHandFailures += 1;
          continue;
        }
        twoHandChecks += 1;
        worstTwoHandError = Math.max(worstTwoHandError, fit.leftError, fit.rightError);
        worstTwoHandSpacingError = Math.max(worstTwoHandSpacingError, Math.abs(fit.separationError));
        if (!fit.withinEnvelope) twoHandFailures += 1;
      }
    }
"""
s = replace_once(s, old, new, 'review shared grip frame')
needle = """    {
      id: 'grip',
      label: 'Dumbbell grip envelope',
      passed: gripFailures === 0,
      detail: supportedGripInstances.length === 0
        ? 'Not applicable: no supported single-hand dumbbell grip.'
        : gripFailures === 0
          ? `${gripChecks} grip samples pass; max reach ${Math.round(worstReachUse * 100)}%, widest gap ${widestGripGap.toFixed(1)}°.`
          : `${gripFailures} of ${gripChecks} grip samples need review.`,
      applicable: supportedGripInstances.length > 0,
    },
"""
replacement = needle + """    {
      id: 'twoHandGrip',
      label: 'Two-hand equipment fit',
      passed: twoHandFailures === 0,
      detail: twoHandInstances.length === 0
        ? 'Not applicable: no rigid two-hand equipment attachment.'
        : twoHandFailures === 0
          ? `${twoHandChecks} bilateral samples pass; worst socket error ${(worstTwoHandError * 1000).toFixed(1)} mm.`
          : `${twoHandFailures} sampled bilateral fits exceed the 5 mm envelope; worst socket error ${(worstTwoHandError * 1000).toFixed(1)} mm, spacing mismatch ${(worstTwoHandSpacingError * 1000).toFixed(1)} mm.`,
      applicable: twoHandInstances.length > 0,
    },
"""
s = replace_once(s, needle, replacement, 'two hand review gate')
write(p, s)


# --- regression tests ------------------------------------------------------
p = 'src/editor/review.test.ts'
s = read(p)
s = replace_once(
    s,
    "import { canonicalSkeleton } from '../rig/skeleton';",
    "import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';",
    'review test evaluation import',
)
s = replace_once(
    s,
    "import { generateClip } from '../animation/generate';",
    "import { generateClip } from '../animation/generate';\nimport { resolveFrame } from '../animation/pipeline';\nimport { measureTwoHandFit } from '../equipment/gripDiagnostics';\nimport { withTwoHandGripWidth } from '../equipment/library';\nimport type { EquipmentInstance } from '../equipment/types';",
    'review test two hand imports',
)
insert = r'''

  it('blocks rigid two-hand equipment until its grip sockets match the authored hands', () => {
    const exercise = clone(getExercise('dumbbell_bicep_curl'));
    const bar: EquipmentInstance = {
      id: 'review_barbell',
      kind: 'barbell',
      position: { x: 0, y: 0, z: 0 },
      rotation: { x: 0, y: 0, z: 0 },
      attachment: {
        mode: 'hands',
        leftSocket: 'grip_l',
        rightSocket: 'grip_r',
      },
      visible: true,
    };
    exercise.equipment.instances = [...exercise.equipment.instances, bar];

    const rawClip = generateClip(canonicalSkeleton, exercise);
    const rawReview = reviewExercise(canonicalSkeleton, exercise, rawClip, 3);
    const rawGate = rawReview.gates.find((gate) => gate.id === 'twoHandGrip');
    expect(rawGate?.applicable).toBe(true);
    expect(rawGate?.passed).toBe(false);
    expect(rawReview.automatedPass).toBe(false);

    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const frame = resolveFrame(canonicalSkeleton, evaluation, rawClip, 0);
    evaluation.apply(frame.pose);
    const transform = frame.equipment.get(bar.id)!;
    const targetWidth = measureTwoHandFit(evaluation, bar, transform)!.targetSeparation;
    const calibrated = withTwoHandGripWidth(bar, targetWidth);
    exercise.equipment.instances = exercise.equipment.instances.map((instance) =>
      instance.id === bar.id ? calibrated : instance,
    );

    const calibratedClip = generateClip(canonicalSkeleton, exercise);
    const calibratedReview = reviewExercise(canonicalSkeleton, exercise, calibratedClip, 3);
    const calibratedGate = calibratedReview.gates.find((gate) => gate.id === 'twoHandGrip');
    expect(calibratedGate?.passed).toBe(true);
    expect(calibratedReview.automatedPass).toBe(true);
  });
'''
s = replace_once(s, '\n});', insert + '\n});', 'two hand review regression')
write(p, s)


# --- docs / Claude handoff -------------------------------------------------
p = 'docs/STUDIO_CAPABILITY_ROADMAP.md'
s = read(p)
needle = '- Dedicated Review workspace aggregates conservative automated gates for technique errors, loop closure, IK reachability, explicit contact locks and the supported single-hand dumbbell grip envelope.'
s = replace_once(
    s,
    needle,
    '- Dedicated Review workspace aggregates conservative automated gates for technique errors, loop closure, IK reachability, explicit contact locks, the supported single-hand dumbbell grip envelope, and rigid two-hand socket alignment.',
    'roadmap review two hand gate',
)
write(p, s)

p = 'AI_CHANGELOG.md'
s = read(p)
entry = '''### ChatGPT — 2026-09-14 — two-hand equipment review gate\n\nExtended the conservative Review workspace with a separate `Two-hand equipment fit` gate. Every `attachment.mode === 'hands'` instance is now measured at the same sampled production frames used for the rest of review. The gate uses `measureTwoHandFit()` and blocks Ready-for-visual-review when either left/right grip socket exceeds the existing 5 mm bilateral envelope. Failure detail reports worst socket error and worst absolute spacing mismatch; exercises with no two-hand equipment mark this gate not applicable and remain unaffected.\n\nThe grip review loop now resolves a single production frame when either supported dumbbell or two-hand checks are needed, avoiding a second solver pass for the same sample. Regression coverage appends a synthetic rigid barbell to the retained curl only inside the test: default 80 cm sockets correctly block automated approval, then the test measures the actual hand separation, calibrates only the bar grip sockets with `withTwoHandGripWidth()`, regenerates, and proves the full review returns green. No accepted exercise definition or curl animation was changed.\n\n'''
s = replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n' + entry, 'two hand review changelog')
write(p, s)

print('Applied two-hand equipment review gate')
