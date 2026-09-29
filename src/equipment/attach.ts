import { HgMat4, HgQuat, HgVec3 } from '../core/linearMath';
import type { PoseEvaluation } from '../rig/skeleton';
import type { Vec3 } from '../rig/types';
import { toRad } from '../core/math';
import type { EquipmentInstance } from './types';
import { equipmentSocketForInstance } from './library';
import type { SocketTransform } from '../constraints/locks';

export interface EquipmentTransform {
  id: string;
  position: HgVec3;
  quaternion: HgQuat;
  matrix: HgMat4;
  /**
   * Set only on a cable, which is the one item that changes size: it is
   * stretched along its own Y to the length between its two ends. `matrix`
   * includes it; everything else is rigid and leaves it out.
   */
  scale?: HgVec3;
}

interface MatrixLike {
  readonly elements: ArrayLike<number>;
}

const UNIT = new HgVec3(1, 1, 1);
const Y_AXIS = new HgVec3(0, 1, 0);
const Z_AXIS = new HgVec3(0, 0, 1);

const copyMatrix = (source: MatrixLike, target = new HgMat4()): HgMat4 => {
  for (let index = 0; index < 16; index += 1) target.elements[index] = source.elements[index];
  return target;
};

const quaternionFromUnitVectors = (from: HgVec3, to: HgVec3): HgQuat => {
  let w = from.dot(to) + 1;
  const quaternion = new HgQuat();
  if (w < 1e-12) {
    w = 0;
    if (Math.abs(from.x) > Math.abs(from.z)) {
      quaternion.set(-from.y, from.x, 0, w);
    } else {
      quaternion.set(0, -from.z, from.y, w);
    }
  } else {
    const cross = new HgVec3().crossVectors(from, to);
    quaternion.set(cross.x, cross.y, cross.z, w);
  }
  return quaternion.normalize();
};

const authoredQuaternion = (rotation?: Vec3): HgQuat =>
  new HgQuat().setFromEulerXZY(
    toRad(rotation?.x ?? 0),
    toRad(rotation?.y ?? 0),
    toRad(rotation?.z ?? 0),
  );

const rigidTransform = (id: string, matrix: HgMat4): EquipmentTransform => ({
  id,
  position: new HgVec3().setFromMatrixPosition(matrix),
  quaternion: new HgQuat().setFromRotationMatrix(matrix),
  matrix,
});

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
    if (instance.attachment.mode === 'cable') continue;
    const transform = resolveInstance(evaluation, instance);
    if (transform) out.set(instance.id, transform);
  }
  // Cables last: each hangs between two items placed above.
  const byId = new Map(instances.map((instance) => [instance.id, instance]));
  for (const instance of instances) {
    if (instance.attachment.mode !== 'cable') continue;
    const end = (link: { equipment: string; socket: string }) => {
      const item = byId.get(link.equipment);
      const placed = out.get(link.equipment);
      return item && placed ? socketWorldPoint(item, link.socket, placed.matrix) : null;
    };
    const from = end(instance.attachment.from);
    const to = end(instance.attachment.to);
    if (!from || !to) continue;
    out.set(instance.id, { id: instance.id, ...cableMatrix(from, to) });
  }
  return out;
}

/** Where one item's socket is, given the matrix that places the item. */
export function socketWorldPoint(
  instance: EquipmentInstance,
  socketId: string,
  placement: MatrixLike,
): HgVec3 | null {
  const socket = equipmentSocketForInstance(instance, socketId);
  if (!socket) return null;
  return new HgVec3(socket.position.x, socket.position.y, socket.position.z)
    .applyMatrix4(copyMatrix(placement));
}

/**
 * Place a cable from `from` to `to`: at `from`, its +Y turned onto the line
 * between them, and stretched along Y to their distance.
 */
export function cableMatrix(
  from: Vec3,
  to: Vec3,
): { position: HgVec3; quaternion: HgQuat; scale: HgVec3; matrix: HgMat4 } {
  const position = new HgVec3(from.x, from.y, from.z);
  const along = new HgVec3(to.x - from.x, to.y - from.y, to.z - from.z);
  const length = along.length();
  const quaternion =
    length > 1e-9
      ? quaternionFromUnitVectors(Y_AXIS, along.multiplyScalar(1 / length))
      : new HgQuat();
  const scale = new HgVec3(1, Math.max(length, 1e-6), 1);
  return {
    position,
    quaternion,
    scale,
    matrix: new HgMat4().compose(position, quaternion, scale),
  };
}

function resolveInstance(
  evaluation: PoseEvaluation,
  instance: EquipmentInstance,
): EquipmentTransform | null {
  const attachment = instance.attachment;

  if (attachment.mode === 'static') {
    const quaternion = authoredQuaternion(instance.rotation);
    const position = new HgVec3(instance.position.x, instance.position.y, instance.position.z);
    return {
      id: instance.id,
      position,
      quaternion,
      matrix: new HgMat4().compose(position, quaternion, UNIT),
    };
  }

  if (attachment.mode === 'hand') {
    const hand = attachment.side === 'l' ? 'hand_l' : 'hand_r';
    const grip = attachment.gripOffset ?? anatomicalGripOffset(attachment.side);
    const gripMatrix = new HgMat4().compose(
      new HgVec3(grip.x, grip.y, grip.z),
      authoredQuaternion(attachment.gripRotation),
      UNIT,
    );
    const matrix = evaluation.firstPartyEvaluation.matrix(hand).clone().multiply(gripMatrix);

    // The equipment socket itself — position and orientation — is what meets
    // the calibrated hand frame. Inverting the full socket transform keeps the
    // contact point fixed while allowing the handle to rotate in the palm.
    const socketLocal = equipmentSocketForInstance(instance, attachment.socket);
    if (socketLocal) {
      const socketMatrix = new HgMat4().compose(
        new HgVec3(socketLocal.position.x, socketLocal.position.y, socketLocal.position.z),
        authoredQuaternion(socketLocal.rotation),
        UNIT,
      );
      matrix.multiply(socketMatrix.invert());
    }
    return rigidTransform(instance.id, matrix);
  }

  const matrix = twoHandAttachmentMatrix(
    evaluation.firstPartyEvaluation.matrix('hand_l'),
    evaluation.firstPartyEvaluation.matrix('hand_r'),
    instance,
  );
  return matrix ? rigidTransform(instance.id, matrix) : null;
}

