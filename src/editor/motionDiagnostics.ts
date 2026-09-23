import { Vector3 } from 'three';
import { sampleClip, sortedKeyframes, type StudioClip } from '../animation/clip';
import { AXES, type Axis } from '../rig/types';
import { mirrorBoneName, type BoneName } from '../rig/boneNames';
import { boneRotation, mirrorPose } from '../rig/pose';
import { PoseEvaluation, type Skeleton } from '../rig/skeleton';
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
  const parent = skeleton.jointParent(bone);
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
