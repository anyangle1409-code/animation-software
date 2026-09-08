import { Euler, Matrix4, Quaternion, Vector3 } from 'three';
import type { PoseEvaluation } from '../rig/skeleton';
import type { BoneName } from '../rig/boneNames';
import { EULER_ORDER } from '../rig/types';
import { toRad } from '../core/math';
import type { EquipmentInstance } from './types';
import { equipmentSocket } from './library';
import type { SocketTransform } from '../constraints/locks';
import type { RetargetBinding } from '../retargeting/retarget';
import { retargetedBoneMatrix } from '../retargeting/retarget';

export interface EquipmentTransform {
  id: string;
  position: Vector3;
  quaternion: Quaternion;
  matrix: Matrix4;
}

const UNIT = new Vector3(1, 1, 1);
const Y_AXIS = new Vector3(0, 1, 0);
const Z_AXIS = new Vector3(0, 0, 1);

/**
 * Where each piece of equipment sits for the current pose.
 *
 * Attachment is rigid, not a follow: a hand-held item takes the hand bone's
 * frame directly, and a two-handed bar is placed on the line between the grips
 * so it stays straight and moves symmetrically however the arms are solved.
 */
export function resolveEquipment(
  evaluation: PoseEvaluation,
  instances: EquipmentInstance[],
): Map<string, EquipmentTransform> {
  return resolveWithHands(
    instances,
    (bone) => evaluation.matrix(bone),
    (bone, point, target) => evaluation.localToWorld(bone, point, target),
  );
}

/** Resolve equipment from the hands of an imported, retargeted character. */
export function resolveRetargetedEquipment(
  binding: RetargetBinding,
  instances: EquipmentInstance[],
): Map<string, EquipmentTransform> {
  return resolveWithHands(
    instances,
    (bone) => retargetedBoneMatrix(binding, bone),
    (bone, point, target) => {
      const matrix = retargetedBoneMatrix(binding, bone);
      return matrix ? target.set(point.x, point.y, point.z).applyMatrix4(matrix) : null;
    },
  );
}

type HandMatrix = (bone: BoneName) => Matrix4 | null;
type HandPoint = (bone: BoneName, point: { x: number; y: number; z: number }, target: Vector3) => Vector3 | null;

function resolveWithHands(
  instances: EquipmentInstance[],
  handMatrix: HandMatrix,
  handPoint: HandPoint,
): Map<string, EquipmentTransform> {
  const out = new Map<string, EquipmentTransform>();
  for (const instance of instances) {
    const transform = resolveInstance(instance, handMatrix, handPoint);
    if (transform) out.set(instance.id, transform);
  }
  return out;
}

function resolveInstance(
  instance: EquipmentInstance,
  handMatrix: HandMatrix,
  handPoint: HandPoint,
): EquipmentTransform | null {
  const attachment = instance.attachment;

  if (attachment.mode === 'static') {
    const quaternion = new Quaternion().setFromEuler(
      new Euler(
        toRad(instance.rotation.x),
        toRad(instance.rotation.y),
        toRad(instance.rotation.z),
        EULER_ORDER,
      ),
    );
    const position = new Vector3(instance.position.x, instance.position.y, instance.position.z);
    return {
      id: instance.id,
      position,
      quaternion,
      matrix: new Matrix4().compose(position, quaternion, UNIT),
    };
  }

  if (attachment.mode === 'hand') {
    const hand: BoneName = attachment.side === 'l' ? 'hand_l' : 'hand_r';
    const grip = attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };
    const resolvedHand = handMatrix(hand);
    if (!resolvedHand) return null;
    const matrix = new Matrix4()
      .copy(resolvedHand)
      .multiply(new Matrix4().makeTranslation(grip.x, grip.y, grip.z));
    // The socket sits at the grip, so the item's own origin is offset back by it.
    const socketLocal = equipmentSocket(instance.kind, attachment.socket);
    if (socketLocal) {
      matrix.multiply(
        new Matrix4().makeTranslation(
          -socketLocal.position.x,
          -socketLocal.position.y,
          -socketLocal.position.z,
        ),
      );
    }
    return decompose(instance.id, matrix);
  }

  // Two-handed: the bar spans the two grips.
  const grip = attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };
  const left = handPoint('hand_l', grip, new Vector3());
  const right = handPoint('hand_r', grip, new Vector3());
  if (!left || !right) return null;
  const axis = new Vector3().subVectors(right, left);
  if (axis.lengthSq() < 1e-8) return null;
  axis.normalize();

  // Keep the bar level: its local +Y stays as close to world up as the grip allows.
  const up = new Vector3(0, 1, 0).addScaledVector(axis, -axis.y);
  if (up.lengthSq() < 1e-8) up.set(0, 0, 1).addScaledVector(axis, -axis.z);
  up.normalize();
  const side = new Vector3().crossVectors(up, axis).normalize();

  const quaternion = new Quaternion().setFromRotationMatrix(
    new Matrix4().makeBasis(side, up, axis),
  );
  const centre = left.clone().add(right).multiplyScalar(0.5);
  const position = centre;
  return {
    id: instance.id,
    position,
    quaternion,
    matrix: new Matrix4().compose(position, quaternion, UNIT),
  };
}

function decompose(id: string, matrix: Matrix4): EquipmentTransform {
  const position = new Vector3();
  const quaternion = new Quaternion();
  matrix.decompose(position, quaternion, new Vector3());
  return { id, position, quaternion, matrix };
}

/**
 * Socket resolver for the constraint layer: converts an equipment id and socket
 * name into the world transform a locked hand should adopt.
 */
export function socketResolver(
  instances: EquipmentInstance[],
  transforms: Map<string, EquipmentTransform>,
): (equipmentId: string, socketId: string) => SocketTransform | null {
  const byId = new Map(instances.map((instance) => [instance.id, instance]));
  return (equipmentId, socketId) => {
    const instance = byId.get(equipmentId);
    const transform = transforms.get(equipmentId);
    if (!instance || !transform) return null;
    const local = equipmentSocket(instance.kind, socketId);
    if (!local) return null;

    const localMatrix = new Matrix4().compose(
      new Vector3(local.position.x, local.position.y, local.position.z),
      new Quaternion().setFromEuler(
        new Euler(
          toRad(local.rotation?.x ?? 0),
          toRad(local.rotation?.y ?? 0),
          toRad(local.rotation?.z ?? 0),
          EULER_ORDER,
        ),
      ),
      UNIT,
    );
    const world = new Matrix4().multiplyMatrices(transform.matrix, localMatrix);
    const position = new Vector3();
    const quaternion = new Quaternion();
    world.decompose(position, quaternion, new Vector3());
    return { position, quaternion };
  };
}

/** Direction a socket's grip axis points in world space, for UI readouts. */
export function socketAxes(transform: SocketTransform): { up: Vector3; forward: Vector3 } {
  return {
    up: Y_AXIS.clone().applyQuaternion(transform.quaternion),
    forward: Z_AXIS.clone().applyQuaternion(transform.quaternion),
  };
}
