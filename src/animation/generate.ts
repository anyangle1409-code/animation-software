import type { BoneName, Side } from '../rig/boneNames';
import { FINGERS } from '../rig/boneNames';
import { PoseEvaluation, canonicalSkeleton, type Skeleton } from '../rig/skeleton';
import type { Pose, Vec3 } from '../rig/types';
import { clampPose, clonePose, poseFromDegrees } from '../rig/pose';
import { toRad } from '../core/math';
import { HgQuat, HgVec3 } from '../core/linearMath';
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
import { IK_CHAINS } from '../ik/chains';
import type { Keyframe, KeyframeIK, PoseMarkerKind, StudioClip } from './clip';
import { resolveEquipment, socketResolver } from '../equipment/attach';
import { measureGripFit } from '../equipment/gripDiagnostics';
import type { EquipmentInstance } from '../equipment/types';
import { floorTargetForSkeleton } from '../constraints/floorGeometry';

/**
 * Build an animation from an exercise definition.
 *
 * Nothing here is generative or random: the same definition always produces the
 * same clip, phase boundaries land exactly on the tempo, and the last keyframe
 * is the first one again so the loop closes perfectly. The result is a starting
 * point the editor can then refine, not a black box.
 */
export function generateClip(skeleton: Skeleton, exercise: ExerciseDefinition): StudioClip {
  const startPose = buildPose(skeleton, exercise, exercise.startPose, 'start');
  const peakPose = buildPose(
    skeleton,
    exercise,
    exercise.peakPose,
    'peak',
    startPose,
  );
  const poses: Record<'start' | 'peak', Pose> = {
    start: startPose,
    peak: peakPose,
  };
  const ik: Record<'start' | 'peak', Partial<Record<IKChainId, KeyframeIK>>> = {
    start: ikFromSpecForSkeleton(
      skeleton,
      exercise,
      exercise.startPose,
      'start',
      poses.start,
    ),
    peak: ikFromSpecForSkeleton(
      skeleton,
      exercise,
      exercise.peakPose,
      'peak',
      poses.peak,
    ),
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
    ...(exercise.rootPivot
      ? { rootPivot: rootPivotForSkeleton(exercise.rootPivot, skeleton) }
      : {}),
  };
}

/**
 * Root pivots are authored against the current canonical reference rig. When
 * the pivot is the reference pelvis landmark, rotate a compatible future rig
 * about its own pelvis instead. That keeps body-relative motion body-relative
 * without changing the authored v3 clip at all.
 */
function rootPivotForSkeleton(pivot: Vec3, skeleton: Skeleton): Vec3 {
  const referencePelvis = canonicalSkeleton.bone('pelvis').restHead;
  const activePelvis = skeleton.bone('pelvis').restHead;
  const isReferencePelvis =
    Math.abs(pivot.x - referencePelvis.x) < 1e-9 &&
    Math.abs(pivot.y - referencePelvis.y) < 1e-9 &&
    Math.abs(pivot.z - referencePelvis.z) < 1e-9;
  return isReferencePelvis
    ? { x: activePelvis.x, y: activePelvis.y, z: activePelvis.z }
    : { ...pivot };
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
  floorReferencePose?: Pose,
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
  fitRootEndpointToActivePivot(skeleton, exercise, pose);
  applyGrip(pose, exercise.hands);
  applyStance(pose, exercise.feet, spec, skeleton);
  const fittedGrip = fitThumbGripToSkeleton(
    skeleton,
    clampPose(skeleton, pose),
    exercise.equipment.instances,
  );
  const fittedFloor = fitPitchedFloorRoot(
    skeleton,
    exercise,
    fittedGrip,
    end,
    floorReferencePose,
  );
  const fittedBallPivot = fitDynamicBallPivotRoot(
    skeleton,
    exercise,
    fittedFloor,
    floorReferencePose,
  );
  return fitEquipmentLockedArmRoot(
    skeleton,
    exercise,
    fittedBallPivot,
    end,
  );
}

