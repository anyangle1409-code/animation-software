import { Euler, Matrix4, Quaternion, Vector3 } from 'three';
import type { BoneName } from './boneNames';
import type { BoneDefinition, Pose, Vec3 } from './types';
import { EULER_ORDER } from './types';
import { HUMANOID_BONES } from './humanoid';

const WORLD_FORWARD = new Vector3(0, 0, 1);
const WORLD_UP = new Vector3(0, 1, 0);

/**
 * Build the orthonormal rest frame of a bone:
 *   +Y along the bone, +Z the body's forward projected perpendicular to Y,
 *   +X = Y x Z.
 * See `types.ts` for why every joint shares this convention.
 */
export function boneFrame(
  head: Vector3,
  tail: Vector3,
  forward: Vector3 = WORLD_FORWARD,
): Quaternion {
  const y = new Vector3().subVectors(tail, head);
  if (y.lengthSq() < 1e-12) return new Quaternion();
  y.normalize();

  const reference = Math.abs(y.dot(forward)) > 0.985 ? WORLD_UP : forward;
  const z = reference.clone().addScaledVector(y, -y.dot(reference));
  if (z.lengthSq() < 1e-12) return new Quaternion();
  z.normalize();

  const x = new Vector3().crossVectors(y, z).normalize();
  const basis = new Matrix4().makeBasis(x, y, z);
  return new Quaternion().setFromRotationMatrix(basis);
}

/** A bone with everything precomputed that forward kinematics needs. */
export interface RigBone {
  readonly definition: BoneDefinition;
  readonly name: BoneName;
  readonly parent: BoneName | null;
  readonly index: number;
  readonly children: BoneName[];
  /** Bone length in metres. */
  readonly length: number;
  /** Rest head position in world space. */
  readonly restHead: Vector3;
  readonly restTail: Vector3;
  /** Rest orientation of the bone frame in world space. */
  readonly restWorldQuaternion: Quaternion;
  /** Head position relative to the parent's rest frame. */
  readonly offset: Vector3;
  /** Rest orientation relative to the parent's rest frame. */
  readonly restLocalQuaternion: Quaternion;
  /** Depth in the hierarchy; 0 for the root. */
  readonly depth: number;
}

/**
 * The canonical skeleton. Immutable: it describes the rig, never a pose.
 * Poses are plain data evaluated against it by `PoseEvaluation`.
 */
export class Skeleton {
  readonly bones: RigBone[] = [];
  readonly byName = new Map<BoneName, RigBone>();
  readonly names: BoneName[] = [];

  constructor(definitions: BoneDefinition[] = HUMANOID_BONES) {
    definitions.forEach((definition, index) => {
      const head = new Vector3(definition.head.x, definition.head.y, definition.head.z);
      const tail = new Vector3(definition.tail.x, definition.tail.y, definition.tail.z);
      const restWorldQuaternion = boneFrame(head, tail);

      const parent = definition.parent ? this.byName.get(definition.parent) : undefined;
      if (definition.parent && !parent) {
        throw new Error(
          `Bone "${definition.name}" lists parent "${definition.parent}", which is not defined before it.`,
        );
      }

      const inverseParent = parent
        ? parent.restWorldQuaternion.clone().invert()
        : new Quaternion();
      const offset = parent
        ? head.clone().sub(parent.restHead).applyQuaternion(inverseParent)
        : head.clone();
      const restLocalQuaternion = inverseParent.clone().multiply(restWorldQuaternion);

      const bone: RigBone = {
        definition,
        name: definition.name,
        parent: definition.parent,
        index,
        children: [],
        length: head.distanceTo(tail),
        restHead: head,
        restTail: tail,
        restWorldQuaternion,
        offset,
        restLocalQuaternion,
        depth: parent ? parent.depth + 1 : 0,
      };

      parent?.children.push(bone.name);
      this.bones.push(bone);
      this.byName.set(bone.name, bone);
      this.names.push(bone.name);
    });
  }

  bone(name: BoneName): RigBone {
    const bone = this.byName.get(name);
    if (!bone) throw new Error(`Unknown bone "${name}"`);
    return bone;
  }

  has(name: string): name is BoneName {
    return this.byName.has(name as BoneName);
  }

