import type { BoneName, Side } from '../rig/boneNames';
import { FINGERS } from '../rig/boneNames';
import { PoseEvaluation, type Skeleton } from '../rig/skeleton';
import type { Pose, Vec3 } from '../rig/types';
import { clampPose, clonePose, poseFromDegrees } from '../rig/pose';
import { toRad } from '../core/math';
import { nextId } from '../core/id';
import type {
  ExerciseDefinition,
  HandSpec,
  FootSpec,
  MovementPhase,
  PoseSpec,
  PhaseJointTiming,
} from '../exercises/types';
import { tempoDuration } from '../exercises/types';
import { gripProfile } from '../exercises/gripProfiles';
import type { IKChainId } from '../ik/types';
import type { Keyframe, KeyframeIK, PoseMarkerKind, StudioClip } from './clip';
import { resolveEquipment } from '../equipment/attach';
import { measureGripFit } from '../equipment/gripDiagnostics';
import type { EquipmentInstance } from '../equipment/types';

/**
 * Build an animation from an exercise definition.
 *
 * Nothing here is generative or random: the same definition always produces the
 * same clip, phase boundaries land exactly on the tempo, and the last keyframe
 * is the first one again so the loop closes perfectly. The result is a starting
 * point the editor can then refine, not a black box.
 */
export function generateClip(skeleton: Skeleton, exercise: ExerciseDefinition): StudioClip {
  const poses: Record<'start' | 'peak', Pose> = {
    start: buildPose(skeleton, exercise, exercise.startPose, 'start'),
    peak: buildPose(skeleton, exercise, exercise.peakPose, 'peak'),
  };
  const ik: Record<'start' | 'peak', Partial<Record<IKChainId, KeyframeIK>>> = {
    start: ikFromSpec(exercise.startPose),
    peak: ikFromSpec(exercise.peakPose),
  };

  const phases = exercise.phases;
  if (phases.length === 0) {
    throw new Error(`Exercise "${exercise.id}" defines no movement phases`);
  }

  const keyframes: Keyframe[] = [];
  let time = 0;
  keyframes.push({
    id: nextId('kf'),
    time: 0,
    pose: clonePose(poses.start),
    ik: cloneIK(ik.start),
    easing: phases[0].easing,
    jointTiming: cloneJointTiming(phases[0].jointTiming),
    ...ikTimingOf(phases[0]),
    phaseId: phases[0].id,
    marker: 'start',
    label: exercise.startPose.label,
  });

  phases.forEach((phase, index) => {
    time += phaseDuration(exercise, phase);
    const next = phases[index + 1];
    const previous = phases[index - 1];
    const isLast = index === phases.length - 1;
    const marker: PoseMarkerKind = isLast
      ? 'return'
      : phase.to === 'peak' && previous?.to !== 'peak'
        ? 'peak'
        : 'transition';
    keyframes.push({
      id: nextId('kf'),
      time: round(time),
      pose: clonePose(poses[phase.to]),
      ik: cloneIK(ik[phase.to]),
      easing: next?.easing ?? 'lift',
      jointTiming: cloneJointTiming(next?.jointTiming),
      ...ikTimingOf(next),
      phaseId: next?.id,
      marker,
      label: phase.to === 'peak' ? exercise.peakPose.label : exercise.startPose.label,
    });
  });

  return {
    id: nextId('clip'),
    name: exercise.clipName,
    exerciseId: exercise.id,
    duration: round(time),
    fps: 30,
    loop: true,
    keyframes,
    locks: exercise.locks.map((lock) => ({ ...lock })),
    equipment: exercise.equipment.instances.map((instance) => ({ ...instance })),
    hands: { ...exercise.hands },
    ...(exercise.rootPivot ? { rootPivot: { ...exercise.rootPivot } } : {}),
  };
}

const round = (value: number): number => Math.round(value * 1e6) / 1e6;

/** A phase's IK timing for its keyframe, absent when it sets none. */
const ikTimingOf = (phase: MovementPhase | undefined) =>
  phase?.ikTiming
    ? {
        ikTiming: Object.fromEntries(
          Object.entries(phase.ikTiming).map(([chain, timing]) => [chain, { ...timing }]),
        ) as NonNullable<MovementPhase['ikTiming']>,
      }
    : {};

