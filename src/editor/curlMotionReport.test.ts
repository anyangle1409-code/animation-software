import { describe, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import {
  measureBilateralMotionSymmetry,
  measureJointMotion,
  measureJointPath,
  measureJointTransitions,
} from './motionDiagnostics';
import { measureJointCoordination } from './coordinationDiagnostics';

const round = (value: number | null, digits = 4) =>
  value === null ? null : Number(value.toFixed(digits));

describe('temporary curl motion report', () => {
  it('prints current retained curl motion metrics', () => {
    const clip = generateClip(canonicalSkeleton, bicepCurl);
    const elbow = measureJointMotion(clip, 'forearm_l');
    const upper = measureJointMotion(clip, 'upperarm_l');
    const clavicle = measureJointMotion(clip, 'clavicle_l');
    const transitions = measureJointTransitions(clip, 'forearm_l');
    const bilateral = measureBilateralMotionSymmetry(clip, canonicalSkeleton, 'forearm_l');
    const path = measureJointPath(clip, canonicalSkeleton, 'forearm_l');

    const segmentReports = clip.keyframes.slice(0, -1).map((frame, index) => {
      const next = clip.keyframes[index + 1];
      const coordination = measureJointCoordination(
        clip,
        'forearm_l',
        'upperarm_l',
        frame.time,
        next.time,
      );
      return {
        from: frame.label ?? frame.id,
        to: next.label ?? next.id,
        start: round(frame.time),
        end: round(next.time),
        elbowExcursionDeg: round(coordination.lead.excursionDeg, 3),
        elbowOnsetPercent: round(coordination.lead.onsetPercent, 3),
        upperArmExcursionDeg: round(coordination.support.excursionDeg, 3),
        upperArmOnsetPercent: round(coordination.support.onsetPercent, 3),
        supportLagSeconds: round(coordination.onsetLagSeconds, 3),
      };
    });

    console.log('CURL_MOTION_REPORT=' + JSON.stringify({
      duration: clip.duration,
      fps: clip.fps,
      keyframes: clip.keyframes.map((frame) => ({
        id: frame.id,
        label: frame.label ?? null,
        time: round(frame.time),
        easing: frame.easing,
      })),
      elbow: {
        maxSpeedDegPerSec: round(elbow.maxSpeed.value, 2),
        maxSpeedAxis: elbow.maxSpeed.axis,
        maxSpeedTime: round(elbow.maxSpeed.time, 3),
        maxAccelerationDegPerSec2: round(elbow.maxAcceleration.value, 1),
        maxAccelerationAxis: elbow.maxAcceleration.axis,
        maxAccelerationTime: round(elbow.maxAcceleration.time, 3),
      },
      upperArm: {
        maxSpeedDegPerSec: round(upper.maxSpeed.value, 2),
        maxAccelerationDegPerSec2: round(upper.maxAcceleration.value, 1),
      },
      clavicle: {
        maxSpeedDegPerSec: round(clavicle.maxSpeed.value, 2),
        maxAccelerationDegPerSec2: round(clavicle.maxAcceleration.value, 1),
      },
      transition: transitions.maxJump ? {
        axis: transitions.maxJump.axis,
        time: round(transitions.maxJump.time, 3),
        label: transitions.maxJump.label ?? null,
        incomingDegPerSec: round(transitions.maxJump.incomingDegPerSec, 2),
        outgoingDegPerSec: round(transitions.maxJump.outgoingDegPerSec, 2),
        velocityJumpDegPerSec: round(transitions.maxJump.velocityJumpDegPerSec, 2),
      } : null,
      bilateral: bilateral ? {
        maxErrorDeg: round(bilateral.maxError.value, 5),
        maxErrorAxis: bilateral.maxError.axis,
        maxErrorTime: round(bilateral.maxError.time, 3),
        rmsErrorDeg: round(bilateral.rmsErrorDeg, 5),
      } : null,
      elbowPath: path ? {
        parent: path.parent,
        maxDriftMm: round(path.maxDriftMetres * 1000, 2),
        maxDriftTime: round(path.maxDriftTime, 3),
        totalPathMm: round(path.totalPathMetres * 1000, 2),
        returnErrorMm: round(path.returnErrorMetres * 1000, 4),
      } : null,
      segments: segmentReports,
    }));
  });
});
