from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing anchor in {path}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1))

# Spatial path of a selected joint relative to its anatomical parent. For a
# forearm selection this is the elbow relative to the shoulder, so whole-body
# translation cannot masquerade as elbow drift.
p = Path("src/editor/motionDiagnostics.ts")
text = p.read_text()
text = text.replace(
    "import type { Skeleton } from '../rig/skeleton';",
    "import { PoseEvaluation, type Skeleton } from '../rig/skeleton';",
    1,
)
addition = r'''

export interface JointPathDiagnostic {
  bone: BoneName;
  parent: BoneName;
  fps: number;
  sampleCount: number;
  /** Largest 3D movement of the joint-from-parent vector away from its start. */
  maxDriftMetres: number;
  maxDriftTime: number;
  /** Distance travelled by that relative joint point through the whole clip. */
  pathLengthMetres: number;
  /** Difference between final and starting relative joint positions. */
  returnErrorMetres: number;
}

/**
 * Measure the selected joint head relative to its anatomical parent joint.
 *
 * World/root translation is deliberately removed. Selecting a forearm therefore
 * measures how far the elbow wanders relative to the shoulder, while pure elbow
 * flexion leaves the elbow joint itself stationary. The metric is descriptive:
 * many exercises intentionally move a joint through space.
 */
export function measureJointPath(
  clip: StudioClip,
  skeleton: Skeleton,
  bone: BoneName,
): JointPathDiagnostic | null {
  const parent = skeleton.bone(bone).parent;
  if (!parent) return null;
  const fps = clip.fps > 0 ? clip.fps : 30;
  const lastFrame = Math.max(1, Math.ceil(clip.duration * fps));
  const evaluation = new PoseEvaluation(skeleton);
  const joint = new Vector3();
  const anchor = new Vector3();
  const relative = new Vector3();
  const start = new Vector3();
  const previous = new Vector3();
  let sampleCount = 0;
  let maxDriftMetres = 0;
  let maxDriftTime = 0;
  let pathLengthMetres = 0;

  for (let frame = 0; frame <= lastFrame; frame += 1) {
    const time = Math.min(clip.duration, frame / fps);
    evaluation.apply(sampleClip(clip, time).pose);
    evaluation.head(bone, joint);
    evaluation.head(parent, anchor);
    relative.subVectors(joint, anchor);
    if (sampleCount === 0) {
      start.copy(relative);
      previous.copy(relative);
    } else {
      pathLengthMetres += relative.distanceTo(previous);
      previous.copy(relative);
    }
    const drift = relative.distanceTo(start);
    if (drift > maxDriftMetres) {
      maxDriftMetres = drift;
      maxDriftTime = time;
    }
    sampleCount += 1;
  }

  return {
    bone,
    parent,
    fps,
    sampleCount,
    maxDriftMetres,
    maxDriftTime,
    pathLengthMetres,
    returnErrorMetres: relative.distanceTo(start),
  };
}
'''
# We need Vector3 in this diagnostics module.
text = "import { Vector3 } from 'three';\n" + text + addition
p.write_text(text)

# Regression: forearm flexion does not move the elbow joint; upper-arm motion
# does, and a symmetric out-and-back returns it exactly to start.
p = Path("src/editor/motionDiagnostics.test.ts")
text = p.read_text()
text = text.replace(
    "  measureJointMotion,\n  measureJointTransitions,",
    "  measureJointMotion,\n  measureJointPath,\n  measureJointTransitions,",
    1,
)
addition = r'''

  it('measures elbow drift from upper-arm motion rather than from elbow flexion itself', () => {
    const flexionOnly = linearForearmClip();
    const fixedElbow = measureJointPath(flexionOnly, canonicalSkeleton, 'forearm_l');
    expect(fixedElbow).not.toBeNull();
    expect(fixedElbow!.parent).toBe('upperarm_l');
    expect(fixedElbow!.maxDriftMetres).toBeLessThan(1e-9);
    expect(fixedElbow!.pathLengthMetres).toBeLessThan(1e-9);

    const moving = linearForearmClip();
    const middle = restPose();
    middle.rotations.upperarm_l = vec3((10 * Math.PI) / 180, 0, 0);
    const end = restPose();
    moving.keyframes = [
      { id: 'start', time: 0, pose: restPose(), ik: {}, easing: 'linear' },
      { id: 'middle', time: 0.5, pose: middle, ik: {}, easing: 'linear' },
      { id: 'end', time: 1, pose: end, ik: {}, easing: 'hold' },
    ];
    const path = measureJointPath(moving, canonicalSkeleton, 'forearm_l');
    expect(path).not.toBeNull();
    expect(path!.maxDriftMetres).toBeGreaterThan(0.02);
    expect(path!.maxDriftTime).toBeCloseTo(0.5, 6);
    expect(path!.pathLengthMetres).toBeGreaterThan(path!.maxDriftMetres * 1.9);
    expect(path!.returnErrorMetres).toBeLessThan(1e-9);
  });
'''
pos = text.rfind("\n});")
if pos < 0:
    raise SystemExit("missing motion diagnostics suite end")
text = text[:pos] + addition + text[pos:]
p.write_text(text)