export const phaseDuration = (exercise: ExerciseDefinition, phase: MovementPhase): number =>
  phase.duration ?? tempoDuration(exercise.tempo, phase);

/** Phase boundaries in seconds, for the timeline ruler. */
export function phaseBoundaries(exercise: ExerciseDefinition): { phase: MovementPhase; start: number; end: number }[] {
  let time = 0;
  return exercise.phases.map((phase) => {
    const start = time;
    time += phaseDuration(exercise, phase);
    return { phase, start, end: round(time) };
  });
}

/**
 * Compose one authored pose: the pose spec, then the joint targets for that end
 * of the movement, then grip and stance, then anatomical clamping.
 */
function buildPose(
  skeleton: Skeleton,
  exercise: ExerciseDefinition,
  spec: PoseSpec,
  end: 'start' | 'peak',
): Pose {
  const joints: PoseSpec['joints'] = {};
  for (const [bone, rotation] of Object.entries(spec.joints)) {
    joints[bone as BoneName] = { ...rotation };
  }
  for (const target of exercise.jointTargets) {
    const existing = joints[target.bone] ?? {};
    joints[target.bone] = { ...existing, [target.axis]: end === 'start' ? target.start : target.peak };
  }

  const pose = poseFromDegrees(joints, spec.root);
  applyGrip(pose, exercise.hands);
  applyStance(pose, exercise.feet, spec, skeleton);
  return fitThumbGripToSkeleton(
    skeleton,
    clampPose(skeleton, pose),
    exercise.equipment.instances,
  );
}

/**
 * Close the fingers to the degree the grip needs. Authored per exercise rather
 * than per finger — nobody wants to keyframe thirty knuckles.
 *
 * Finger flexion lives on z, which is a handed axis: the two hands curl towards
 * opposite world directions, so the right hand takes the negative angle. Sending
 * both hands the same sign extends the right hand's fingers instead of closing
 * them, and the joint limits then clamp it into a flat, open palm.
 */
export function applyGrip(pose: Pose, hands: HandSpec): void {
  const closure = Math.max(0, Math.min(1, hands.closure));
  const profile = gripProfile(hands.gripPreset ?? hands.grip);
  const sides: { side: Side; sign: number }[] = [
    { side: 'l', sign: 1 },
    { side: 'r', sign: -1 },
  ];
  for (const { side, sign } of sides) {
    for (const finger of FINGERS) {
      const digitClosure = Math.max(0, Math.min(1, hands.digitClosure?.[finger] ?? closure));
      if (digitClosure <= 0) continue;
      const isThumb = finger === 'thumb';
      const segments = isThumb ? profile.thumb : profile.fingers;
      segments.forEach((maximum, index) => {
        const bone = `${finger}_0${index + 1}_${side}` as BoneName;
        const existing = pose.rotations[bone];
        pose.rotations[bone] = {
          x:
            isThumb && index === 0
              ? toRad(profile.thumbOppositionX * digitClosure)
              : existing?.x ?? 0,
          y: existing?.y ?? 0,
          z: sign * toRad(maximum * digitClosure),
        };
      });
    }
  }
}

interface ThumbGripAxes {
  baseX: number;
  baseZ: number;
  middleZ: number;
  tipZ: number;
}

interface ThumbSearchAxis {
  bone: BoneName;
  axis: 'x' | 'z';
  key: keyof ThumbGripAxes;
}

/**
 * Keep the accepted authored grip profile whenever it already fits the active
 * skeleton. A clean-room/future rig may place its thumb differently at rest;
 * in that case fit only the thumb, against the exact same geometric envelope,
 * using that skeleton's own joint limits.
 *
 * The search is deterministic coordinate descent on a 5-degree grid. It never
 * changes the envelope, finger rotations, equipment geometry or hand bone. If
 * no legal thumb pose clears the existing envelope, the authored pose is
 * restored so the review gate continues to fail visibly.
 */
