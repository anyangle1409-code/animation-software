import { Euler, Matrix4, Quaternion, Vector3 } from 'three';
import type { PoseEvaluation } from '../rig/skeleton';
import { EULER_ORDER } from '../rig/types';
import { toRad } from '../core/math';
import type { EquipmentInstance } from './types';
import { equipmentSocketForInstance } from './library';
import type { SocketTransform } from '../constraints/locks';

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
  const out = new Map<string, EquipmentTransform>();
  for (const instance of instances) {
    const transform = resolveInstance(evaluation, instance);
    if (transform) out.set(instance.id, transform);
  }
  return out;
}

function resolveInstance(
  evaluation: PoseEvaluation,
  instance: EquipmentInstance,
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
    const hand = attachment.side === 'l' ? 'hand_l' : 'hand_r';
    const grip = attachment.gripOffset ?? anatomicalGripOffset(attachment.side);
    const gripQuaternion = new Quaternion().setFromEuler(
      new Euler(
        toRad(attachment.gripRotation?.x ?? 0),
        toRad(attachment.gripRotation?.y ?? 0),
        toRad(attachment.gripRotation?.z ?? 0),
        EULER_ORDER,
      ),
    );
    const gripMatrix = new Matrix4().compose(
      new Vector3(grip.x, grip.y, grip.z),
      gripQuaternion,
      UNIT,
    );
    const matrix = new Matrix4().copy(evaluation.matrix(hand)).multiply(gripMatrix);
    // The equipment socket itself — position and orientation — is what meets
    // the calibrated hand frame. Inverting the full socket transform keeps the
    // contact point fixed while allowing the handle to rotate in the palm.
    const socketLocal = equipmentSocketForInstance(instance, attachment.socket);
    if (socketLocal) {
      const socketMatrix = new Matrix4().compose(
        new Vector3(socketLocal.position.x, socketLocal.position.y, socketLocal.position.z),
        new Quaternion().setFromEuler(
          new Euler(
            toRad(socketLocal.rotation?.x ?? 0),
            toRad(socketLocal.rotation?.y ?? 0),
            toRad(socketLocal.rotation?.z ?? 0),
            EULER_ORDER,
          ),
        ),
        UNIT,
      );
      matrix.multiply(socketMatrix.invert());
    }
    return decompose(instance.id, matrix);
  }

  // Two-handed: the bar spans the two grips.
  const grip = attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };
  const left = evaluation.localToWorld('hand_l', grip, new Vector3());
  const right = evaluation.localToWorld('hand_r', grip, new Vector3());
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

/**
 * Centre of a cylindrical handle inside the curled fingers, in hand-local
 * coordinates. The palm-facing axis is mirrored between hands.
 */
export function anatomicalGripOffset(side: 'l' | 'r'): { x: number; y: number; z: number } {
  return { x: side === 'l' ? -0.025 : 0.025, y: 0.085, z: 0 };
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
    const local = equipmentSocketForInstance(instance, socketId);
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
