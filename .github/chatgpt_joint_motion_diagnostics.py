from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text()


def write(path: str, text: str) -> None:
    Path(path).write_text(text)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)


Path('src/editor/motionDiagnostics.ts').write_text(r'''import { sampleClip, type StudioClip } from '../animation/clip';
import { AXES, type Axis } from '../rig/types';
import type { BoneName } from '../rig/boneNames';
import { boneRotation } from '../rig/pose';
import { toDeg } from '../core/math';

export interface MotionWorstPoint {
  axis: Axis;
  value: number;
  time: number;
}

export interface AxisMotionDiagnostic {
  maxSpeedDegPerSec: number;
  speedTime: number;
  maxAccelerationDegPerSec2: number;
  accelerationTime: number;
}

export interface JointMotionDiagnostic {
  bone: BoneName;
  fps: number;
  sampleCount: number;
  axes: Record<Axis, AxisMotionDiagnostic>;
  maxSpeed: MotionWorstPoint;
  maxAcceleration: MotionWorstPoint;
}

interface TimedVelocity {
  value: number;
  time: number;
}

const shortestAngleDelta = (from: number, to: number): number =>
  Math.atan2(Math.sin(to - from), Math.cos(to - from));

const emptyAxis = (): AxisMotionDiagnostic => ({
  maxSpeedDegPerSec: 0,
  speedTime: 0,
  maxAccelerationDegPerSec2: 0,
  accelerationTime: 0,
});

/**
 * Frame-by-frame motion diagnostic for one authored joint.
 *
 * Rotations are compared with shortest-path angular differences so crossing the
 * ±180° representation boundary never looks like a false snap. Speed and
 * acceleration are finite-difference authoring signals, not force/injury data
 * and deliberately carry no universal pass/fail threshold.
 */
export function measureJointMotion(
  clip: StudioClip,
  bone: BoneName,
): JointMotionDiagnostic {
  const fps = clip.fps > 0 ? clip.fps : 30;
  const lastFrame = Math.max(1, Math.ceil(clip.duration * fps));
  const times: number[] = [];
  for (let frame = 0; frame <= lastFrame; frame += 1) {
    const time = Math.min(clip.duration, frame / fps);
    if (times.length === 0 || Math.abs(time - times[times.length - 1]) > 1e-10) times.push(time);
  }

  const rotations = times.map((time) => boneRotation(sampleClip(clip, time).pose, bone));
  const axes: Record<Axis, AxisMotionDiagnostic> = {
    x: emptyAxis(),
    y: emptyAxis(),
    z: emptyAxis(),
  };

  let maxSpeed: MotionWorstPoint = { axis: 'x', value: 0, time: 0 };
  let maxAcceleration: MotionWorstPoint = { axis: 'x', value: 0, time: 0 };

  for (const axis of AXES) {
    const velocities: TimedVelocity[] = [];
    for (let index = 1; index < times.length; index += 1) {
      const dt = times[index] - times[index - 1];
      if (dt <= 0) continue;
      const delta = shortestAngleDelta(rotations[index - 1][axis], rotations[index][axis]);
      const velocity = toDeg(delta) / dt;
      velocities.push({ value: velocity, time: times[index] });
      const speed = Math.abs(velocity);
      if (speed > axes[axis].maxSpeedDegPerSec) {
        axes[axis].maxSpeedDegPerSec = speed;
        axes[axis].speedTime = times[index];
      }
      if (speed > maxSpeed.value) maxSpeed = { axis, value: speed, time: times[index] };
    }

    for (let index = 1; index < velocities.length; index += 1) {
      const dt = velocities[index].time - velocities[index - 1].time;
      if (dt <= 0) continue;
      const acceleration = Math.abs((velocities[index].value - velocities[index - 1].value) / dt);
      if (acceleration > axes[axis].maxAccelerationDegPerSec2) {
        axes[axis].maxAccelerationDegPerSec2 = acceleration;
        axes[axis].accelerationTime = velocities[index].time;
      }
      if (acceleration > maxAcceleration.value) {
        maxAcceleration = { axis, value: acceleration, time: velocities[index].time };
      }
    }
  }

  return {
    bone,
    fps,
    sampleCount: times.length,
    axes,
    maxSpeed,
    maxAcceleration,
  };
}
''')

Path('src/editor/motionDiagnostics.test.ts').write_text(r'''import { describe, expect, it } from 'vitest';
import type { StudioClip } from '../animation/clip';
import { restPose } from '../rig/pose';
import { vec3 } from '../rig/types';
import { measureJointMotion } from './motionDiagnostics';

const linearForearmClip = (): StudioClip => {
  const start = restPose();
  start.rotations.forearm_l = vec3(0, 0, 0);
  const end = restPose();
  end.rotations.forearm_l = vec3(Math.PI / 2, 0, 0);
  return {
    id: 'motion-diagnostic-linear',
    name: 'motion_diagnostic_linear',
    exerciseId: 'diagnostic',
    duration: 1,
    fps: 30,
    loop: false,
    keyframes: [
      { id: 'start', time: 0, pose: start, ik: {}, easing: 'linear' },
      { id: 'end', time: 1, pose: end, ik: {}, easing: 'hold' },
    ],
    locks: [],
    equipment: [],
  };
};

describe('selected-joint motion diagnostics', () => {
  it('measures a constant 90 degree-per-second hinge without inventing acceleration', () => {
    const diagnostic = measureJointMotion(linearForearmClip(), 'forearm_l');
    expect(diagnostic.fps).toBe(30);
    expect(diagnostic.sampleCount).toBe(31);
    expect(diagnostic.axes.x.maxSpeedDegPerSec).toBeCloseTo(90, 8);
    expect(diagnostic.axes.x.maxAccelerationDegPerSec2).toBeLessThan(1e-8);
    expect(diagnostic.axes.y.maxSpeedDegPerSec).toBe(0);
    expect(diagnostic.axes.z.maxSpeedDegPerSec).toBe(0);
    expect(diagnostic.maxSpeed.axis).toBe('x');
  });

  it('uses shortest-path angle differences across the representation boundary', () => {
    const clip = linearForearmClip();
    clip.duration = 1 / 30;
    clip.keyframes[0].pose.rotations.forearm_l = vec3((179 * Math.PI) / 180, 0, 0);
    clip.keyframes[1].time = 1 / 30;
    clip.keyframes[1].pose.rotations.forearm_l = vec3((-179 * Math.PI) / 180, 0, 0);
    const diagnostic = measureJointMotion(clip, 'forearm_l');
    expect(diagnostic.axes.x.maxSpeedDegPerSec).toBeCloseTo(60, 8);
  });
});
''')

