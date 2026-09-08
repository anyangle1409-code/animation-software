import type { EquipmentDefinition, EquipmentKind, EquipmentSocket } from './types';
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
      socket('back', 'Back support', [0, 0.6, 0.16], 'support', [-45, 0, 0]),
      socket('seat', 'Seat', [0, 0.44, -0.42], 'support'),
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
      socket('pullup_l', 'Pull-up bar (L)', [-0.24, 1.97, 0], 'grip', [0, 90, 0]),
      socket('pullup_r', 'Pull-up bar (R)', [0.24, 1.97, 0], 'grip', [0, -90, 0]),
    ],
  },
  cable_handle: {
    kind: 'cable_handle',
    label: 'Cable handle',
    defaultMass: 1,
    paired: true,
    size: vec3(0.06, 0.16, 0.14),
    sockets: [socket('grip', 'Handle', [0, 0, 0]), socket('clip', 'Cable clip', [0, 0.11, 0], 'mount')],
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
};

export const EQUIPMENT_LIST = Object.values(EQUIPMENT_LIBRARY);

export function equipmentSocket(kind: EquipmentKind, socketId: string): EquipmentSocket | null {
  return EQUIPMENT_LIBRARY[kind].sockets.find((entry) => entry.id === socketId) ?? null;
}
