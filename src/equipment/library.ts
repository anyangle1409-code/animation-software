import { SHOULDER_WIDENING } from '../rig/humanoid';
import type { EquipmentDefinition, EquipmentInstance, EquipmentKind, EquipmentSocket } from './types';
import { vec3 } from '../rig/types';

/**
 * Equipment is authored in a frame that matches the hand's own bone frame:
 * a grip axis along local +Z (thumb towards +Z), the fingers wrapping around
 * local +Y. Attaching a hand to a socket then means making the two frames
 * agree, which is what keeps a dumbbell rigidly in the hand instead of
 * floating near it.
 */
const socket = (
  id: string,
  label: string,
  position: [number, number, number],
  kind: EquipmentSocket['kind'] = 'grip',
  rotation?: [number, number, number],
): EquipmentSocket => ({
  id,
  label,
  position: vec3(...position),
  kind,
  ...(rotation ? { rotation: vec3(...rotation) } : {}),
});

export const EQUIPMENT_LIBRARY: Record<EquipmentKind, EquipmentDefinition> = {
  dumbbell: {
    kind: 'dumbbell',
    label: 'Dumbbell',
    defaultMass: 10,
    paired: true,
    size: vec3(0.11, 0.11, 0.28),
    sockets: [socket('grip', 'Handle', [0, 0, 0])],
  },
  barbell: {
    kind: 'barbell',
    label: 'Barbell',
    defaultMass: 20,
    paired: false,
    size: vec3(0.46, 0.46, 2.2),
    sockets: [
      socket('grip_l', 'Left hand', [0, 0, -0.4]),
      socket('grip_r', 'Right hand', [0, 0, 0.4], 'grip', [0, 180, 0]),
      socket('grip_l_wide', 'Left hand (wide)', [0, 0, -0.55]),
      socket('grip_r_wide', 'Right hand (wide)', [0, 0, 0.55], 'grip', [0, 180, 0]),
      socket('grip_l_narrow', 'Left hand (narrow)', [0, 0, -0.22]),
      socket('grip_r_narrow', 'Right hand (narrow)', [0, 0, 0.22], 'grip', [0, 180, 0]),
      socket('centre', 'Bar centre', [0, 0, 0], 'mount'),
    ],
  },
  ez_curl_bar: {
    kind: 'ez_curl_bar',
    label: 'EZ curl bar',
    defaultMass: 10,
    paired: false,
    size: vec3(0.4, 0.16, 1.2),
    // The angled sections put the hands in a semi-supinated grip.
    sockets: [
      socket('grip_l', 'Left hand', [0, 0.03, -0.16], 'grip', [0, 0, -22]),
      socket('grip_r', 'Right hand', [0, 0.03, 0.16], 'grip', [0, 180, 22]),
      socket('centre', 'Bar centre', [0, 0, 0], 'mount'),
    ],
  },
  weight_plate: {
    kind: 'weight_plate',
    label: 'Weight plate',
    defaultMass: 20,
    paired: false,
    size: vec3(0.45, 0.45, 0.035),
    sockets: [
      socket('mount', 'Collar', [0, 0, 0], 'mount'),
      socket('grip', 'Rim grip', [0, 0.2, 0]),
    ],
  },
  flat_bench: {
    kind: 'flat_bench',
    label: 'Flat bench',
    defaultMass: 0,
    paired: false,
    size: vec3(0.32, 0.46, 1.25),
    sockets: [
      socket('back', 'Back support', [0, 0.46, 0.1], 'support'),
      socket('seat', 'Seat', [0, 0.46, -0.4], 'support'),
      socket('head', 'Head end', [0, 0.46, 0.5], 'support'),
    ],
  },
  incline_bench: {
    kind: 'incline_bench',
    label: 'Incline bench',
    defaultMass: 0,
    paired: false,
    size: vec3(0.32, 0.95, 1.25),
    sockets: [
      socket('back', 'Back support', [0, 0.691, 0.105], 'support', [-45, 0, 0]),
      socket('seat', 'Seat', [0, 0.395, -0.35], 'support'),
    ],
  },
  squat_rack: {
    kind: 'squat_rack',
    label: 'Squat rack',
    defaultMass: 0,
    paired: false,
    size: vec3(0.9, 2.1, 1.4),
    sockets: [
      socket('hooks', 'J-hooks', [0, 1.42, 0], 'mount'),
      socket('safety', 'Safety bars', [0, 0.85, 0], 'mount'),
      // The rack's top crossbar runs along world X, so its grips are turned a
      // quarter turn: +Z is the thumb direction, and both thumbs point inwards.
      // The grips sit 8 cm below the bar itself, because an arm chain solves for
      // the wrist and a hand wrapped over a bar carries it at the knuckles.
      // The grip spacing is shoulder-relative, not a fixed property of the
      // rack: the exercise asks for a grip "just wider than the shoulders", so
      // the sockets carry the Stage 2 shoulder widening. The bar is 1.3 m wide
      // with uprights at +/-0.62, so +/-0.274 is comfortably on it.
      socket('pullup_l', 'Pull-up bar (L)', [-(0.24 + SHOULDER_WIDENING), 1.97, 0], 'grip', [0, 90, 0]),
      socket('pullup_r', 'Pull-up bar (R)', [0.24 + SHOULDER_WIDENING, 1.97, 0], 'grip', [0, -90, 0]),
    ],
  },
  cable_handle: {
    kind: 'cable_handle',
    label: 'Cable handle',
    defaultMass: 1,
    paired: true,
    size: vec3(0.06, 0.16, 0.14),
    sockets: [
      socket('grip', 'Handle', [0, 0, 0]),
      socket('clip', 'Cable clip', [0, 0.11, 0], 'mount'),
      // Both hands on the one handle, fists interlocked one above the other.
      socket('grip_l', 'Upper hand', [0, 0, 0.0316]),
      socket('grip_r', 'Lower hand', [0, 0, -0.0316], 'grip', [0, 180, 0]),
    ],
  },
  cable_rope: {
    kind: 'cable_rope',
    label: 'Cable rope',
    defaultMass: 1,
    paired: false,
    size: vec3(0.1, 0.5, 0.3),
    sockets: [
      socket('grip_l', 'Left end', [0, 0, -0.08]),
      socket('grip_r', 'Right end', [0, 0, 0.08], 'grip', [0, 180, 0]),
      socket('clip', 'Cable clip', [0, 0.3, 0], 'mount'),
    ],
  },
  lat_pulldown_bar: {
    kind: 'lat_pulldown_bar',
    label: 'Lat pulldown bar',
    defaultMass: 3,
    paired: false,
    size: vec3(0.2, 0.24, 1.2),
    sockets: [
      socket('grip_l', 'Left hand', [0, -0.05, -0.48], 'grip', [0, 0, -28]),
      socket('grip_r', 'Right hand', [0, -0.05, 0.48], 'grip', [0, 180, 28]),
      socket('clip', 'Cable clip', [0, 0.06, 0], 'mount'),
    ],
  },
  resistance_band: {
    kind: 'resistance_band',
    label: 'Resistance band',
    defaultMass: 0,
    paired: false,
    size: vec3(0.06, 0.06, 1.0),
    sockets: [
      socket('grip_l', 'Left end', [0, 0, -0.45]),
      socket('grip_r', 'Right end', [0, 0, 0.45], 'grip', [0, 180, 0]),
      socket('anchor', 'Anchor', [0, 0, 0], 'mount'),
    ],
  },
  kettlebell: {
    kind: 'kettlebell',
    label: 'Kettlebell',
    defaultMass: 16,
    paired: true,
    size: vec3(0.22, 0.3, 0.22),
    sockets: [socket('grip', 'Handle', [0, 0, 0]), socket('base', 'Base', [0, -0.26, 0], 'mount')],
  },
  cable_tower: {
    kind: 'cable_tower',
    label: 'Cable tower',
    defaultMass: 0,
    paired: false,
    size: vec3(0.7, 2.3, 0.6),
    // The bottom of the high pulley's wheel, where the cable leaves it.
    sockets: [
      socket('pulley', 'High pulley', [0, 2.075, -0.14], 'mount'),
      // The front of the mid pulley's wheel, where a horizontal cable leaves it.
      socket('pulley_mid', 'Mid pulley', [0, 1.25, -0.015], 'mount'),
    ],
  },
  cable_bar: {
    kind: 'cable_bar',
    label: 'Straight cable bar',
    defaultMass: 2,
    paired: false,
    size: vec3(0.05, 0.1, 0.5),
    sockets: [
      socket('grip_l', 'Left hand', [0, 0, -0.2]),
      socket('grip_r', 'Right hand', [0, 0, 0.2], 'grip', [0, 180, 0]),
      socket('clip', 'Cable clip', [0, 0.079, 0], 'mount'),
    ],
  },
  cable: {
    kind: 'cable',
    label: 'Cable',
    defaultMass: 0,
    paired: false,
    size: vec3(0.01, 1, 0.01),
    sockets: [],
  },
};

