import { describe, expect, it } from 'vitest';
import type { StudioClip } from '../animation/clip';
import { restPose } from '../rig/pose';
import { canonicalSkeleton } from '../rig/skeleton';
import { vec3 } from '../rig/types';
import {
  measureBilateralMotionSymmetry,
  measureJointMotion,
  measureJointTransitions,
} from './motionDiagnostics';

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


  it('measures resolved left/right motion against the rig mirror transform', () => {
    const clip = linearForearmClip();
    clip.keyframes[0].pose.rotations.forearm_l = vec3(0, (30 * Math.PI) / 180, 0);
    clip.keyframes[0].pose.rotations.forearm_r = vec3(0, (-30 * Math.PI) / 180, 0);
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

});
