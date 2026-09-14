import type { Vec3 } from '../rig/types';

export const EQUIPMENT_KINDS = [
  'dumbbell',
  'barbell',
  'ez_curl_bar',
  'weight_plate',
  'flat_bench',
  'incline_bench',
  'squat_rack',
  'cable_handle',
  'cable_rope',
  'lat_pulldown_bar',
  'resistance_band',
  'kettlebell',
] as const;

export type EquipmentKind = (typeof EQUIPMENT_KINDS)[number];

/**
 * A named point on a piece of equipment that something can be attached to —
 * a grip, a plate seat, a bench's back surface. Sockets are what make
 * attachment rigid rather than decorative.
 */
export interface EquipmentSocket {
  id: string;
  label: string;
  /** Position in the equipment's local frame, metres. */
  position: Vec3;
  /**
   * Orientation in the equipment's local frame, as Euler degrees. +Y points
   * the way an attached bone's own +Y should point, +Z its forward.
   */
  rotation?: Vec3;
  kind: SocketKind;
}

export type SocketKind =
  /** A place a hand grips. */
  | 'grip'
  /** A surface a body part rests on. */
  | 'support'
  /** A place another piece of equipment mounts. */
  | 'mount';

export interface EquipmentDefinition {
  kind: EquipmentKind;
  label: string;
  /** Default mass in kilograms, used for labelling exports. */
  defaultMass: number;
  sockets: EquipmentSocket[];
  /** Whether the item is normally held one per hand. */
  paired: boolean;
  /** Rough bounding size in metres, for camera framing. */
  size: Vec3;
}

/** One piece of equipment placed in a scene. */
export interface EquipmentInstance {
  id: string;
  kind: EquipmentKind;
  label?: string;
  mass?: number;
  /** World transform when the item is not driven by an attachment. */
  position: Vec3;
  rotation: Vec3;
  /** Per-exercise local socket calibration. Library defaults remain unchanged. */
  socketOverrides?: Partial<Record<string, { position?: Vec3; rotation?: Vec3 }>>;
  /**
   * How the item is bound into the scene. `hand` makes the item rigidly follow
   * a hand; `hands` keeps a single bar between two hands, moving symmetrically;
   * `static` leaves it where it is placed.
   */
  attachment: EquipmentAttachment;
  visible: boolean;
}

export type EquipmentAttachment =
  | { mode: 'static' }
  | {
      mode: 'hand';
      side: 'l' | 'r';
      /** Socket on the equipment that meets the hand. */
      socket: string;
      /** Offset of the grip within the hand, in the hand bone's local frame. */
      gripOffset?: Vec3;
      /** Equipment orientation relative to the hand grip frame, Euler degrees. */
      gripRotation?: Vec3;
    }
  | {
      mode: 'hands';
      /** Sockets gripped by the left and right hands. */
      leftSocket: string;
      rightSocket: string;
      gripOffset?: Vec3;
    };
