import { sampleClip, type StudioClip } from '../animation/clip';
import type { BoneName } from '../rig/boneNames';
import { boneRotation } from '../rig/pose';
import { AXES } from '../rig/types';
import { toDeg } from '../core/math';

export interface JointSegmentTimingDiagnostic {
  bone: BoneName;
  excursionDeg: number;
  onsetTime: number | null;
  onsetPercent: number | null;
  finishTime: number | null;
  finishPercent: number | null;
}

export interface JointCoordinationDiagnostic {
  segmentStart: number;
  segmentEnd: number;
  lead: JointSegmentTimingDiagnostic;
  support: JointSegmentTimingDiagnostic;
  /** support onset minus lead onset. Positive means the selected/lead joint starts first. */
  onsetLagSeconds: number | null;
}

const shortestAngleDelta = (from: number, to: number): number =>
  Math.atan2(Math.sin(to - from), Math.cos(to - from));

function distanceDeg(
  clip: StudioClip,
  bone: BoneName,
  baseTime: number,
  time: number,
): number {
  const base = boneRotation(sampleClip(clip, baseTime).pose, bone);
  const current = boneRotation(sampleClip(clip, time).pose, bone);
  let squared = 0;
  for (const axis of AXES) {
    const degrees = toDeg(shortestAngleDelta(base[axis], current[axis]));
    squared += degrees * degrees;
  }
  return Math.sqrt(squared);
}

function measureBone(
  clip: StudioClip,
  bone: BoneName,
  segmentStart: number,
  segmentEnd: number,
): JointSegmentTimingDiagnostic {
  const duration = Math.max(1e-9, segmentEnd - segmentStart);
  const fps = clip.fps > 0 ? clip.fps : 30;
  const firstFrame = Math.floor(segmentStart * fps);
  const lastFrame = Math.ceil(segmentEnd * fps);
  const samples: { time: number; distance: number }[] = [];

  for (let frame = firstFrame; frame <= lastFrame; frame += 1) {
    const time = Math.min(segmentEnd, Math.max(segmentStart, frame / fps));
    if (samples.length && Math.abs(time - samples[samples.length - 1].time) < 1e-10) continue;
    samples.push({ time, distance: distanceDeg(clip, bone, segmentStart, time) });
  }
  if (!samples.length || samples[0].time > segmentStart + 1e-10) {
    samples.unshift({ time: segmentStart, distance: 0 });
  }
  if (samples[samples.length - 1].time < segmentEnd - 1e-10) {
    samples.push({ time: segmentEnd, distance: distanceDeg(clip, bone, segmentStart, segmentEnd) });
  }

  const excursionDeg = Math.max(...samples.map((sample) => sample.distance));
  if (excursionDeg < 0.25) {
    return { bone, excursionDeg, onsetTime: null, onsetPercent: null, finishTime: null, finishPercent: null };
  }

  // Ignore tiny floating-point/keyframe noise while still detecting deliberately
  // small support motion. Five percent works across both 126° elbow flexion and
  // the curl's subtle 4° upper-arm contribution; 0.1° is the absolute floor.
  const onsetThreshold = Math.max(0.1, excursionDeg * 0.05);
  const finishThreshold = excursionDeg * 0.95;
  const onset = samples.find((sample) => sample.distance >= onsetThreshold) ?? null;
  const finish = samples.find((sample) => sample.distance >= finishThreshold) ?? null;

  const percent = (time: number | null): number | null =>
    time === null ? null : Math.max(0, Math.min(1, (time - segmentStart) / duration));

  return {
    bone,
    excursionDeg,
    onsetTime: onset?.time ?? null,
    onsetPercent: percent(onset?.time ?? null),
    finishTime: finish?.time ?? null,
    finishPercent: percent(finish?.time ?? null),
  };
}

/**
 * Compare movement timing for a selected joint and a support/parent joint in
 * one authored keyframe segment. This reports coordination; it never labels a
 * lag as good/bad because sequencing is exercise-specific.
 */
export function measureJointCoordination(
  clip: StudioClip,
  leadBone: BoneName,
  supportBone: BoneName,
  segmentStart: number,
  segmentEnd: number,
): JointCoordinationDiagnostic {
  const lead = measureBone(clip, leadBone, segmentStart, segmentEnd);
  const support = measureBone(clip, supportBone, segmentStart, segmentEnd);
  return {
    segmentStart,
    segmentEnd,
    lead,
    support,
    onsetLagSeconds:
      lead.onsetTime !== null && support.onsetTime !== null
        ? support.onsetTime - lead.onsetTime
        : null,
  };
}