p = 'src/editor/panels/JointPanel.tsx'
s = read(p)
s = replace_once(
    s,
    "import { skeleton, useStudio } from '../store';\n",
    "import { skeleton, useStudio } from '../store';\nimport { measureJointMotion } from '../motionDiagnostics';\n",
    'JointPanel diagnostic import',
)
s = replace_once(
    s,
    "  const time = useStudio((state) => state.time);\n",
    "  const time = useStudio((state) => state.time);\n  const setTime = useStudio((state) => state.setTime);\n",
    'JointPanel setTime',
)
s = replace_once(
    s,
    "  const rotation = selected ? pose.rotations[selected] : undefined;\n",
    "  const rotation = selected ? pose.rotations[selected] : undefined;\n  const motion = useMemo(\n    () => (selected ? measureJointMotion(clip, selected) : null),\n    [clip, selected],\n  );\n",
    'JointPanel motion memo',
)
s = replace_once(
    s,
    "      <h3>Segment timing</h3>\n",
    "      <h3>Motion quality</h3>\n      {selected && motion ? (\n        <div className=\"joint-motion-diagnostic\">\n          <p className=\"panel__hint\">\n            Frame-by-frame at {motion.fps} fps using shortest-path joint angles. These are animation\n            diagnostics, not force or injury thresholds.\n          </p>\n          <dl className=\"spec-list\">\n            <dt>Highest angular speed</dt>\n            <dd>\n              {motion.maxSpeed.value.toFixed(1)}°/s · {motion.maxSpeed.axis.toUpperCase()} · {motion.maxSpeed.time.toFixed(2)}s\n            </dd>\n            <dt>Highest angular acceleration</dt>\n            <dd>\n              {motion.maxAcceleration.value.toFixed(0)}°/s² · {motion.maxAcceleration.axis.toUpperCase()} · {motion.maxAcceleration.time.toFixed(2)}s\n            </dd>\n          </dl>\n          <div className=\"button-row\">\n            <button type=\"button\" onClick={() => setTime(motion.maxSpeed.time)}>\n              Jump to fastest frame\n            </button>\n            <button type=\"button\" onClick={() => setTime(motion.maxAcceleration.time)}>\n              Jump to sharpest change\n            </button>\n          </div>\n          <details>\n            <summary>Per-axis motion</summary>\n            <dl className=\"spec-list\">\n              {AXES.map((axis) => (\n                <div className=\"spec-list__pair\" key={`motion-${axis}`}>\n                  <dt>{axis.toUpperCase()}</dt>\n                  <dd>\n                    {motion.axes[axis].maxSpeedDegPerSec.toFixed(1)}°/s · {motion.axes[axis].maxAccelerationDegPerSec2.toFixed(0)}°/s²\n                  </dd>\n                </div>\n              ))}\n            </dl>\n          </details>\n        </div>\n      ) : (\n        <p className=\"panel__empty\">Select a joint to inspect its motion through the full rep.</p>\n      )}\n\n      <h3>Segment timing</h3>\n",
    'JointPanel motion UI',
)
write(p, s)

p = 'docs/STUDIO_CAPABILITY_ROADMAP.md'
s = read(p)
s = replace_once(
    s,
    '- Selected-bone timing authoring for delay, finish point and easing on each keyframe segment.\n',
    '- Selected-bone timing authoring for delay, finish point and easing on each keyframe segment.\n- Selected-joint frame-by-frame motion diagnostics report worst angular speed and acceleration with exact timestamps and jump-to-frame controls, giving elbow/shoulder timing review an objective signal without imposing a universal movement threshold.\n',
    'roadmap motion diagnostics',
)
write(p, s)

p = 'AI_CHANGELOG.md'
s = read(p)
entry = '''### ChatGPT — 2026-09-14 — selected-joint motion-quality diagnostics\n\nAdded `src/editor/motionDiagnostics.ts`, which samples the selected joint at the clip's authored FPS and measures per-axis angular speed and angular acceleration using shortest-path angle deltas. Crossing the ±180° representation boundary therefore cannot create a false 358° snap. The diagnostic reports the worst speed and acceleration with responsible axis/timestamp and deliberately has no universal pass/fail threshold: these are animation-quality signals, not force or injury estimates.\n\nThe Joint workspace now exposes the whole-rep maxima, per-axis values, and `Jump to fastest frame` / `Jump to sharpest change` controls. This pairs with the existing Focus-selected camera and per-joint segment timing so elbow snapping, shoulder take-over or abrupt secondary timing can be located first and then tuned without changing unrelated joints. Regression coverage proves a synthetic linear 90°/s hinge reads 90°/s with effectively zero acceleration and verifies shortest-path handling across +179°/-179°.\n\n\n'''
s = replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n' + entry, 'changelog insertion')
write(p, s)

print('Applied selected-joint motion-quality diagnostics')
