from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing anchor in {path}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1))

# Extend motion diagnostics with finite-difference velocity continuity at each
# interior keyframe. This localises phase-boundary snaps without imposing a
# generic pass/fail threshold.
p = Path("src/editor/motionDiagnostics.ts")
text = p.read_text()
text = text.replace(
    "import { sampleClip, type StudioClip } from '../animation/clip';",
    "import { sampleClip, sortedKeyframes, type StudioClip } from '../animation/clip';",
    1,
)
addition = r'''

export interface JointTransitionPoint {
  keyframeId: string;
  time: number;
  label?: string;
  axis: Axis;
  incomingDegPerSec: number;
  outgoingDegPerSec: number;
  velocityJumpDegPerSec: number;
}

export interface JointTransitionDiagnostic {
  bone: BoneName;
  fps: number;
  points: JointTransitionPoint[];
  maxJump: JointTransitionPoint | null;
}

/**
 * Measure angular-velocity continuity immediately before and after each
 * interior keyframe for one joint.
 *
 * This complements whole-rep acceleration: it answers whether the sharpest
 * change is specifically attached to a phase/keyframe boundary. A deliberate
 * stop into a hold can legitimately have a large change, so no universal
 * failure threshold is assigned.
 */
export function measureJointTransitions(
  clip: StudioClip,
  bone: BoneName,
): JointTransitionDiagnostic {
  const fps = clip.fps > 0 ? clip.fps : 30;
  const step = 1 / fps;
  const frames = sortedKeyframes(clip);
  const points: JointTransitionPoint[] = [];
  let maxJump: JointTransitionPoint | null = null;

  for (let index = 1; index < frames.length - 1; index += 1) {
    const frame = frames[index];
    const beforeTime = Math.max(frames[index - 1].time, frame.time - step);
    const afterTime = Math.min(frames[index + 1].time, frame.time + step);
    const inDt = frame.time - beforeTime;
    const outDt = afterTime - frame.time;
    if (inDt <= 1e-10 || outDt <= 1e-10) continue;

    const before = boneRotation(sampleClip(clip, beforeTime).pose, bone);
    const at = boneRotation(sampleClip(clip, frame.time).pose, bone);
    const after = boneRotation(sampleClip(clip, afterTime).pose, bone);

    let boundary: JointTransitionPoint | null = null;
    for (const axis of AXES) {
      const incoming = toDeg(shortestAngleDelta(before[axis], at[axis])) / inDt;
      const outgoing = toDeg(shortestAngleDelta(at[axis], after[axis])) / outDt;
      const jump = Math.abs(outgoing - incoming);
      if (!boundary || jump > boundary.velocityJumpDegPerSec) {
        boundary = {
          keyframeId: frame.id,
          time: frame.time,
          ...(frame.label ? { label: frame.label } : {}),
          axis,
          incomingDegPerSec: incoming,
          outgoingDegPerSec: outgoing,
          velocityJumpDegPerSec: jump,
        };
      }
    }
    if (!boundary) continue;
    points.push(boundary);
    if (!maxJump || boundary.velocityJumpDegPerSec > maxJump.velocityJumpDegPerSec) {
      maxJump = boundary;
    }
  }

  return { bone, fps, points, maxJump };
}
'''
text += addition
p.write_text(text)

# Regression: same-slope transition stays continuous, deliberate stop is
# localised at the exact middle keyframe.
p = Path("src/editor/motionDiagnostics.test.ts")
text = p.read_text()
text = text.replace(
    "import { measureJointMotion } from './motionDiagnostics';",
    "import { measureJointMotion, measureJointTransitions } from './motionDiagnostics';",
    1,
)
addition = r'''

  it('localises a velocity discontinuity to the keyframe where a moving joint stops', () => {
    const clip = linearForearmClip();
    const middle = restPose();
    middle.rotations.forearm_l = vec3(Math.PI / 4, 0, 0);
    const end = restPose();
    end.rotations.forearm_l = vec3(Math.PI / 4, 0, 0);
    clip.keyframes = [
      { id: 'start', time: 0, pose: restPose(), ik: {}, easing: 'linear' },
      { id: 'stop', time: 0.5, pose: middle, ik: {}, easing: 'linear', label: 'Stop here' },
      { id: 'end', time: 1, pose: end, ik: {}, easing: 'hold' },
    ];

    const diagnostic = measureJointTransitions(clip, 'forearm_l');
    expect(diagnostic.points).toHaveLength(1);
    expect(diagnostic.maxJump?.keyframeId).toBe('stop');
    expect(diagnostic.maxJump?.time).toBeCloseTo(0.5, 8);
    expect(diagnostic.maxJump?.axis).toBe('x');
    expect(diagnostic.maxJump?.incomingDegPerSec).toBeCloseTo(90, 6);
    expect(diagnostic.maxJump?.outgoingDegPerSec).toBeCloseTo(0, 6);
    expect(diagnostic.maxJump?.velocityJumpDegPerSec).toBeCloseTo(90, 6);
  });

  it('reports near-zero boundary jump when both segments keep the same linear velocity', () => {
    const clip = linearForearmClip();
    const middle = restPose();
    middle.rotations.forearm_l = vec3(Math.PI / 4, 0, 0);
    clip.keyframes = [
      { id: 'start', time: 0, pose: restPose(), ik: {}, easing: 'linear' },
      { id: 'middle', time: 0.5, pose: middle, ik: {}, easing: 'linear' },
      clip.keyframes[1],
    ];
    const diagnostic = measureJointTransitions(clip, 'forearm_l');
    expect(diagnostic.maxJump?.velocityJumpDegPerSec ?? 0).toBeLessThan(1e-8);
  });
'''
pos = text.rfind("\n});")
if pos < 0:
    raise SystemExit("missing motion diagnostics suite end")
