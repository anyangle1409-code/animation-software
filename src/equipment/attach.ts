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

  const matrix = twoHandAttachmentMatrix(
    evaluation.matrix('hand_l'),
    evaluation.matrix('hand_r'),
    instance,
  );
  return matrix ? decompose(instance.id, matrix) : null;
}


/** Hand-local targets used by a rigid two-hand attachment. */
export function twoHandGripOffsets(instance: EquipmentInstance): {
  left: { x: number; y: number; z: number };
  right: { x: number; y: number; z: number };
} | null {
  if (instance.attachment.mode !== 'hands') return null;
  // Per side, so the mirrored palm axis is respected rather than both hands
  // taking one shared offset.
  const shared = instance.attachment.gripOffset;
  return {
    left: instance.attachment.leftGripOffset ?? shared ?? anatomicalGripOffset('l'),
    right: instance.attachment.rightGripOffset ?? shared ?? anatomicalGripOffset('r'),
  };
}

/**
 * Fit one rigid two-hand equipment instance from its actual authored grip
 * sockets to the two hand-local grip targets. The midpoint and socket axis are
 * matched exactly; if socket separation differs from hand separation the
 * residual is reported by the grip diagnostics rather than being hidden by
 * wrist/arm compensation or non-rigid scaling.
 */
export function twoHandAttachmentMatrix(
  leftHand: Matrix4,
  rightHand: Matrix4,
  instance: EquipmentInstance,
): Matrix4 | null {
  if (instance.attachment.mode !== 'hands') return null;
  const offsets = twoHandGripOffsets(instance);
  if (!offsets) return null;
  const leftSocket = equipmentSocketForInstance(instance, instance.attachment.leftSocket);
  const rightSocket = equipmentSocketForInstance(instance, instance.attachment.rightSocket);
  if (!leftSocket || !rightSocket) return null;

  const leftTarget = new Vector3(offsets.left.x, offsets.left.y, offsets.left.z).applyMatrix4(leftHand);
  const rightTarget = new Vector3(offsets.right.x, offsets.right.y, offsets.right.z).applyMatrix4(rightHand);
  const worldAxis = new Vector3().subVectors(rightTarget, leftTarget);
  const localAxis = new Vector3(
    rightSocket.position.x - leftSocket.position.x,
    rightSocket.position.y - leftSocket.position.y,
    rightSocket.position.z - leftSocket.position.z,
  );
  if (worldAxis.lengthSq() < 1e-8 || localAxis.lengthSq() < 1e-8) return null;
  worldAxis.normalize();
  localAxis.normalize();

  const basisFor = (axis: Vector3, preferredUp: Vector3) => {
    const up = preferredUp.clone().addScaledVector(axis, -preferredUp.dot(axis));
    if (up.lengthSq() < 1e-8) {
      up.set(1, 0, 0).addScaledVector(axis, -axis.x);
    }
    up.normalize();
    const side = new Vector3().crossVectors(up, axis).normalize();
    return new Matrix4().makeBasis(side, up, axis);
  };

  const localBasis = basisFor(localAxis, Y_AXIS);
  const worldBasis = basisFor(worldAxis, Y_AXIS);
  const localQ = new Quaternion().setFromRotationMatrix(localBasis);
  const worldQ = new Quaternion().setFromRotationMatrix(worldBasis);
  const quaternion = worldQ.multiply(localQ.invert());
  const roll = instance.attachment.gripRoll ?? 0;
  if (Math.abs(roll) > 1e-9) {
    quaternion.premultiply(
      new Quaternion().setFromAxisAngle(worldAxis, toRad(roll)),
    );
  }

  const localMid = new Vector3(
    (leftSocket.position.x + rightSocket.position.x) / 2,
    (leftSocket.position.y + rightSocket.position.y) / 2,
    (leftSocket.position.z + rightSocket.position.z) / 2,
  );
  const worldMid = leftTarget.clone().add(rightTarget).multiplyScalar(0.5);
  const rotatedLocalMid = localMid.clone().applyQuaternion(quaternion);
  const position = worldMid.sub(rotatedLocalMid);
  return new Matrix4().compose(position, quaternion, UNIT);
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
