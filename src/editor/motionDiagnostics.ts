import { sampleClip, type StudioClip } from '../animation/clip';
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