text = text[:pos] + addition + text[pos:]
p.write_text(text)

# Joint workspace: surface worst transition beside speed/acceleration and jump
# directly to it for Focus-selected inspection.
p = Path("src/editor/panels/JointPanel.tsx")
text = p.read_text()
text = text.replace(
    "import { measureJointMotion } from '../motionDiagnostics';",
    "import { measureJointMotion, measureJointTransitions } from '../motionDiagnostics';",
    1,
)
text = text.replace(
    "  const motion = useMemo(\n    () => (selected ? measureJointMotion(clip, selected) : null),\n    [clip, selected],\n  );",
    "  const motion = useMemo(\n    () => (selected ? measureJointMotion(clip, selected) : null),\n    [clip, selected],\n  );\n  const transitions = useMemo(\n    () => (selected ? measureJointTransitions(clip, selected) : null),\n    [clip, selected],\n  );",
    1,
)
old = """            <dt>Highest angular acceleration</dt>\n            <dd>\n              {motion.maxAcceleration.value.toFixed(0)}°/s² · {motion.maxAcceleration.axis.toUpperCase()} · {motion.maxAcceleration.time.toFixed(2)}s\n            </dd>\n          </dl>\n          <div className=\"button-row\">\n            <button type=\"button\" onClick={() => setTime(motion.maxSpeed.time)}>\n              Jump to fastest frame\n            </button>\n            <button type=\"button\" onClick={() => setTime(motion.maxAcceleration.time)}>\n              Jump to sharpest change\n            </button>\n          </div>\n"""
new = """            <dt>Highest angular acceleration</dt>\n            <dd>\n              {motion.maxAcceleration.value.toFixed(0)}°/s² · {motion.maxAcceleration.axis.toUpperCase()} · {motion.maxAcceleration.time.toFixed(2)}s\n            </dd>\n            <dt>Largest keyframe velocity jump</dt>\n            <dd>\n              {transitions?.maxJump\n                ? `${transitions.maxJump.velocityJumpDegPerSec.toFixed(1)}°/s · ${transitions.maxJump.axis.toUpperCase()} · ${transitions.maxJump.time.toFixed(2)}s${transitions.maxJump.label ? ` · ${transitions.maxJump.label}` : ''}`\n                : 'No interior keyframe boundary'}\n            </dd>\n          </dl>\n          <div className=\"button-row\">\n            <button type=\"button\" onClick={() => setTime(motion.maxSpeed.time)}>\n              Jump to fastest frame\n            </button>\n            <button type=\"button\" onClick={() => setTime(motion.maxAcceleration.time)}>\n              Jump to sharpest change\n            </button>\n            {transitions?.maxJump && (\n              <button type=\"button\" onClick={() => setTime(transitions.maxJump!.time)}>\n                Jump to worst keyframe transition\n              </button>\n            )}\n          </div>\n          {transitions?.maxJump && (\n            <p className=\"panel__note\">\n              At that boundary: incoming {transitions.maxJump.incomingDegPerSec.toFixed(1)}°/s, outgoing {transitions.maxJump.outgoingDegPerSec.toFixed(1)}°/s. A stop into a hold can be intentional; use this to locate the transition, not as an automatic failure.\n            </p>\n          )}\n"""
if old not in text:
    raise SystemExit("missing JointPanel motion block anchor")
text = text.replace(old, new, 1)
p.write_text(text)

replace(
    "docs/STUDIO_CAPABILITY_ROADMAP.md",
    "- Selected-joint frame-by-frame motion diagnostics report worst angular speed and acceleration with exact timestamps and jump-to-frame controls, giving elbow/shoulder timing review an objective signal without imposing a universal movement threshold.",
    "- Selected-joint frame-by-frame motion diagnostics report worst angular speed and acceleration with exact timestamps and jump-to-frame controls, giving elbow/shoulder timing review an objective signal without imposing a universal movement threshold.\n- Keyframe transition continuity compares incoming/outgoing angular velocity around every interior keyframe, reports the largest per-axis velocity jump and exact boundary, and can jump directly there; intentional stops/holds remain descriptive rather than automatically failed.",
)

p = Path("AI_CHANGELOG.md")
text = p.read_text()
entry = r'''
### ChatGPT — 2026-09-14 — selected-joint keyframe transition continuity

Extended selected-joint motion diagnostics with a phase-boundary continuity pass. For every interior keyframe, the Studio now samples one authored frame immediately before and after the boundary, computes shortest-path incoming/outgoing angular velocity per axis, and records the largest velocity jump. The Joint workspace shows the worst boundary, axis, timestamp and incoming/outgoing speeds with a direct jump-to-frame action.

This is intentionally descriptive rather than a universal pass/fail rule: a deliberate transition into a squeeze/hold can legitimately stop the joint. The purpose is to separate a keyframe/phase-boundary snap from a speed or acceleration peak occurring elsewhere in the movement, which is particularly useful when reviewing the curl elbow and late upper-arm contribution.

Regression coverage proves a 90°/s linear hinge stopping at a middle keyframe is localised as a 90°/s X-axis jump at exactly 0.5 s, while two adjacent linear segments with the same velocity report essentially zero boundary discontinuity.

'''
marker = "## Unreleased\n\n"
if marker not in text:
    raise SystemExit("missing changelog marker")
text = text.replace(marker, marker + entry, 1)
p.write_text(text)

print("Applied selected-joint transition continuity diagnostics")
