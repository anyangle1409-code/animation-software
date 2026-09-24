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
  'cable_tower',
  'cable_bar',
  'cable',
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
   * `static` leaves it where it is placed; `cable` stretches between two other
   * items' sockets.
   */
  attachment: EquipmentAttachment;
  visible: boolean;
  /**
   * The body rests on this item — sits on a bench, lies on a pad. Clearance is
   * then the opposite question from a dumbbell's: the body should meet it, and
   * may press a little way in as soft tissue does, but must not sink through.
   */
  supportsBody?: boolean;
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
      /** Shared hand-local grip point retained for backwards compatibility. */
      gripOffset?: Vec3;
      /** Optional side-specific hand-local grip points. */
      leftGripOffset?: Vec3;
      rightGripOffset?: Vec3;
      /** Roll of the rigid two-hand item around the line joining both grips, degrees. */
      gripRoll?: number;
    }
  | {
      /**
       * A line running from one item's socket to another's — the cable from a
       * machine's pulley to the handle clipped to it. It has no pose of its own:
       * it starts at `from`, points at `to` and is exactly as long as the gap,
       * so it follows whatever the two ends do.
       */
      mode: 'cable';
      from: { equipment: string; socket: string };
      to: { equipment: string; socket: string };
    };
