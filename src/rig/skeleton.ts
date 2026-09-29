import type { BoneName } from './boneNames';
import type { BoneDefinition, Pose, Vec3 } from './types';
import { HUMANOID_BONES } from './humanoid';
import { HgMat4, HgQuat, HgVec3 } from '../core/linearMath';
import {
  HgPoseEvaluation,
  HgSkeleton,
  hgBoneFrame,
} from './firstPartySkeleton';

const HG_WORLD_FORWARD: Vec3 = { x: 0, y: 0, z: 1 };

/**
 * Build the orthonormal rest frame of a bone:
 *   +Y along the bone, +Z the body's forward projected perpendicular to Y,
 *   +X = Y x Z.
 *
 * Both the calculation and the returned quaternion are project-owned.
 */
export function boneFrame(
  head: Vec3,
  tail: Vec3,
  forward: Vec3 = HG_WORLD_FORWARD,
): HgQuat {
  return hgBoneFrame(
    new HgVec3(head.x, head.y, head.z),
    new HgVec3(tail.x, tail.y, tail.z),
    new HgVec3(forward.x, forward.y, forward.z),
  );
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
  readonly restHead: HgVec3;
  readonly restTail: HgVec3;
  /** Rest orientation of the bone frame in world space. */
  readonly restWorldQuaternion: HgQuat;
  /** Head position relative to the parent's rest frame. */
  readonly offset: HgVec3;
  /** Rest orientation relative to the parent's rest frame. */
  readonly restLocalQuaternion: HgQuat;
  /** Depth in the hierarchy; 0 for the root. */
  readonly depth: number;
}

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
        restHead: current.restHead.clone(),
        restTail: current.restTail.clone(),
        restWorldQuaternion: current.restWorldQuaternion.clone(),
        offset: current.offset.clone(),
        restLocalQuaternion: current.restLocalQuaternion.clone(),
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
 * Forward kinematics facade backed entirely by the project-owned evaluator.
 *
 * The object identity remains stable across apply() calls, but matrices,
 * quaternions and vectors no longer require Three compatibility objects.
 */
export class PoseEvaluation {
  readonly skeleton: Skeleton;
  readonly firstPartyEvaluation: HgPoseEvaluation;
  private readonly scratchVector = new HgVec3();

  constructor(skeleton: Skeleton) {
    this.skeleton = skeleton;
    this.firstPartyEvaluation = new HgPoseEvaluation(skeleton.firstParty);
  }

  /** Recompute every bone's world transform for `pose`. */
  apply(pose: Pose): this {
    this.firstPartyEvaluation.apply(pose);
    return this;
  }

  matrix(name: BoneName): HgMat4 {
    return this.firstPartyEvaluation.matrix(name);
  }

  quaternion(name: BoneName): HgQuat {
    return this.firstPartyEvaluation.quaternion(name);
  }

  /** World position of a bone's joint. */
  head<T extends Vec3 & { set(x: number, y: number, z: number): T } = HgVec3>(
    name: BoneName,
    target: T = new HgVec3() as unknown as T,
  ): T {
    const point = this.firstPartyEvaluation.head(name, this.scratchVector);
    return target.set(point.x, point.y, point.z);
  }

  /** World position of a bone's far end. */
  tail<T extends Vec3 & { set(x: number, y: number, z: number): T } = HgVec3>(
    name: BoneName,
    target: T = new HgVec3() as unknown as T,
  ): T {
    const point = this.firstPartyEvaluation.tail(name, this.scratchVector);
    return target.set(point.x, point.y, point.z);
  }

  /** A point expressed in the bone's local frame, converted to world space. */
  localToWorld<T extends Vec3 & { set(x: number, y: number, z: number): T } = HgVec3>(
    name: BoneName,
    local: Vec3,
    target: T = new HgVec3() as unknown as T,
  ): T {
    const point = this.firstPartyEvaluation.localToWorld(name, local, this.scratchVector);
    return target.set(point.x, point.y, point.z);
  }

  /** A world point expressed in the bone's local frame. */
  worldToLocal<T extends Vec3 & { set(x: number, y: number, z: number): T } = HgVec3>(
    name: BoneName,
    world: Vec3,
    target: T = new HgVec3() as unknown as T,
  ): T {
    this.scratchVector.set(world.x, world.y, world.z);
    const point = this.firstPartyEvaluation.worldToLocal(name, this.scratchVector, this.scratchVector);
    return target.set(point.x, point.y, point.z);
  }
}

/** The shared canonical rig. One skeleton, every exercise. */
export const canonicalSkeleton = new Skeleton();