  /** Bones from `name` up to the root, nearest first. */
  chainToRoot(name: BoneName): RigBone[] {
    const chain: RigBone[] = [];
    let current: RigBone | undefined = this.bone(name);
    while (current) {
      chain.push(current);
      current = current.parent ? this.byName.get(current.parent) : undefined;
    }
    return chain;
  }

  /** `name` and everything beneath it, parents first. */
  descendants(name: BoneName): RigBone[] {
    const out: RigBone[] = [];
    const walk = (boneName: BoneName) => {
      const bone = this.bone(boneName);
      out.push(bone);
      bone.children.forEach(walk);
    };
    walk(name);
    return out;
  }

  isAncestorOf(ancestor: BoneName, descendant: BoneName): boolean {
    let current = this.bone(descendant).parent;
    while (current) {
      if (current === ancestor) return true;
      current = this.bone(current).parent;
    }
    return false;
  }
}

/**
 * Forward kinematics for one pose. Reuses its buffers, so the same instance can
 * be evaluated every frame without allocating.
 */
export class PoseEvaluation {
  readonly skeleton: Skeleton;
  private readonly matrices: Matrix4[];
  private readonly quaternions: Quaternion[];
  private readonly scratchEuler = new Euler(0, 0, 0, EULER_ORDER);
  private readonly scratchQuaternion = new Quaternion();
  private readonly scratchMatrix = new Matrix4();
  private readonly scratchVector = new Vector3();

  constructor(skeleton: Skeleton) {
    this.skeleton = skeleton;
    this.matrices = skeleton.bones.map(() => new Matrix4());
    this.quaternions = skeleton.bones.map(() => new Quaternion());
  }

  /** Recompute every bone's world transform for `pose`. */
  apply(pose: Pose): this {
    const { bones } = this.skeleton;
    for (let i = 0; i < bones.length; i += 1) {
      const bone = bones[i];
      const rotation = pose.rotations[bone.name];
      this.scratchEuler.set(rotation?.x ?? 0, rotation?.y ?? 0, rotation?.z ?? 0, EULER_ORDER);
      this.scratchQuaternion.setFromEuler(this.scratchEuler);

      const local = this.matrices[i];
      local.compose(
        this.scratchVector.copy(bone.offset),
        this.quaternions[i]
          .copy(bone.restLocalQuaternion)
          .multiply(this.scratchQuaternion),
        UNIT_SCALE,
      );

      if (bone.parent === null) {
        // The root additionally carries the rig's world placement.
        this.scratchEuler.set(
          pose.rootRotation.x,
          pose.rootRotation.y,
          pose.rootRotation.z,
          EULER_ORDER,
        );
        this.scratchMatrix.compose(
          this.scratchVector.set(pose.rootPosition.x, pose.rootPosition.y, pose.rootPosition.z),
          this.scratchQuaternion.setFromEuler(this.scratchEuler),
          UNIT_SCALE,
        );
        local.premultiply(this.scratchMatrix);
      } else {
        local.premultiply(this.matrices[this.skeleton.bone(bone.parent).index]);
      }

      this.quaternions[i].setFromRotationMatrix(local);
    }
    return this;
  }

  matrix(name: BoneName): Matrix4 {
    return this.matrices[this.skeleton.bone(name).index];
  }

  quaternion(name: BoneName): Quaternion {
    return this.quaternions[this.skeleton.bone(name).index];
  }

  /** World position of a bone's joint. */
  head(name: BoneName, target = new Vector3()): Vector3 {
    return target.setFromMatrixPosition(this.matrix(name));
  }

  /** World position of a bone's far end. */
  tail(name: BoneName, target = new Vector3()): Vector3 {
    const bone = this.skeleton.bone(name);
    return target.set(0, bone.length, 0).applyMatrix4(this.matrix(name));
  }

  /** A point expressed in the bone's local frame, converted to world space. */
  localToWorld(name: BoneName, local: Vec3, target = new Vector3()): Vector3 {
    return target.set(local.x, local.y, local.z).applyMatrix4(this.matrix(name));
  }

  /** A world point expressed in the bone's local frame. */
  worldToLocal(name: BoneName, world: Vector3, target = new Vector3()): Vector3 {
    return target
      .copy(world)
      .applyMatrix4(this.scratchMatrix.copy(this.matrix(name)).invert());
  }
}

const UNIT_SCALE = new Vector3(1, 1, 1);

/** The shared canonical rig. One skeleton, every exercise. */
export const canonicalSkeleton = new Skeleton();