function fitThumbGripToSkeleton(
  skeleton: Skeleton,
  pose: Pose,
  equipmentInstances: EquipmentInstance[],
): Pose {
  const instance = equipmentInstances.find(
    (candidate) =>
      candidate.kind === 'dumbbell' &&
      candidate.attachment.mode === 'hand',
  );
  if (!instance || instance.attachment.mode !== 'hand') return pose;

  const side = instance.attachment.side;
  const evaluation = new PoseEvaluation(skeleton).apply(pose);
  const transform = resolveEquipment(evaluation, [instance]).get(instance.id);
  if (!transform) return pose;

  const initial = measureGripFit(evaluation, transform, side);
  if (initial.withinEnvelope) return pose;

  const prefix = (segment: number) => `thumb_0${segment}_${side}` as BoneName;
  const searchAxes: ThumbSearchAxis[] = [
    { bone: prefix(1), axis: 'x', key: 'baseX' },
    { bone: prefix(1), axis: 'z', key: 'baseZ' },
    { bone: prefix(2), axis: 'z', key: 'middleZ' },
    { bone: prefix(3), axis: 'z', key: 'tipZ' },
  ];
  const degreesOf = (bone: BoneName, axis: 'x' | 'z') =>
    ((pose.rotations[bone]?.[axis] ?? 0) * 180) / Math.PI;
  const original: ThumbGripAxes = {
    baseX: degreesOf(prefix(1), 'x'),
    baseZ: degreesOf(prefix(1), 'z'),
    middleZ: degreesOf(prefix(2), 'z'),
    tipZ: degreesOf(prefix(3), 'z'),
  };
  const candidate: ThumbGripAxes = { ...original };

  const applyCandidate = () => {
    for (const item of searchAxes) {
      const existing = pose.rotations[item.bone] ?? { x: 0, y: 0, z: 0 };
      pose.rotations[item.bone] = {
        ...existing,
        [item.axis]: toRad(candidate[item.key]),
      };
    }
    evaluation.apply(pose);
    return measureGripFit(evaluation, transform, side);
  };

  const score = (fit: ReturnType<typeof measureGripFit>) => {
    const reachFailure = Math.max(0, fit.reachUse - 1);
    const gapFailure = Math.max(0, fit.widestGapDeg - 170);
    const deviation =
      Object.keys(candidate).reduce((sum, key) => {
        const name = key as keyof ThumbGripAxes;
        const delta = (candidate[name] - original[name]) / 60;
        return sum + delta * delta;
      }, 0);
    // Failure terms dominate. Once the established envelope is clear, prefer
    // a compact wrap and the smallest departure from the authored profile.
    return (
      reachFailure * 1000 +
      gapFailure * 20 +
      fit.reachUse +
      fit.widestGapDeg / 360 +
      deviation * 0.02
    );
  };

  let bestFit = initial;
  let bestScore = score(initial);
  for (let pass = 0; pass < 2; pass += 1) {
    for (const item of searchAxes) {
      const limit = skeleton.bone(item.bone).definition.limits[item.axis];
      if (!limit) continue;
      const values = new Set<number>([
        candidate[item.key],
        original[item.key],
        limit.min,
        limit.max,
      ]);
      const first = Math.ceil(limit.min / 5) * 5;
      for (let value = first; value <= limit.max + 1e-9; value += 5) {
        values.add(value);
      }

      let axisBest = candidate[item.key];
      let axisBestFit = bestFit;
      let axisBestScore = bestScore;
      for (const value of values) {
        candidate[item.key] = value;
        const fit = applyCandidate();
        const nextScore = score(fit);
        if (nextScore < axisBestScore - 1e-12) {
          axisBest = value;
          axisBestFit = fit;
          axisBestScore = nextScore;
        }
      }
      candidate[item.key] = axisBest;
      bestFit = applyCandidate();
      bestScore = axisBestScore;
      // Preserve the exact measurement selected for the winning coordinate;
      // the re-application above should be numerically identical.
      if (
        Math.abs(bestFit.reachUse - axisBestFit.reachUse) > 1e-10 ||
        Math.abs(bestFit.widestGapDeg - axisBestFit.widestGapDeg) > 1e-8
      ) {
        bestFit = axisBestFit;
      }
    }
  }

  if (!bestFit.withinEnvelope) {
    Object.assign(candidate, original);
    applyCandidate();
    return pose;
  }

  // Keep a symmetric opposite hand when the exercise carries the usual pair.
  const opposite = side === 'l' ? 'r' : 'l';
  const hasOpposite = equipmentInstances.some(
    (candidateInstance) =>
      candidateInstance.kind === 'dumbbell' &&
      candidateInstance.attachment.mode === 'hand' &&
      candidateInstance.attachment.side === opposite,
  );
  if (hasOpposite) {
    for (let segment = 1; segment <= 3; segment += 1) {
      const source = prefix(segment);
      const target = `thumb_0${segment}_${opposite}` as BoneName;
      const sourceRotation = pose.rotations[source] ?? { x: 0, y: 0, z: 0 };
      const targetRotation = pose.rotations[target] ?? { x: 0, y: 0, z: 0 };
      pose.rotations[target] = {
        ...targetRotation,
        x: sourceRotation.x,
        z: -sourceRotation.z,
      };
    }
  }

  return pose;
}

