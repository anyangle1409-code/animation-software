import { Vector3 } from 'three';
import type { BoneName, Side } from '../rig/boneNames';
import type { PoseEvaluation } from '../rig/skeleton';
import { twoHandGripOffsets, type EquipmentTransform } from './attach';
import type { EquipmentInstance } from './types';
import { equipmentSocketForInstance } from './library';

interface GripContactPoint {
  bone: BoneName;
  along: number;
  reach: number;
}

export interface GripFitMeasurement {
  side: Side;
  /** Largest measured distance as a fraction of that contact's allowed reach. */
  reachUse: number;
  /** Largest angular opening between neighbouring contacts around the handle. */
  widestGapDeg: number;
  /** Complement of the widest gap; useful as an intuitive wrap readout. */
  wrapCoverageDeg: number;
  /** Same geometric envelope used by the established grip regression tests. */
  withinEnvelope: boolean;
}

export const GRIP_CLOSURE_PRESETS = [
  { id: 'loose', label: 'Loose', closure: 0.7 },
  { id: 'training', label: 'Training', closure: 0.85 },
  { id: 'closed', label: 'Closed', closure: 1 },
] as const;

export const gripContactPoints = (side: Side): GripContactPoint[] => [
  { bone: `index_02_${side}` as BoneName, along: 0.5, reach: 0.032 },
  { bone: `index_03_${side}` as BoneName, along: 1, reach: 0.04 },
  { bone: `middle_02_${side}` as BoneName, along: 0.5, reach: 0.032 },
  { bone: `middle_03_${side}` as BoneName, along: 1, reach: 0.04 },
  { bone: `ring_02_${side}` as BoneName, along: 0.5, reach: 0.034 },
  { bone: `pinky_02_${side}` as BoneName, along: 0.5, reach: 0.038 },
  { bone: `thumb_02_${side}` as BoneName, along: 0.5, reach: 0.042 },
  { bone: `thumb_03_${side}` as BoneName, along: 1, reach: 0.032 },
];

const pointOf = (evaluation: PoseEvaluation, bone: BoneName, along: number): Vector3 =>
  along >= 1 ? evaluation.tail(bone, new Vector3()) : evaluation.head(bone, new Vector3());

/**
 * Measure how the authored fingers surround a cylindrical hand-held handle.
 * This is a geometric authoring diagnostic, not a safety or force model.
 */
export function measureGripFit(
  evaluation: PoseEvaluation,
  equipment: EquipmentTransform,
  side: Side,
): GripFitMeasurement {
  const handle = equipment.position;
  const axis = new Vector3(0, 0, 1).applyQuaternion(equipment.quaternion).normalize();
  const up = new Vector3(0, 1, 0).addScaledVector(axis, -axis.y);
  if (up.lengthSq() < 1e-10) up.set(1, 0, 0).addScaledVector(axis, -axis.x);
  up.normalize();
  const across = new Vector3().crossVectors(up, axis).normalize();

  let reachUse = 0;
  const angles: number[] = [];
  for (const point of gripContactPoints(side)) {
    const offset = pointOf(evaluation, point.bone, point.along).sub(handle);
    offset.addScaledVector(axis, -offset.dot(axis));
    reachUse = Math.max(reachUse, offset.length() / point.reach);
    angles.push(Math.atan2(offset.dot(up), offset.dot(across)));
  }

  angles.sort((a, b) => a - b);
  let widest = angles[0] + Math.PI * 2 - angles[angles.length - 1];
  for (let index = 1; index < angles.length; index += 1) {
    widest = Math.max(widest, angles[index] - angles[index - 1]);
  }
  const widestGapDeg = (widest * 180) / Math.PI;
  return {
    side,
    reachUse,
    widestGapDeg,
    wrapCoverageDeg: 360 - widestGapDeg,
    withinEnvelope: reachUse < 1 && widestGapDeg < 170,
  };
}


export interface TwoHandFitMeasurement {
  leftError: number;
  rightError: number;
  targetSeparation: number;
  socketSeparation: number;
  separationError: number;
  withinEnvelope: boolean;
}

/**
 * Measure positional fit of a rigid two-hand item at the current frame. A
 * spacing mismatch is deliberately visible: the solver never scales the bar or
 * moves the wrists to hide it.
 */
export function measureTwoHandFit(
  evaluation: PoseEvaluation,
  instance: EquipmentInstance,
  equipment: EquipmentTransform,
): TwoHandFitMeasurement | null {
  if (instance.attachment.mode !== 'hands') return null;
  const offsets = twoHandGripOffsets(instance);
  const leftSocket = equipmentSocketForInstance(instance, instance.attachment.leftSocket);
  const rightSocket = equipmentSocketForInstance(instance, instance.attachment.rightSocket);
  if (!offsets || !leftSocket || !rightSocket) return null;

  const leftTarget = evaluation.localToWorld('hand_l', offsets.left, new Vector3());
  const rightTarget = evaluation.localToWorld('hand_r', offsets.right, new Vector3());
  const leftActual = new Vector3(
    leftSocket.position.x,
    leftSocket.position.y,
    leftSocket.position.z,
  ).applyMatrix4(equipment.matrix);
  const rightActual = new Vector3(
    rightSocket.position.x,
    rightSocket.position.y,
    rightSocket.position.z,
  ).applyMatrix4(equipment.matrix);
  const targetSeparation = leftTarget.distanceTo(rightTarget);
  const socketSeparation = leftActual.distanceTo(rightActual);
  const leftError = leftActual.distanceTo(leftTarget);
  const rightError = rightActual.distanceTo(rightTarget);
  return {
    leftError,
    rightError,
    targetSeparation,
    socketSeparation,
    separationError: socketSeparation - targetSeparation,
    withinEnvelope: Math.max(leftError, rightError) <= 0.005,
  };
}