/** Hand-local targets used by a rigid two-hand attachment. */
export function twoHandGripOffsets(instance: EquipmentInstance): {
  left: { x: number; y: number; z: number };
  right: { x: number; y: number; z: number };
} | null {
  if (instance.attachment.mode !== 'hands') return null;
  const shared = instance.attachment.gripOffset;
  return {
    left: instance.attachment.leftGripOffset ?? shared ?? anatomicalGripOffset('l'),
    right: instance.attachment.rightGripOffset ?? shared ?? anatomicalGripOffset('r'),
  };
}

/**
 * Fit one rigid two-hand equipment instance from its actual authored grip
 * sockets to the two hand-local grip targets.
 */
export function twoHandAttachmentMatrix(
  leftHand: MatrixLike,
  rightHand: MatrixLike,
  instance: EquipmentInstance,
): HgMat4 | null {
  if (instance.attachment.mode !== 'hands') return null;
  const offsets = twoHandGripOffsets(instance);
  if (!offsets) return null;
  const leftSocket = equipmentSocketForInstance(instance, instance.attachment.leftSocket);
  const rightSocket = equipmentSocketForInstance(instance, instance.attachment.rightSocket);
  if (!leftSocket || !rightSocket) return null;

  const leftTarget = new HgVec3(offsets.left.x, offsets.left.y, offsets.left.z)
    .applyMatrix4(copyMatrix(leftHand));
  const rightTarget = new HgVec3(offsets.right.x, offsets.right.y, offsets.right.z)
    .applyMatrix4(copyMatrix(rightHand));
  const worldAxis = new HgVec3().subVectors(rightTarget, leftTarget);
  const localAxis = new HgVec3(
    rightSocket.position.x - leftSocket.position.x,
    rightSocket.position.y - leftSocket.position.y,
    rightSocket.position.z - leftSocket.position.z,
  );
  if (worldAxis.lengthSq() < 1e-8 || localAxis.lengthSq() < 1e-8) return null;
  worldAxis.normalize();
  localAxis.normalize();

  const basisFor = (axis: HgVec3, preferredUp: HgVec3) => {
    const up = preferredUp.clone().addScaledVector(axis, -preferredUp.dot(axis));
    if (up.lengthSq() < 1e-8) {
      up.set(1, 0, 0).addScaledVector(axis, -axis.x);
    }
    up.normalize();
    const side = new HgVec3().crossVectors(up, axis).normalize();
    return new HgMat4().makeBasis(side, up, axis);
  };

  const localQ = new HgQuat().setFromRotationMatrix(basisFor(localAxis, Y_AXIS));
  const worldQ = new HgQuat().setFromRotationMatrix(basisFor(worldAxis, Y_AXIS));
  const quaternion = worldQ.multiply(localQ.invert());
  const roll = instance.attachment.gripRoll ?? 0;
  if (Math.abs(roll) > 1e-9) {
    quaternion.premultiply(new HgQuat().setFromAxisAngle(worldAxis, toRad(roll)));
  }

  const localMid = new HgVec3(
    (leftSocket.position.x + rightSocket.position.x) / 2,
    (leftSocket.position.y + rightSocket.position.y) / 2,
    (leftSocket.position.z + rightSocket.position.z) / 2,
  );
  const worldMid = leftTarget.clone().add(rightTarget).multiplyScalar(0.5);
  const rotatedLocalMid = localMid.clone().applyQuaternion(quaternion);
  const position = worldMid.sub(rotatedLocalMid);
  return new HgMat4().compose(position, quaternion, UNIT);
}

/**
 * Centre of a cylindrical handle inside the curled fingers, in hand-local
 * coordinates. The palm-facing axis is mirrored between hands.
 */
export function anatomicalGripOffset(side: 'l' | 'r'): { x: number; y: number; z: number } {
  return { x: side === 'l' ? -0.025 : 0.025, y: 0.085, z: 0 };
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

    const position = new HgVec3(local.position.x, local.position.y, local.position.z)
      .applyMatrix4(transform.matrix);
    const quaternion = transform.quaternion.clone().multiply(authoredQuaternion(local.rotation));
    return { position, quaternion };
  };
}

/** Direction a socket's grip axis points in world space, for UI readouts. */
export function socketAxes(transform: SocketTransform): { up: HgVec3; forward: HgVec3 } {
  const quaternion = new HgQuat().set(
    transform.quaternion.x,
    transform.quaternion.y,
    transform.quaternion.z,
    transform.quaternion.w,
  );
  return {
    up: Y_AXIS.clone().applyQuaternion(quaternion),
    forward: Z_AXIS.clone().applyQuaternion(quaternion),
  };
}
