import type { BoneName } from './boneNames';
import type { BoneDefinition, Pose, Vec3 } from './types';
import { HgMat4, HgQuat, HgVec3, HG_UNIT_SCALE } from '../core/linearMath';

const WORLD_FORWARD = new HgVec3(0, 0, 1);
const WORLD_UP = new HgVec3(0, 1, 0);

export function hgBoneFrame(
  head: HgVec3,
  tail: HgVec3,
  forward: HgVec3 = WORLD_FORWARD,
): HgQuat {
  const y = new HgVec3().subVectors(tail, head);
  if (y.lengthSq() < 1e-12) return new HgQuat();
  y.normalize();

  const reference = Math.abs(y.dot(forward)) > 0.985 ? WORLD_UP : forward;
  const z = reference.clone().addScaledVector(y, -y.dot(reference));
  if (z.lengthSq() < 1e-12) return new HgQuat();
  z.normalize();

  const x = new HgVec3().crossVectors(y, z).normalize();
  return new HgQuat().setFromRotationMatrix(new HgMat4().makeBasis(x, y, z));
}

export interface HgRigBone {
  readonly definition: BoneDefinition;
  readonly name: BoneName;
  readonly parent: BoneName | null;
  readonly index: number;
  readonly children: BoneName[];
  readonly length: number;
  readonly restHead: HgVec3;
  readonly restTail: HgVec3;
  readonly restWorldQuaternion: HgQuat;
  readonly offset: HgVec3;
  readonly restLocalQuaternion: HgQuat;
  readonly depth: number;
}

export class HgSkeleton {
  readonly bones: HgRigBone[] = [];
  readonly byName = new Map<BoneName, HgRigBone>();
  readonly names: BoneName[] = [];

  constructor(definitions: BoneDefinition[]) {
    definitions.forEach((definition, index) => {
      const head = new HgVec3(definition.head.x, definition.head.y, definition.head.z);
      const tail = new HgVec3(definition.tail.x, definition.tail.y, definition.tail.z);
      const restWorldQuaternion = hgBoneFrame(head, tail);

      const parent = definition.parent ? this.byName.get(definition.parent) : undefined;
      if (definition.parent && !parent) {
        throw new Error(
          `Bone "${definition.name}" lists parent "${definition.parent}", which is not defined before it.`,
        );
      }

      const inverseParent = parent
        ? parent.restWorldQuaternion.clone().invert()
        : new HgQuat();
      const offset = parent
        ? head.clone().sub(parent.restHead).applyQuaternion(inverseParent)
        : head.clone();
      const restLocalQuaternion = inverseParent.clone().multiply(restWorldQuaternion);

      const bone: HgRigBone = {
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

  bone(name: BoneName): HgRigBone {
    const bone = this.byName.get(name);
    if (!bone) throw new Error(`Unknown bone "${name}"`);
    return bone;
  }

  has(name: string): name is BoneName {
    return this.byName.has(name as BoneName);
  }

  chainToRoot(name: BoneName): HgRigBone[] {
    const chain: HgRigBone[] = [];
    let current: HgRigBone | undefined = this.bone(name);
    while (current) {
      chain.push(current);
      current = current.parent ? this.byName.get(current.parent) : undefined;
    }
    return chain;
  }

  descendants(name: BoneName): HgRigBone[] {
    const out: HgRigBone[] = [];
    const walk = (boneName: BoneName) => {
      const bone = this.bone(boneName);
      out.push(bone);
      bone.children.forEach(walk);
    };
    walk(name);
    return out;
  }

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

export class HgPoseEvaluation {
  readonly skeleton: HgSkeleton;
  private readonly matrices: HgMat4[];
  private readonly quaternions: HgQuat[];
  private readonly scratchQuaternion = new HgQuat();
  private readonly scratchMatrix = new HgMat4();
  private readonly scratchVector = new HgVec3();

  constructor(skeleton: HgSkeleton) {
    this.skeleton = skeleton;
    this.matrices = skeleton.bones.map(() => new HgMat4());
    this.quaternions = skeleton.bones.map(() => new HgQuat());
  }

  apply(pose: Pose): this {
    const { bones } = this.skeleton;

    for (let index = 0; index < bones.length; index += 1) {
      const bone = bones[index];
      const rotation = pose.rotations[bone.name];

      this.scratchQuaternion.setFromEulerXZY(
        rotation?.x ?? 0,
        rotation?.y ?? 0,
        rotation?.z ?? 0,
      );

      const local = this.matrices[index];
      local.compose(
        this.scratchVector.copy(bone.offset),
        this.quaternions[index]
          .copy(bone.restLocalQuaternion)
          .multiply(this.scratchQuaternion),
        HG_UNIT_SCALE,
      );

      if (bone.parent === null) {
        this.scratchMatrix.compose(
          this.scratchVector.set(
            pose.rootPosition.x,
            pose.rootPosition.y,
            pose.rootPosition.z,
          ),
          this.scratchQuaternion.setFromEulerXZY(
            pose.rootRotation.x,
            pose.rootRotation.y,
            pose.rootRotation.z,
          ),
          HG_UNIT_SCALE,
        );
        local.premultiply(this.scratchMatrix);
      } else {
        local.premultiply(this.matrices[this.skeleton.bone(bone.parent).index]);
      }

      this.quaternions[index].setFromRotationMatrix(local);
    }

    return this;
  }

  matrix(name: BoneName): HgMat4 {
    return this.matrices[this.skeleton.bone(name).index];
  }

  quaternion(name: BoneName): HgQuat {
    return this.quaternions[this.skeleton.bone(name).index];
  }

  head(name: BoneName, target = new HgVec3()): HgVec3 {
    return target.setFromMatrixPosition(this.matrix(name));
  }

  tail(name: BoneName, target = new HgVec3()): HgVec3 {
    const bone = this.skeleton.bone(name);
    return target.set(0, bone.length, 0).applyMatrix4(this.matrix(name));
  }

  localToWorld(name: BoneName, local: Vec3, target = new HgVec3()): HgVec3 {
    return target.set(local.x, local.y, local.z).applyMatrix4(this.matrix(name));
  }

  worldToLocal(name: BoneName, world: HgVec3, target = new HgVec3()): HgVec3 {
    return target
      .copy(world)
      .applyMatrix4(this.scratchMatrix.copy(this.matrix(name)).invert());
  }
}