/**
 * Set the stance from the exercise's foot spec: hips abduct to reach the
 * requested width, and the feet turn out by the requested angle.
 */
export function applyStance(
  pose: Pose,
  feet: FootSpec,
  spec: PoseSpec,
  skeleton?: Skeleton,
): void {
  // Preserve the accepted v3 numbers exactly when no skeleton is supplied,
  // while letting shadow/future rigs derive stance from their own rest geometry.
  // v3: hip half-width 0.09 m, hip-to-ankle vertical span 0.84 m.
  // ORIGINAL v4: 0.092 m and 0.875 m respectively.
  const HIP_HALF_WIDTH = skeleton
    ? Math.abs(skeleton.bone('thigh_l').restHead.x)
    : 0.09;
  const LEG_LENGTH = skeleton
    ? Math.abs(skeleton.bone('thigh_l').restHead.y - skeleton.bone('shin_l').restTail.y)
    : 0.84;
  const halfWidth = feet.width / 2;
  const abduction = Math.atan2(halfWidth - HIP_HALF_WIDTH, LEG_LENGTH);

  const sides: { side: Side; sign: number }[] = [
    { side: 'l', sign: -1 },
    { side: 'r', sign: 1 },
  ];
  for (const { side, sign } of sides) {
    const thigh = `thigh_${side}` as BoneName;
    const shin = `shin_${side}` as BoneName;
    const foot = `foot_${side}` as BoneName;

    // Authored angles win: the spec is the place to override a generated stance.
    if (spec.joints[thigh]?.z === undefined) {
      const existing = pose.rotations[thigh] ?? { x: 0, y: 0, z: 0 };
      pose.rotations[thigh] = { ...existing, z: sign * abduction };
    }
    if (spec.joints[shin]?.z === undefined) {
      const existing = pose.rotations[shin] ?? { x: 0, y: 0, z: 0 };
      pose.rotations[shin] = { ...existing, z: 0 };
    }
    if (spec.joints[foot]?.y === undefined && feet.toeOut !== 0) {
      const existing = pose.rotations[foot] ?? { x: 0, y: 0, z: 0 };
      // The foot's inversion axis runs along the foot, so toe-out lives on z.
      pose.rotations[foot] = { ...existing, z: -sign * toRad(feet.toeOut) };
    }
  }
}

function ikFromSpec(
  spec: PoseSpec,
): Partial<Record<IKChainId, KeyframeIK>> {
  const out: Partial<Record<IKChainId, KeyframeIK>> = {};
  for (const [chain, value] of Object.entries(spec.ik ?? {})) {
    if (!value) continue;
    out[chain as IKChainId] = {
      enabled: true,
      target: { ...value.target },
      pole: { ...value.pole },
      ...(value.aim ? { aim: structuredClone(value.aim) } : {}),
      ...(value.onBall ? { onBall: { ...value.onBall } } : {}),
    };
  }
  return out;
}

function cloneIK(
  ik: Partial<Record<IKChainId, KeyframeIK>>,
): Partial<Record<IKChainId, KeyframeIK>> {
  const out: Partial<Record<IKChainId, KeyframeIK>> = {};
  for (const [chain, value] of Object.entries(ik)) {
    if (!value) continue;
    out[chain as IKChainId] = { ...value, target: { ...value.target }, pole: { ...value.pole } };
  }
  return out;
}

function cloneJointTiming(
  timing: Partial<Record<BoneName, PhaseJointTiming>> | undefined,
): Partial<Record<BoneName, PhaseJointTiming>> | undefined {
  if (!timing) return undefined;
  const out: Partial<Record<BoneName, PhaseJointTiming>> = {};
  for (const [bone, value] of Object.entries(timing)) {
    if (value) out[bone as BoneName] = { ...value };
  }
  return out;
}

export type { Vec3 };
