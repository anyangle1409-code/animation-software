from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing anchor in {path}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1))

# Resolved bilateral symmetry uses the rig's own mirror transform, not raw sign
# guesses, and compares every authored frame.
p = Path("src/editor/motionDiagnostics.ts")
text = p.read_text()
text = text.replace(
    "import type { BoneName } from '../rig/boneNames';",
    "import { mirrorBoneName, type BoneName } from '../rig/boneNames';",
    1,
)
text = text.replace(
    "import { boneRotation } from '../rig/pose';",
    "import { boneRotation, mirrorPose } from '../rig/pose';\nimport type { Skeleton } from '../rig/skeleton';",
    1,
)
addition = r'''

export interface BilateralMotionSymmetryDiagnostic {
  bone: BoneName;
  opposite: BoneName;
  fps: number;
  sampleCount: number;
  rmsErrorDeg: number;
  maxError: MotionWorstPoint;
}

/**
 * Compare the sampled opposite-side joint against the exact pose produced by
 * the canonical rig's mirror transform.
 *
 * Flexion, axial rotation and ab/adduction therefore use the same handedness
 * rules as editor mirroring. Zero means a perfect bilateral mirror; non-zero is
 * descriptive because some exercises intentionally move asymmetrically.
 */
export function measureBilateralMotionSymmetry(
  clip: StudioClip,
  skeleton: Skeleton,
  bone: BoneName,
): BilateralMotionSymmetryDiagnostic | null {
  const opposite = mirrorBoneName(bone);
  if (opposite === bone) return null;
  const fps = clip.fps > 0 ? clip.fps : 30;
  const lastFrame = Math.max(1, Math.ceil(clip.duration * fps));
  let sampleCount = 0;
  let squared = 0;
  let components = 0;
  let maxError: MotionWorstPoint = { axis: 'x', value: 0, time: 0 };

  for (let frame = 0; frame <= lastFrame; frame += 1) {
    const time = Math.min(clip.duration, frame / fps);
    const pose = sampleClip(clip, time).pose;
    const mirrored = mirrorPose(skeleton, pose);
    const actual = boneRotation(pose, opposite);
    const expected = boneRotation(mirrored, opposite);
    for (const axis of AXES) {
      const error = Math.abs(toDeg(shortestAngleDelta(expected[axis], actual[axis])));
      squared += error * error;
      components += 1;
      if (error > maxError.value) maxError = { axis, value: error, time };
    }
    sampleCount += 1;
  }

  return {
    bone,
    opposite,
    fps,
    sampleCount,
    rmsErrorDeg: components > 0 ? Math.sqrt(squared / components) : 0,
    maxError,
  };
}
'''
text += addition
p.write_text(text)

# Regression proves exact mirrored motion is zero and a one-sided 10-degree
# endpoint change is detected at the final frame.
p = Path("src/editor/motionDiagnostics.test.ts")
text = p.read_text()
text = text.replace(
    "import { restPose } from '../rig/pose';",
    "import { restPose } from '../rig/pose';\nimport { canonicalSkeleton } from '../rig/skeleton';",
    1,
)
text = text.replace(
    "import { measureJointMotion, measureJointTransitions } from './motionDiagnostics';",
    "import {\n  measureBilateralMotionSymmetry,\n  measureJointMotion,\n  measureJointTransitions,\n} from './motionDiagnostics';",
    1,
)
addition = r'''

  it('measures resolved left/right motion against the rig mirror transform', () => {
    const clip = linearForearmClip();
    clip.keyframes[0].pose.rotations.forearm_l = vec3(0, (30 * Math.PI) / 180, (5 * Math.PI) / 180);
    clip.keyframes[0].pose.rotations.forearm_r = vec3(0, (-30 * Math.PI) / 180, (-5 * Math.PI) / 180);
    clip.keyframes[1].pose.rotations.forearm_l = vec3(Math.PI / 2, (40 * Math.PI) / 180, 0);
    clip.keyframes[1].pose.rotations.forearm_r = vec3(Math.PI / 2, (-40 * Math.PI) / 180, 0);

    const symmetric = measureBilateralMotionSymmetry(clip, canonicalSkeleton, 'forearm_l');
    expect(symmetric).not.toBeNull();
    expect(symmetric!.opposite).toBe('forearm_r');
    expect(symmetric!.maxError.value).toBeLessThan(1e-8);
    expect(symmetric!.rmsErrorDeg).toBeLessThan(1e-8);

    clip.keyframes[1].pose.rotations.forearm_r = vec3((80 * Math.PI) / 180, (-40 * Math.PI) / 180, 0);
    const asymmetric = measureBilateralMotionSymmetry(clip, canonicalSkeleton, 'forearm_l');
    expect(asymmetric?.maxError.axis).toBe('x');
    expect(asymmetric?.maxError.value).toBeCloseTo(10, 6);
    expect(asymmetric?.maxError.time).toBeCloseTo(1, 8);
  });
'''
pos = text.rfind("\n});")
if pos < 0:
    raise SystemExit("missing motion diagnostics suite end")
text = text[:pos] + addition + text[pos:]
p.write_text(text)

