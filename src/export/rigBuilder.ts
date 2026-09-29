import type { EquipmentKind } from '../equipment/types';
import {
  buildThreeEquipmentObject,
  composeThreeEquipmentMatrix,
  type EquipmentThreeEuler,
  type EquipmentThreeMatrix4,
  type EquipmentThreeObject,
  type EquipmentThreeVector3,
} from '../equipment/threeGeometryBoundary';

/**
 * The character itself lives in `body/`, because the viewport builds the same
 * mesh from the same profiles — what the studio shows is what the file holds.
 */
export { buildSkinnedRig, MANNEQUIN_NAME } from '../body/skin';
export type { BuiltRig } from '../body/skin';

/** Build a plain temporary Three object for the remaining legacy export path. */
export function buildEquipmentObject(
  kind: EquipmentKind,
  backAngle?: number,
): EquipmentThreeObject {
  return buildThreeEquipmentObject(kind, backAngle);
}

export const composeMatrix = (
  position: EquipmentThreeVector3,
  rotation: EquipmentThreeEuler,
  target?: EquipmentThreeMatrix4,
): EquipmentThreeMatrix4 => composeThreeEquipmentMatrix(position, rotation, target);
