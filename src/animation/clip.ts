import type { BoneName } from '../rig/boneNames';
import type { Pose, Vec3 } from '../rig/types';
import type { EasingKind, PhaseJointTiming } from '../exercises/types';
import type { HandSpec } from '../exercises/types';
import type { EffectorLock } from '../constraints/types';
import type { EquipmentInstance } from '../equipment/types';
import type { IKChainId } from '../ik/types';
import { blendPoses, clonePose } from '../rig/pose';
import { ease } from './easing';
import { clamp, lerpAngle } from '../core/math';

export type PoseMarkerKind = 'start' | 'transition' | 'peak' | 'return';

export interface KeyframeIK {
  enabled: boolean;
  target: Vec3;
  pole: Vec3;
  aim?: { direction: Vec3; forward?: Vec3 };
}

export interface Keyframe {
  id: string;
  /** Seconds from the start of the clip. */
  time: number;
  /** Forward-kinematic pose. IK targets, when present, override limbs. */
  pose: Pose;
  ik: Partial<Record<IKChainId, KeyframeIK>>;
  /** Easing used from this keyframe to the next. */
  easing: EasingKind;
  /** Optional per-bone timing used from this keyframe to the next. */
  jointTiming?: Partial<Record<BoneName, PhaseJointTiming>>;
  /** Semantic landmark used by the Studio timeline; it does not alter motion. */
  marker?: PoseMarkerKind;
  label?: string;
  phaseId?: string;
}

export interface StudioClip {
  id: string;
  /** Export name, e.g. `bicep_curl`. */
  name: string;
  exerciseId: string;
  duration: number;
  fps: number;
  loop: boolean;
  keyframes: Keyframe[];
  locks: EffectorLock[];
  equipment: EquipmentInstance[];
  /**
   * The grip the clip was generated with. The finger rotations in the poses
   * already carry it, but a character with its own solved grip needs to know
   * which family and how closed, to substitute its own angles for the
   * authored ones.
   */
  hands?: HandSpec;
}

export interface ClipSample {
  pose: Pose;
  ik: Partial<Record<IKChainId, KeyframeIK>>;
  phaseId?: string;
  /** Index of the keyframe at or before the sample time. */
  index: number;
}

/** Keyframes sorted by time. Callers may insert freely; this owns the order. */
export const sortedKeyframes = (clip: StudioClip): Keyframe[] =>
  [...clip.keyframes].sort((a, b) => a.time - b.time);

/**
 * Sample the clip at `time`. Poses are blended with the easing of the keyframe
 * being left, so a phase's tempo lives on its own keyframe. A phase may also
 * delay or finish individual bones independently; that is used for secondary
 * body motion without inserting extra stop-start keyframes into a smooth rep.
 */
export function sampleClip(clip: StudioClip, time: number): ClipSample {
  const keyframes = sortedKeyframes(clip);
  if (keyframes.length === 0) {
    throw new Error(`Clip "${clip.name}" has no keyframes`);
  }
  const t = clip.loop ? wrap(time, clip.duration) : clamp(time, 0, clip.duration);

  let index = 0;
  for (let i = 0; i < keyframes.length; i += 1) {
    if (keyframes[i].time <= t + 1e-9) index = i;
  }
  const from = keyframes[index];
  const to = keyframes[index + 1];
  if (!to) {
    return { pose: clonePose(from.pose), ik: cloneIK(from.ik), phaseId: from.phaseId, index };
  }

  const span = to.time - from.time;
  const raw = span <= 1e-9 ? 0 : (t - from.time) / span;
  const blend = ease(from.easing, raw);
  const pose = blendPoses(from.pose, to.pose, blend);
  applyJointTiming(pose, from, to, raw);

  return {
    pose,
    ik: blendIK(from.ik, to.ik, blend),
    phaseId: from.phaseId,
    index,
  };
}

const wrap = (time: number, duration: number): number =>
  duration <= 0 ? 0 : ((time % duration) + duration) % duration;