# Joint workspace surfaces final sampled symmetry beside speed/transition data.
p = Path("src/editor/panels/JointPanel.tsx")
text = p.read_text()
text = text.replace(
    "import { measureJointMotion, measureJointTransitions } from '../motionDiagnostics';",
    "import {\n  measureBilateralMotionSymmetry,\n  measureJointMotion,\n  measureJointTransitions,\n} from '../motionDiagnostics';",
    1,
)
text = text.replace(
    "  const transitions = useMemo(\n    () => (selected ? measureJointTransitions(clip, selected) : null),\n    [clip, selected],\n  );",
    "  const transitions = useMemo(\n    () => (selected ? measureJointTransitions(clip, selected) : null),\n    [clip, selected],\n  );\n  const bilateral = useMemo(\n    () => (selected ? measureBilateralMotionSymmetry(clip, skeleton, selected) : null),\n    [clip, selected],\n  );",
    1,
)
old = """            <dt>Largest keyframe velocity jump</dt>\n            <dd>\n              {transitions?.maxJump\n                ? `${transitions.maxJump.velocityJumpDegPerSec.toFixed(1)}°/s · ${transitions.maxJump.axis.toUpperCase()} · ${transitions.maxJump.time.toFixed(2)}s${transitions.maxJump.label ? ` · ${transitions.maxJump.label}` : ''}`\n                : 'No interior keyframe boundary'}\n            </dd>\n          </dl>\n"""
new = """            <dt>Largest keyframe velocity jump</dt>\n            <dd>\n              {transitions?.maxJump\n                ? `${transitions.maxJump.velocityJumpDegPerSec.toFixed(1)}°/s · ${transitions.maxJump.axis.toUpperCase()} · ${transitions.maxJump.time.toFixed(2)}s${transitions.maxJump.label ? ` · ${transitions.maxJump.label}` : ''}`\n                : 'No interior keyframe boundary'}\n            </dd>\n            {bilateral && (\n              <>\n                <dt>Bilateral mirror mismatch</dt>\n                <dd>{bilateral.maxError.value.toFixed(2)}° max · {bilateral.rmsErrorDeg.toFixed(2)}° RMS · {bilateral.maxError.time.toFixed(2)}s</dd>\n              </>\n            )}\n          </dl>\n"""
if old not in text:
    raise SystemExit("missing JointPanel bilateral insertion anchor")
text = text.replace(old, new, 1)
old_buttons = """            {transitions?.maxJump && (\n              <button type=\"button\" onClick={() => setTime(transitions.maxJump!.time)}>\n                Jump to worst keyframe transition\n              </button>\n            )}\n          </div>\n"""
new_buttons = """            {transitions?.maxJump && (\n              <button type=\"button\" onClick={() => setTime(transitions.maxJump!.time)}>\n                Jump to worst keyframe transition\n              </button>\n            )}\n            {bilateral && (\n              <button type=\"button\" onClick={() => setTime(bilateral.maxError.time)}>\n                Jump to worst bilateral mismatch\n              </button>\n            )}\n          </div>\n"""
if old_buttons not in text:
    raise SystemExit("missing JointPanel motion button anchor")
text = text.replace(old_buttons, new_buttons, 1)
old_note = """          {transitions?.maxJump && (\n            <p className=\"panel__note\">\n              At that boundary: incoming {transitions.maxJump.incomingDegPerSec.toFixed(1)}°/s, outgoing {transitions.maxJump.outgoingDegPerSec.toFixed(1)}°/s. A stop into a hold can be intentional; use this to locate the transition, not as an automatic failure.\n            </p>\n          )}\n"""
new_note = old_note + """          {bilateral && (\n            <p className=\"panel__note\">\n              Bilateral comparison uses the rig's exact mirror transform against {boneLabel(bilateral.opposite)} at every authored frame. Zero means an exact mirror; asymmetry may still be intentional for unilateral exercises.\n            </p>\n          )}\n"""
if old_note not in text:
    raise SystemExit("missing JointPanel transition note anchor")
text = text.replace(old_note, new_note, 1)
p.write_text(text)

replace(
    "docs/STUDIO_CAPABILITY_ROADMAP.md",
    "- Bilateral timing symmetry is explicit: the Joint workspace compares delay/finish/easing against the anatomical opposite and can copy selected-side timing to the other side in one undoable edit without changing pose angles.",
    "- Bilateral timing symmetry is explicit: the Joint workspace compares delay/finish/easing against the anatomical opposite and can copy selected-side timing to the other side in one undoable edit without changing pose angles.\n- Whole-rep resolved bilateral motion symmetry now samples the final clip and compares the opposite joint against the canonical rig's exact mirror transform, reporting maximum and RMS angular mismatch with a jump to the worst frame; intentional unilateral asymmetry remains descriptive rather than failed.",
)

p = Path("AI_CHANGELOG.md")
text = p.read_text()
entry = r'''
### ChatGPT — 2026-09-14 — resolved bilateral motion symmetry

Added a whole-rep bilateral motion diagnostic for paired joints. Rather than comparing raw left/right Euler values, it samples the final clip and mirrors each sampled pose through the canonical rig's existing `mirrorPose()` transform, which preserves flexion and flips the handed axial/abduction axes exactly as editor mirroring does. The actual opposite-side joint is then compared against that mirrored expectation using shortest-path angular deltas.

The Joint workspace now reports maximum and RMS mirror mismatch with the exact worst timestamp and a jump-to-frame action. This measures the resolved animation after timing/easing rather than merely checking that stored timing settings match. It remains descriptive because unilateral exercises may intentionally be asymmetric; for bilateral curls it provides a direct check that both arms actually follow the same mirrored path.

Regression coverage proves a synthetic forearm path containing flexion plus handed Y/Z rotation reads essentially zero error when correctly mirrored, then detects an intentional 10° one-sided flexion change on the X axis at the final frame.

'''
marker = "## Unreleased\n\n"
if marker not in text:
    raise SystemExit("missing changelog marker")
text = text.replace(marker, marker + entry, 1)
p.write_text(text)

print("Applied resolved bilateral motion symmetry diagnostics")