/**
 * Exercise roots that rotate about the reference pelvis are authored so that
 * that pelvis landmark follows a particular world-space path. A compatible
 * skeleton with a different pelvis height needs a translated root endpoint to
 * keep that same path.
 *
 * This is exact geometry, not proportional scaling: move the root by the
 * rotated difference between the active and reference pivot landmarks. The
 * reference rig therefore remains bit-for-bit unchanged.
 */
function fitRootEndpointToActivePivot(
  skeleton: Skeleton,
  exercise: ExerciseDefinition,
  pose: Pose,
): void {
  if (!exercise.rootPivot) return;

  const referencePelvis = canonicalSkeleton.bone('pelvis').restHead;
  const pivot = exercise.rootPivot;
  const usesReferencePelvis =
    Math.abs(pivot.x - referencePelvis.x) < 1e-9 &&
    Math.abs(pivot.y - referencePelvis.y) < 1e-9 &&
    Math.abs(pivot.z - referencePelvis.z) < 1e-9;
  if (!usesReferencePelvis) return;

  const activePelvis = skeleton.bone('pelvis').restHead;
  const delta = new HgVec3(
    activePelvis.x - referencePelvis.x,
    activePelvis.y - referencePelvis.y,
    activePelvis.z - referencePelvis.z,
  );
  if (delta.lengthSq() < 1e-18) return;

  const rotation = new HgQuat().setFromEulerXZY(
    pose.rootRotation.x,
    pose.rootRotation.y,
    pose.rootRotation.z,
  );
  delta.applyQuaternion(rotation);
  pose.rootPosition = {
    x: pose.rootPosition.x - delta.x,
    y: pose.rootPosition.y - delta.y,
    z: pose.rootPosition.z - delta.z,
  };
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

/**
 * A calf-style floor lock with `onBall: {}` lets the ankle rise around a ball
 * that stays fixed. The authored root arc encodes a rotation of the reference
 * foot lever, not an absolute metre displacement. Recover that rotation from
 * the reference foot, then apply it to the active skeleton's ankle-to-ball
 * lever so a longer/shorter compatible foot reaches the same plantarflexion.
 */
function fitDynamicBallPivotRoot(
  skeleton: Skeleton,
  exercise: ExerciseDefinition,
  pose: Pose,
  floorReferencePose?: Pose,
): Pose {
  if (!floorReferencePose || Math.abs(pose.rootRotation.x) > 1e-6) return pose;
  const dynamicBallLocks = exercise.locks.filter(
    (lock) =>
      lock.enabled &&
      lock.mode === 'floor' &&
      lock.onBall !== undefined &&
      lock.onBall.ankle === undefined &&
      lock.chain.startsWith('leg'),
  );
  if (dynamicBallLocks.length === 0) return pose;

  const referenceFoot = canonicalSkeleton.bone('foot_l');
  const activeFoot = skeleton.bone('foot_l');
  if (
    Math.abs(activeFoot.length - referenceFoot.length) < 1e-9 &&
    Math.abs(activeFoot.restHead.y - referenceFoot.restHead.y) < 1e-9 &&
    Math.abs(activeFoot.restTail.z - referenceFoot.restTail.z) < 1e-9
  ) {
    return pose;
  }

  const deltaY = pose.rootPosition.y - floorReferencePose.rootPosition.y;
  const deltaZ = pose.rootPosition.z - floorReferencePose.rootPosition.z;
  if (Math.hypot(deltaY, deltaZ) < 1e-9) return pose;

  const refY = referenceFoot.restHead.y - referenceFoot.restTail.y;
  const refZ = referenceFoot.restHead.z - referenceFoot.restTail.z;
  const refStart = Math.atan2(refY, -refZ);
  const refEnd = Math.atan2(refY + deltaY, -(refZ + deltaZ));
  const rotation = refEnd - refStart;

  const activeEvaluation = new PoseEvaluation(skeleton).apply(floorReferencePose);
  const chain = IK_CHAINS[dynamicBallLocks[0].chain];
  const ankle = activeEvaluation.head(chain.end);
  const ball = activeEvaluation.tail(chain.end);
  const activeY = ankle.y - ball.y;
  const activeZ = ankle.z - ball.z;
  const activeLength = Math.hypot(activeY, activeZ);
  if (activeLength < 1e-9) return pose;

  const activeStart = Math.atan2(activeY, -activeZ);
  const activeEnd = activeStart + rotation;
  const desiredY = activeLength * Math.sin(activeEnd);
  const desiredZ = -activeLength * Math.cos(activeEnd);

  pose.rootPosition = {
    ...pose.rootPosition,
    y: floorReferencePose.rootPosition.y + (desiredY - activeY),
    z: floorReferencePose.rootPosition.z + (desiredZ - activeZ),
  };
  return pose;
}

/**
 * A pitched body supported by planted feet should keep the knee bend authored
 * by its exercise when a compatible skeleton has different femur/tibia lengths.
 *
 * Solve only root Y from two-bone geometry. Root Z, pitch, foot placement and
 * every authored technique threshold remain unchanged. Unpositioned floor
 * locks use the opening pose as their anchor, matching the runtime lock model.
 */
function fitPitchedFloorRoot(
  skeleton: Skeleton,
  exercise: ExerciseDefinition,
  pose: Pose,
  end: 'start' | 'peak',
  floorReferencePose?: Pose,
): Pose {
  if (Math.abs(pose.rootRotation.x) < 1e-6) return pose;

  // Preserve the accepted reference geometry exactly. The shadow/future rig
  // path is what needs body-relative adaptation.
  const referenceThigh = canonicalSkeleton.bone('thigh_l');
  const referenceShin = canonicalSkeleton.bone('shin_l');
  const activeThigh = skeleton.bone('thigh_l');
  const activeShin = skeleton.bone('shin_l');
  if (
    Math.abs(activeThigh.length - referenceThigh.length) < 1e-9 &&
    Math.abs(activeShin.length - referenceShin.length) < 1e-9
  ) {
    return pose;
  }

  const floorLocks = exercise.locks.filter(
    (lock) => lock.enabled && lock.mode === 'floor' && lock.chain.startsWith('leg'),
  );
  if (floorLocks.length === 0) return pose;

  const evaluation = new PoseEvaluation(skeleton).apply(pose);
  const referenceEvaluation = floorReferencePose
    ? new PoseEvaluation(skeleton).apply(floorReferencePose)
    : null;
  const deltas: number[] = [];

  for (const lock of floorLocks) {
    const chain = IK_CHAINS[lock.chain];
    const authored = exercise.jointTargets.find(
      (entry) => entry.bone === chain.mid && entry.axis === 'x',
    );
    if (!authored) continue;

    const kneeDegrees = end === 'start' ? authored.start : authored.peak;
    const knee = Math.abs(toRad(kneeDegrees));
    const upper = skeleton.bone(chain.root).length;
    const lower = skeleton.bone(chain.mid).length;
    const desiredReach = Math.sqrt(
      upper * upper +
      lower * lower +
      2 * upper * lower * Math.cos(knee),
    );

    let target: Vec3 | null = null;
    if (lock.position) {
      target = floorTargetForSkeleton(
        skeleton,
        lock.chain,
        lock.position,
        Boolean(lock.onBall),
      );
    } else if (referenceEvaluation) {
      const point = lock.onBall
        ? referenceEvaluation.tail(chain.end)
        : referenceEvaluation.head(chain.end);
      target = { x: point.x, y: point.y, z: point.z };
    }
    if (!target) continue;

    const hip = evaluation.head(chain.root);
    const dx = target.x - hip.x;
    const dz = target.z - hip.z;
    const verticalSquared = desiredReach * desiredReach - dx * dx - dz * dz;
    if (verticalSquared <= 0) continue;

    const desiredHipY = target.y + Math.sqrt(verticalSquared);
    deltas.push(desiredHipY - hip.y);
  }

  if (deltas.length === 0) return pose;
  const delta = deltas.reduce((sum, value) => sum + value, 0) / deltas.length;
  if (!Number.isFinite(delta) || Math.abs(delta) < 1e-9) return pose;
  pose.rootPosition = {
    ...pose.rootPosition,
    y: pose.rootPosition.y + delta,
  };
  return pose;
}

/**
 * Place a root-translated body so a static equipment-locked arm reaches its
 * fixed socket at the elbow flexion already authored by the exercise's
 * jointTargets. This turns body size into root placement instead of relying on
 * one v3-specific world-space height.
 *
 * The fit adjusts only root Y. X/Z path, equipment, pole targets and joint
 * standards stay authored. Exercises without static arm equipment locks are
 * untouched.
 */
function fitEquipmentLockedArmRoot(
  skeleton: Skeleton,
  exercise: ExerciseDefinition,
  pose: Pose,
  end: 'start' | 'peak',
): Pose {
  const armLocks = exercise.locks.filter(
    (lock) =>
      lock.enabled &&
      lock.mode === 'equipment' &&
      lock.chain.startsWith('arm') &&
      lock.equipmentId &&
      lock.socket,
  );
  if (armLocks.length === 0) return pose;

  const evaluation = new PoseEvaluation(skeleton).apply(pose);
  const transforms = resolveEquipment(evaluation, exercise.equipment.instances);
  const resolveSocket = socketResolver(exercise.equipment.instances, transforms);
  const deltas: number[] = [];

  for (const lock of armLocks) {
    if (!lock.equipmentId || !lock.socket) continue;
    const chain = IK_CHAINS[lock.chain];
    const target = resolveSocket(lock.equipmentId, lock.socket);
    if (!target) continue;

    const authored = exercise.jointTargets.find(
      (entry) => entry.bone === chain.mid && entry.axis === 'x',
    );
    if (!authored) continue;
    const flexionDegrees = end === 'start' ? authored.start : authored.peak;
    const flexion = Math.abs(toRad(flexionDegrees));
    const upper = skeleton.bone(chain.root).length;
    const lower = skeleton.bone(chain.mid).length;
    const desiredReach = Math.sqrt(
      upper * upper +
      lower * lower +
      2 * upper * lower * Math.cos(flexion),
    );

    const shoulder = evaluation.head(chain.root);
    const dx = target.position.x - shoulder.x;
    const dz = target.position.z - shoulder.z;
    const verticalSquared = desiredReach * desiredReach - dx * dx - dz * dz;
    if (verticalSquared <= 0) continue;

    // Equipment-locked overhead grips sit above the shoulder in the supported
    // family; preserve that branch of the geometric solution.
    const desiredShoulderY = target.position.y - Math.sqrt(verticalSquared);
    deltas.push(desiredShoulderY - shoulder.y);
  }

  if (deltas.length === 0) return pose;
  const delta = deltas.reduce((sum, value) => sum + value, 0) / deltas.length;
  if (!Number.isFinite(delta) || Math.abs(delta) < 1e-9) return pose;
  pose.rootPosition = {
    ...pose.rootPosition,
    y: pose.rootPosition.y + delta,
  };
  return pose;
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

function ikFromSpecForSkeleton(
  skeleton: Skeleton,
  exercise: ExerciseDefinition,
  spec: PoseSpec,
  end: 'start' | 'peak',
  activePose: Pose,
): Partial<Record<IKChainId, KeyframeIK>> {
  const out: Partial<Record<IKChainId, KeyframeIK>> = {};
  const hasArmIK = Object.entries(spec.ik ?? {}).some(
    ([chain, value]) => Boolean(value) && chain.startsWith('arm'),
  );

  let referenceEvaluation: PoseEvaluation | null = null;
  let activeEvaluation: PoseEvaluation | null = null;
  if (hasArmIK) {
    const referencePose = buildPose(canonicalSkeleton, exercise, spec, end);
    referenceEvaluation = new PoseEvaluation(canonicalSkeleton).apply(referencePose);
    activeEvaluation = new PoseEvaluation(skeleton).apply(activePose);
  }

  for (const [chain, value] of Object.entries(spec.ik ?? {})) {
    if (!value) continue;
    const chainId = chain as IKChainId;
    let target = { ...value.target };
    let pole = { ...value.pole };

    if (
      chainId.startsWith('arm') &&
      referenceEvaluation &&
      activeEvaluation
    ) {
      const fitted = armIKForSkeleton(
        skeleton,
        chainId,
        target,
        pole,
        referenceEvaluation,
        activeEvaluation,
      );
      target = fitted.target;
      pole = fitted.pole;
    }

    out[chainId] = {
      enabled: true,
      target,
      pole,
      ...(value.aim ? { aim: structuredClone(value.aim) } : {}),
      ...(value.onBall ? { onBall: { ...value.onBall } } : {}),
    };
  }
  return out;
}

/**
 * Arm IK targets are authored in the reference rig's world frame. Preserve
 * their actual biomechanics on a compatible rig by keeping the shoulder-to-
 * wrist direction and elbow flexion, then solving that same flexion against the
 * active upper-arm and forearm lengths. The pole is translated/scaled from the
 * shoulder by the same total-arm ratio so the elbow plane remains authored.
 *
 * The canonical/reference rig is mathematically unchanged by this mapping.
 */
function armIKForSkeleton(
  skeleton: Skeleton,
  chainId: IKChainId,
  target: Vec3,
  pole: Vec3,
  referenceEvaluation: PoseEvaluation,
  activeEvaluation: PoseEvaluation,
): { target: Vec3; pole: Vec3 } {
  const chain = IK_CHAINS[chainId];
  const referenceShoulder = referenceEvaluation.head(chain.root);
  const activeShoulder = activeEvaluation.head(chain.root);

  const direction = new HgVec3(
    target.x - referenceShoulder.x,
    target.y - referenceShoulder.y,
    target.z - referenceShoulder.z,
  );
  const referenceDistance = direction.length();
  if (referenceDistance < 1e-9) return { target: { ...target }, pole: { ...pole } };

  const referenceUpper = canonicalSkeleton.bone(chain.root).length;
  const referenceLower = canonicalSkeleton.bone(chain.mid).length;
  const activeUpper = skeleton.bone(chain.root).length;
  const activeLower = skeleton.bone(chain.mid).length;

  const cosine = Math.max(
    -1,
    Math.min(
      1,
      (
        referenceDistance * referenceDistance -
        referenceUpper * referenceUpper -
        referenceLower * referenceLower
      ) / (2 * referenceUpper * referenceLower),
    ),
  );
  const activeDistance = Math.sqrt(
    activeUpper * activeUpper +
    activeLower * activeLower +
    2 * activeUpper * activeLower * cosine,
  );
  direction.multiplyScalar(activeDistance / referenceDistance);

  const armScale =
    (activeUpper + activeLower) /
    (referenceUpper + referenceLower);
  const poleOffset = new HgVec3(
    pole.x - referenceShoulder.x,
    pole.y - referenceShoulder.y,
    pole.z - referenceShoulder.z,
  ).multiplyScalar(armScale);

  return {
    target: {
      x: activeShoulder.x + direction.x,
      y: activeShoulder.y + direction.y,
      z: activeShoulder.z + direction.z,
    },
    pole: {
      x: activeShoulder.x + poleOffset.x,
      y: activeShoulder.y + poleOffset.y,
      z: activeShoulder.z + poleOffset.z,
    },
  };
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