# Joint panel readout.
p = Path("src/editor/panels/JointPanel.tsx")
text = p.read_text()
text = text.replace(
    "  measureJointMotion,\n  measureJointTransitions,",
    "  measureJointMotion,\n  measureJointPath,\n  measureJointTransitions,",
    1,
)
text = text.replace(
    "  const bilateral = useMemo(\n    () => (selected ? measureBilateralMotionSymmetry(clip, skeleton, selected) : null),\n    [clip, selected],\n  );",
    "  const bilateral = useMemo(\n    () => (selected ? measureBilateralMotionSymmetry(clip, skeleton, selected) : null),\n    [clip, selected],\n  );\n  const jointPath = useMemo(\n    () => (selected ? measureJointPath(clip, skeleton, selected) : null),\n    [clip, selected],\n  );",
    1,
)
anchor = """            {bilateral && (\n              <>\n                <dt>Bilateral mirror mismatch</dt>\n                <dd>{bilateral.maxError.value.toFixed(2)}° max · {bilateral.rmsErrorDeg.toFixed(2)}° RMS · {bilateral.maxError.time.toFixed(2)}s</dd>\n              </>\n            )}\n          </dl>\n"""
replacement = """            {bilateral && (\n              <>\n                <dt>Bilateral mirror mismatch</dt>\n                <dd>{bilateral.maxError.value.toFixed(2)}° max · {bilateral.rmsErrorDeg.toFixed(2)}° RMS · {bilateral.maxError.time.toFixed(2)}s</dd>\n              </>\n            )}\n            {jointPath && (\n              <>\n                <dt>Joint drift from parent</dt>\n                <dd>{(jointPath.maxDriftMetres * 1000).toFixed(1)} mm max · {jointPath.maxDriftTime.toFixed(2)}s</dd>\n                <dt>Relative joint path</dt>\n                <dd>{(jointPath.pathLengthMetres * 1000).toFixed(1)} mm travelled · {(jointPath.returnErrorMetres * 1000).toFixed(1)} mm return error</dd>\n              </>\n            )}\n          </dl>\n"""
if anchor not in text:
    raise SystemExit("missing JointPanel path readout anchor")
text = text.replace(anchor, replacement, 1)
buttons = """            {bilateral && (\n              <button type=\"button\" onClick={() => setTime(bilateral.maxError.time)}>\n                Jump to worst bilateral mismatch\n              </button>\n            )}\n          </div>\n"""
buttons_replacement = """            {bilateral && (\n              <button type=\"button\" onClick={() => setTime(bilateral.maxError.time)}>\n                Jump to worst bilateral mismatch\n              </button>\n            )}\n            {jointPath && (\n              <button type=\"button\" onClick={() => setTime(jointPath.maxDriftTime)}>\n                Jump to maximum joint drift\n              </button>\n            )}\n          </div>\n"""
if buttons not in text:
    raise SystemExit("missing JointPanel path button anchor")
text = text.replace(buttons, buttons_replacement, 1)
notes = """          {bilateral && (\n            <p className=\"panel__note\">\n              Bilateral comparison uses the rig's exact mirror transform against {boneLabel(bilateral.opposite)} at every authored frame. Zero means an exact mirror; asymmetry may still be intentional for unilateral exercises.\n            </p>\n          )}\n"""
notes_replacement = notes + """          {jointPath && (\n            <p className=\"panel__note\">\n              Spatial drift is the selected joint head relative to {boneLabel(jointPath.parent)}, so whole-body/root translation is removed. Selecting a forearm measures elbow wander relative to its shoulder; pure elbow flexion alone does not move that joint point.\n            </p>\n          )}\n"""
if notes not in text:
    raise SystemExit("missing JointPanel path note anchor")
text = text.replace(notes, notes_replacement, 1)
p.write_text(text)

replace(
    "docs/STUDIO_CAPABILITY_ROADMAP.md",
    "- Whole-rep resolved bilateral motion symmetry now samples the final clip and compares the opposite joint against the canonical rig's exact mirror transform, reporting maximum and RMS angular mismatch with a jump to the worst frame; intentional unilateral asymmetry remains descriptive rather than failed.",
    "- Whole-rep resolved bilateral motion symmetry now samples the final clip and compares the opposite joint against the canonical rig's exact mirror transform, reporting maximum and RMS angular mismatch with a jump to the worst frame; intentional unilateral asymmetry remains descriptive rather than failed.\n- Selected-joint spatial path diagnostics track the joint head relative to its anatomical parent, reporting maximum drift, total relative path length, return error and the worst timestamp. For a selected forearm this directly measures elbow wander relative to the shoulder while removing whole-body/root translation.",
)

p = Path("AI_CHANGELOG.md")
text = p.read_text()
entry = r'''
### ChatGPT — 2026-09-14 — selected-joint spatial path diagnostics

Added a whole-rep spatial path diagnostic for the selected joint. It evaluates the canonical forward kinematics at the authored clip FPS, measures the selected bone head relative to its anatomical parent's head, and reports maximum 3D drift from the starting relative position, total relative path length, final return error and the exact worst timestamp. Root/world translation is removed by construction.

This is especially useful for the bicep-curl review: selecting `forearm_l` or `forearm_r` means the measured point is the elbow joint and the parent anchor is the upper-arm/shoulder joint. Pure elbow flexion therefore reads zero elbow drift, while upper-arm/shoulder contribution moves the elbow and becomes directly measurable in millimetres. The Joint workspace can jump straight to the maximum-drift frame. Values remain descriptive because many exercises intentionally translate joints.

Regression coverage proves a 90° forearm-flexion clip leaves the elbow point fixed, then adds a 10° upper-arm out-and-back path and verifies substantial measured drift, a midpoint worst frame, non-zero travelled path and essentially zero return error.

'''
marker = "## Unreleased\n\n"
if marker not in text:
    raise SystemExit("missing changelog marker")
text = text.replace(marker, marker + entry, 1)
p.write_text(text)

print("Applied selected-joint spatial path diagnostics")