/**
 * Override the ordinary phase blend for explicitly timed bones. `delay` and
 * `finish` are normalised phase positions, so tempo changes do not alter the
 * intended coordination. The local easing starts and ends at zero velocity for
 * `lift`, keeping a delayed stabiliser smooth rather than snapping into motion.
 */
function applyJointTiming(pose: Pose, from: Keyframe, to: Keyframe, raw: number): void {
  for (const [name, timing] of Object.entries(from.jointTiming ?? {})) {
    if (!timing) continue;
    const bone = name as BoneName;
    const delay = clamp(timing.delay ?? 0, 0, 1);
    const finish = Math.max(delay, clamp(timing.finish ?? 1, 0, 1));
    const timingSpan = finish - delay;
    const localRaw =
      timingSpan <= 1e-9
        ? raw >= finish
          ? 1
          : 0
        : clamp((raw - delay) / timingSpan, 0, 1);
    const localBlend = ease(timing.easing ?? from.easing, localRaw);
    const a = from.pose.rotations[bone] ?? { x: 0, y: 0, z: 0 };
    const b = to.pose.rotations[bone] ?? { x: 0, y: 0, z: 0 };
    pose.rotations[bone] = {
      x: lerpAngle(a.x, b.x, localBlend),
      y: lerpAngle(a.y, b.y, localBlend),
      z: lerpAngle(a.z, b.z, localBlend),
    };
  }
}

function cloneIK(
  ik: Partial<Record<IKChainId, KeyframeIK>>,
): Partial<Record<IKChainId, KeyframeIK>> {
  const out: Partial<Record<IKChainId, KeyframeIK>> = {};
  for (const [chain, value] of Object.entries(ik)) {
    if (value) out[chain as IKChainId] = { ...value, target: { ...value.target }, pole: { ...value.pole } };
  }
  return out;
}

function blendIK(
  from: Partial<Record<IKChainId, KeyframeIK>>,
  to: Partial<Record<IKChainId, KeyframeIK>>,
  t: number,
): Partial<Record<IKChainId, KeyframeIK>> {
  const out: Partial<Record<IKChainId, KeyframeIK>> = {};
  const chains = new Set<IKChainId>([
    ...(Object.keys(from) as IKChainId[]),
    ...(Object.keys(to) as IKChainId[]),
  ]);
  for (const chain of chains) {
    const a = from[chain];
    const b = to[chain];
    if (!a || !b) {
      const only = a ?? b;
      if (only) out[chain] = { ...only, target: { ...only.target }, pole: { ...only.pole } };
      continue;
    }
    out[chain] = {
      enabled: a.enabled || b.enabled,
      target: mix(a.target, b.target, t),
      pole: mix(a.pole, b.pole, t),
      aim: a.aim && b.aim ? { direction: mix(a.aim.direction, b.aim.direction, t) } : a.aim ?? b.aim,
    };
  }
  return out;
}

const mix = (a: Vec3, b: Vec3, t: number): Vec3 => ({
  x: a.x + (b.x - a.x) * t,
  y: a.y + (b.y - a.y) * t,
  z: a.z + (b.z - a.z) * t,
});

/** True when the clip returns exactly to its opening pose. */
export function closesLoop(clip: StudioClip, epsilon = 1e-4): boolean {
  const keyframes = sortedKeyframes(clip);
  const first = keyframes[0];
  const last = keyframes[keyframes.length - 1];
  if (!first || !last) return false;
  if (Math.abs(last.time - clip.duration) > 1e-6) return false;
  const names = new Set([
    ...Object.keys(first.pose.rotations),
    ...Object.keys(last.pose.rotations),
  ]);
  for (const name of names) {
    const a = first.pose.rotations[name as keyof typeof first.pose.rotations];
    const b = last.pose.rotations[name as keyof typeof last.pose.rotations];
    const ax = a?.x ?? 0;
    const ay = a?.y ?? 0;
    const az = a?.z ?? 0;
    if (
      Math.abs(ax - (b?.x ?? 0)) > epsilon ||
      Math.abs(ay - (b?.y ?? 0)) > epsilon ||
      Math.abs(az - (b?.z ?? 0)) > epsilon
    ) {
      return false;
    }
  }
  return true;
}