export const EQUIPMENT_LIST = Object.values(EQUIPMENT_LIBRARY);

export function equipmentSocket(kind: EquipmentKind, socketId: string): EquipmentSocket | null {
  return EQUIPMENT_LIBRARY[kind].sockets.find((entry) => entry.id === socketId) ?? null;
}


/** Effective socket for one exercise equipment instance, including local overrides. */
export function equipmentSocketForInstance(
  instance: EquipmentInstance,
  socketId: string,
): EquipmentSocket | null {
  const base = equipmentSocket(instance.kind, socketId);
  if (!base) return null;
  const override = instance.socketOverrides?.[socketId];
  return {
    ...base,
    position: override?.position ? { ...override.position } : { ...base.position },
    ...(override?.rotation
      ? { rotation: { ...override.rotation } }
      : base.rotation
        ? { rotation: { ...base.rotation } }
        : {}),
  };
}


/**
 * Return a copy of a two-hand equipment instance with its two authored grip
 * sockets moved symmetrically to the requested separation. Passing null removes
 * only the positional calibration and restores the library socket positions;
 * any socket-rotation override remains intact.
 */
export function withTwoHandGripWidth(
  instance: EquipmentInstance,
  width: number | null,
): EquipmentInstance {
  if (instance.attachment.mode !== 'hands') return instance;
  const { leftSocket, rightSocket } = instance.attachment;
  const left = equipmentSocketForInstance(instance, leftSocket);
  const right = equipmentSocketForInstance(instance, rightSocket);
  if (!left || !right) return instance;

  const socketOverrides: EquipmentInstance['socketOverrides'] = {
    ...(instance.socketOverrides ?? {}),
  };

  const setPosition = (socketId: string, position: EquipmentSocket['position'] | null) => {
    const previous = socketOverrides?.[socketId] ?? {};
    if (!position) {
      const { position: _position, ...remaining } = previous;
      if (Object.keys(remaining).length > 0) socketOverrides![socketId] = remaining;
      else delete socketOverrides![socketId];
      return;
    }
    socketOverrides![socketId] = { ...previous, position: { ...position } };
  };

  if (width === null) {
    setPosition(leftSocket, null);
    setPosition(rightSocket, null);
  } else {
    const requested = Math.max(0.1, Math.min(2.0, width));
    const midpoint = {
      x: (left.position.x + right.position.x) / 2,
      y: (left.position.y + right.position.y) / 2,
      z: (left.position.z + right.position.z) / 2,
    };
    const axis = {
      x: right.position.x - left.position.x,
      y: right.position.y - left.position.y,
      z: right.position.z - left.position.z,
    };
    const length = Math.hypot(axis.x, axis.y, axis.z) || 1;
    const half = requested / 2;
    const unit = { x: axis.x / length, y: axis.y / length, z: axis.z / length };
    setPosition(leftSocket, {
      x: midpoint.x - unit.x * half,
      y: midpoint.y - unit.y * half,
      z: midpoint.z - unit.z * half,
    });
    setPosition(rightSocket, {
      x: midpoint.x + unit.x * half,
      y: midpoint.y + unit.y * half,
      z: midpoint.z + unit.z * half,
    });
  }

  return {
    ...instance,
    socketOverrides:
      socketOverrides && Object.keys(socketOverrides).length > 0 ? socketOverrides : undefined,
  };
}
