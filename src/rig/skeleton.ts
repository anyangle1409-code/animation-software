import { Matrix4, Quaternion, Vector3 } from 'three';
import type { BoneName } from './boneNames';
import type { BoneDefinition, Pose, Vec3 } from './types';
import { HUMANOID_BONES } from './humanoid';
import { HgVec3 } from '../core/linearMath';
import {
  HgPoseEvaluation,
  HgSkeleton,
  hgBoneFrame,
} from './firstPartySkeleton';

const THREE_WORLD_FORWARD = new Vector3(0, 0, 1);

/**
 * Build the orthonormal rest frame of a bone:
 *   +Y along the bone, +Z the body's forward projected perpendicular to Y,
 *   +X = Y x Z.
 *
 * The calculation is now first-party; the Three quaternion returned here is a
 * temporary compatibility object for callers that have not yet crossed the
 * renderer/export boundary.
 */
export function boneFrame(
  head: Vector3,
  tail: Vector3,
  forward: Vector3 = THREE_WORLD_FORWARD,
): Quaternion {
  const frame = hgBoneFrame(
    new HgVec3(head.x, head.y, head.z),
    new HgVec3(tail.x, tail.y, tail.z),
    new HgVec3(forward.x, forward.y, forward.z),
  );
  return new Quaternion(frame.x, frame.y, frame.z, frame.w);
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

const asThreeVector = (value: HgVec3): Vector3 =>
  new Vector3(value.x, value.y, value.z);

const asThreeQuaternion = (value: { x: number; y: number; z: number; w: number }): Quaternion =>
  new Quaternion(value.x, value.y, value.z, value.w);

/**
 * Compatibility shell around the project-owned skeleton construction.
 *
 * The canonical rest-frame calculations are performed by HgSkeleton. Three
 * vectors/quaternions remain only as boundary objects until renderer/export
 * callers are migrated in later S6-S8 increments.
 */
export class Skeleton {
  readonly bones: RigBone[] = [];
  readonly byName = new Map<BoneName, RigBone>();
  readonly names: BoneName[] = [];
  readonly firstParty: HgSkeleton;

  constructor(definitions: BoneDefinition[] = HUMANOID_BONES) {
    this.firstParty = new HgSkeleton(definitions);

    for (const current of this.firstParty.bones) {
      const bone: RigBone = {
        definition: current.definition,
        name: current.name,
        parent: current.parent,
        index: current.index,
        children: [...current.children],
        length: current.length,
        restHead: asThreeVector(current.restHead),
        restTail: asThreeVector(current.restTail),
        restWorldQuaternion: asThreeQuaternion(current.restWorldQuaternion),
        offset: asThreeVector(current.offset),
        restLocalQuaternion: asThreeQuaternion(current.restLocalQuaternion),
        depth: current.depth,
      };
      this.bones.push(bone);
      this.byName.set(bone.name, bone);
      this.names.push(bone.name);
    }
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

  /**
   * The nearest ancestor that is a different joint — whose head does not sit
   * on this bone's own head.
   */
  jointParent(name: BoneName): BoneName | null {
    const bone = this.bone(name);
    let current = bone.parent;
    while (current) {
      const candidate = this.bone(current);
      if (candidate.restHead.distanceTo(bone.restHead) > 1e-9) return current;
      current = candidate.parent;
    }
    return null;
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
 * Forward kinematics compatibility shell.
 *
 * HgPoseEvaluation now performs the production transform calculation. The
 * Three matrices/quaternions exposed by this class are copied compatibility
 * views for existing renderer/export/engine callers and can be removed as
 * those boundaries migrate.
 */
export class PoseEvaluation {
  readonly skeleton: Skeleton;
  private readonly firstParty: HgPoseEvaluation;
  private readonly matrices: Matrix4[];
  private readonly quaternions: Quaternion[];
  private readonly scratchVector = new HgVec3();

  constructor(skeleton: Skeleton) {
    this.skeleton = skeleton;
    this.firstParty = new HgPoseEvaluation(skeleton.firstParty);
    this.matrices = skeleton.bones.map(() => new Matrix4());
    this.quaternions = skeleton.bones.map(() => new Quaternion());
  }

  /** Recompute every bone's world transform for `pose`. */
  apply(pose: Pose): this {
    this.firstParty.apply(pose);

    for (const bone of this.skeleton.bones) {
      const sourceMatrix = this.firstParty.matrix(bone.name).elements;
      const targetMatrix = this.matrices[bone.index].elements;
      for (let index = 0; index < 16; index += 1) {
        targetMatrix[index] = sourceMatrix[index];
      }

      const sourceQuaternion = this.firstParty.quaternion(bone.name);
      this.quaternions[bone.index].set(
        sourceQuaternion.x,
        sourceQuaternion.y,
        sourceQuaternion.z,
        sourceQuaternion.w,
      );
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
    const point = this.firstParty.head(name, this.scratchVector);
    return target.set(point.x, point.y, point.z);
  }

  /** World position of a bone's far end. */
  tail(name: BoneName, target = new Vector3()): Vector3 {
    const point = this.firstParty.tail(name, this.scratchVector);
    return target.set(point.x, point.y, point.z);
  }

  /** A point expressed in the bone's local frame, converted to world space. */
  localToWorld(name: BoneName, local: Vec3, target = new Vector3()): Vector3 {
    const point = this.firstParty.localToWorld(name, local, this.scratchVector);
    return target.set(point.x, point.y, point.z);
  }

  /** A world point expressed in the bone's local frame. */
  worldToLocal(name: BoneName, world: Vector3, target = new Vector3()): Vector3 {
    this.scratchVector.set(world.x, world.y, world.z);
    const point = this.firstParty.worldToLocal(name, this.scratchVector, this.scratchVector);
    return target.set(point.x, point.y, point.z);
  }
}

/** The shared canonical rig. One skeleton, every exercise. */
export const canonicalSkeleton = new Skeleton();
