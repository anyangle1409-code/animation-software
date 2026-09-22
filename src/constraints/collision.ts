import { Euler, Matrix4, Vector3 } from 'three';
import { EQUIPMENT_PARTS } from '../equipment/geometry';
import type { Part } from '../equipment/geometry';
import type { EquipmentKind } from '../equipment/types';

/**
 * How close does a piece of equipment come to the body?
 *
 * Nothing in the technique-rule vocabulary can ask this. A repetition can
 * satisfy every joint limit, reach every IK target, close its loop and hold
 * every contact while driving a dumbbell clean through the thigh — the hammer
 * curl did exactly that when it was first written, 16.92 mm deep with 82
 * vertices inside, and every existing gate reported it clean.
 *
 * This is the measurement half of the plan's Phase 5. It does not decide policy:
 * it returns a signed distance and lets a test or a review gate say what is
 * acceptable, because what counts as too close differs between a dumbbell beside
 * a thigh and a bar against a chest.
 *
 * ## The envelope comes from the equipment's own geometry
 *
 * `EQUIPMENT_PARTS` is the single description the viewport and the GLB exporter
 * both build from, so deriving the collision envelope from it too means the
 * thing being measured is the thing being drawn and exported. A hand-written
 * envelope would be a third copy, free to drift from both.
 *
 * Each part contributes a signed distance and the item is their union, which is
 * the minimum. Two approximations, both deliberately conservative — they can
 * report less clearance than there really is, never more, so the error can only
 * make the guard stricter:
 *
 * - a tapered cylinder (`radiusTop` ≠ `radius`) is measured at its widest;
 * - a torus is treated as its full swept ring even when `arc` is partial.
 *
 * Anything that reads a number from here and calls it exact would be wrong; the
 * number is a lower bound on the true clearance.
 */

const scratch = new Vector3();
const local = new Vector3();

/** Inverse of a part's own placement within the equipment frame. */
function partMatrix(part: Part): Matrix4 {
  const [px, py, pz] = part.position ?? [0, 0, 0];
  const matrix = new Matrix4();
  if ('rotation' in part && part.rotation) {
    const [rx, ry, rz] = part.rotation;
    matrix.makeRotationFromEuler(new Euler(rx, ry, rz));
  }
  matrix.setPosition(px, py, pz);
  return matrix.invert();
}

const INVERSE = new WeakMap<Part, Matrix4>();
const inverseOf = (part: Part): Matrix4 => {
  let matrix = INVERSE.get(part);
  if (!matrix) {
    matrix = partMatrix(part);
    INVERSE.set(part, matrix);
  }
  return matrix;
};

/**
 * Signed distance from a point to one part, in the part's own frame.
 *
 * Every primitive is measured exactly except where the header notes otherwise.
 * A cylinder is authored along its own Y, which is why the radial term uses x
 * and z rather than x and y.
 */
function distanceToPart(part: Part, point: Vector3): number {
  switch (part.shape) {
    case 'cylinder': {
      const radius = Math.max(part.radius, part.radiusTop ?? part.radius);
      const radial = Math.hypot(point.x, point.z) - radius;
      const axial = Math.abs(point.y) - part.length / 2;
      // Outside both, the distance is the corner; outside one, that one.
      return radial > 0 && axial > 0
        ? Math.hypot(radial, axial)
        : Math.max(radial, axial);
    }
    case 'box': {
      const [sx, sy, sz] = part.size;
      const dx = Math.abs(point.x) - sx / 2;
      const dy = Math.abs(point.y) - sy / 2;
      const dz = Math.abs(point.z) - sz / 2;
      const outside = Math.hypot(Math.max(dx, 0), Math.max(dy, 0), Math.max(dz, 0));
      return outside > 0 ? outside : Math.max(dx, dy, dz);
    }
    case 'sphere':
      return point.length() - part.radius;
    case 'torus': {
      // The ring lies in the part's own XZ plane, its tube swept about Y.
      const ring = Math.hypot(point.x, point.z) - part.radius;
      return Math.hypot(ring, point.y) - part.tube;
    }
    default:
      return Number.POSITIVE_INFINITY;
  }
}

/**
 * Signed distance from a point in an item's own frame to its surface: negative
 * inside, positive outside, in metres.
 */
export function equipmentDistance(kind: EquipmentKind, point: Vector3): number {
  const parts = EQUIPMENT_PARTS[kind];
  let closest = Number.POSITIVE_INFINITY;
  for (const part of parts) {
    local.copy(point).applyMatrix4(inverseOf(part));
    const distance = distanceToPart(part, local);
    if (distance < closest) closest = distance;
  }
  return closest;
}

export interface ClearanceSample {
  /** Signed distance, metres. Negative means the body is inside the item. */
  closest: number;
  /** How many measured points were inside the item. */
  inside: number;
  /** Where the closest approach happened, for the failure message. */
  where: string;
}

/**
 * Closest approach between one placed item and a set of world-space points.
 *
 * `toItem` takes world space into the item's own frame — the inverse of the
 * transform that places it — and `points` is called back for each index so the
 * caller keeps ownership of how the body is posed and which vertices count.
 */
export function measureClearance(
  kind: EquipmentKind,
  toItem: Matrix4,
  count: number,
  points: (index: number, out: Vector3) => Vector3 | null,
  label: (index: number) => string,
  into: ClearanceSample = { closest: Number.POSITIVE_INFINITY, inside: 0, where: '' },
): ClearanceSample {
  for (let index = 0; index < count; index += 1) {
    const world = points(index, scratch);
    if (!world) continue;
    const distance = equipmentDistance(kind, world.applyMatrix4(toItem));
    if (distance < 0) into.inside += 1;
    if (distance < into.closest) {
      into.closest = distance;
      into.where = label(index);
    }
  }
  return into;
}
