import type { BoneName } from './boneNames';

export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

export const vec3 = (x = 0, y = 0, z = 0): Vec3 => ({ x, y, z });

/**
 * Rotation axes are expressed in each bone's own rest frame, built so that the
 * convention is the same for every joint in the body:
 *
 *   +Y  runs along the bone, from its head towards its tail
 *   +Z  is the bone's "forward" (the body's front, projected perpendicular to Y)
 *   +X  = Y x Z, the flexion axis
 *
 * That gives every joint the same anatomical meaning for its three axes:
 *
 *   x — flexion / extension   (sagittal plane)
 *   y — axial rotation        (twist along the bone)
 *   z — abduction / adduction (frontal plane)
 *
 * Because limbs bend in opposite directions, the *sign* of flexion differs
 * between the arm and the leg: elbow flexion is +x, knee flexion is -x. Each
 * axis therefore carries its own label so the UI can describe it correctly
 * instead of the user having to remember which way is which.
 */
export type Axis = 'x' | 'y' | 'z';
export const AXES: Axis[] = ['x', 'y', 'z'];

export interface AxisLimit {
  /** Minimum rotation in degrees. */
  min: number;
  /** Maximum rotation in degrees. */
  max: number;
  /** What positive rotation about this axis does, e.g. "Flexion". */
  positive: string;
  /** What negative rotation about this axis does, e.g. "Extension". */
  negative: string;
}

/** A locked axis (`null`) is pinned to zero — a hinge has two of them. */
export type JointLimits = Record<Axis, AxisLimit | null>;

export interface BoneDefinition {
  name: BoneName;
  parent: BoneName | null;
  /** World-space position of the joint in the rest pose, in metres. */
  head: Vec3;
  /** World-space position of the bone's far end in the rest pose, in metres. */
  tail: Vec3;
  limits: JointLimits;
  /** Approximate soft-tissue radius, used by the mannequin and by muscles. */
  radius: number;
  /** Bones excluded from the default display to keep the viewport readable. */
  minor?: boolean;
}

/**
 * A pose is plain data: a local rotation per bone (Euler angles in radians,
 * order ZXY, in the bone's rest frame) plus the root's world transform.
 *
 * Everything in the studio — FK, IK, constraints, muscles, the timeline and
 * every exporter — reads and writes this one structure, which is what keeps
 * animation data independent of any particular visible character.
 */
export interface Pose {
  rotations: Partial<Record<BoneName, Vec3>>;
  rootPosition: Vec3;
  rootRotation: Vec3;
}

/**
 * Euler order for every joint rotation: twist (y) innermost, then abduction
 * (z), then flexion (x).
 *
 * The order matters more than it looks. An Euler decomposition is singular when
 * its *middle* axis reaches ±90°, and at that point the other two axes trade
 * off freely — a solver picks an arbitrary split, the joint limits clamp it,
 * and the pose falls apart. Putting abduction in the middle moves that
 * singularity to 90° of abduction, which a hip cannot reach at all, instead of
 * 90° of flexion, which is exactly where a squat and a press live.
 */
export const EULER_ORDER = 'XZY' as const;
