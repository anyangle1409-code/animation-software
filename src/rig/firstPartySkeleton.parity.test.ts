import { describe, expect, it } from 'vitest';
import { Euler, Matrix4, Quaternion, Vector3 } from 'three';
import { EXERCISES } from '../exercises/library';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { canonicalSkeleton, PoseEvaluation } from './skeleton';
import { HgPoseEvaluation, hgCanonicalSkeleton } from './firstPartySkeleton';
import { HgVec3 } from '../core/linearMath';
import type { BoneName } from './boneNames';
import type { BoneDefinition, Pose } from './types';
import { EULER_ORDER } from './types';
import { HUMANOID_BONES } from './humanoid';

const EPS = 2e-11;
const WORLD_FORWARD = new Vector3(0, 0, 1);
const WORLD_UP = new Vector3(0, 1, 0);
const UNIT_SCALE = new Vector3(1, 1, 1);

interface ThreeReferenceBone {
  definition: BoneDefinition;
  name: BoneName;
  parent: BoneName | null;
  index: number;
  length: number;
  restHead: Vector3;
  restTail: Vector3;
  restWorldQuaternion: Quaternion;
  offset: Vector3;
  restLocalQuaternion: Quaternion;
}

const threeBoneFrame = (head: Vector3, tail: Vector3): Quaternion => {
  const y = new Vector3().subVectors(tail, head);
  if (y.lengthSq() < 1e-12) return new Quaternion();
  y.normalize();
  const reference = Math.abs(y.dot(WORLD_FORWARD)) > 0.985 ? WORLD_UP : WORLD_FORWARD;
  const z = reference.clone().addScaledVector(y, -y.dot(reference));
  if (z.lengthSq() < 1e-12) return new Quaternion();
  z.normalize();
  const x = new Vector3().crossVectors(y, z).normalize();
  return new Quaternion().setFromRotationMatrix(new Matrix4().makeBasis(x, y, z));
};

class ThreeReferenceSkeleton {
  readonly bones: ThreeReferenceBone[] = [];
  readonly byName = new Map<BoneName, ThreeReferenceBone>();

  constructor(definitions: BoneDefinition[] = HUMANOID_BONES) {
    definitions.forEach((definition, index) => {
      const head = new Vector3(definition.head.x, definition.head.y, definition.head.z);
      const tail = new Vector3(definition.tail.x, definition.tail.y, definition.tail.z);
      const restWorldQuaternion = threeBoneFrame(head, tail);
      const parent = definition.parent ? this.byName.get(definition.parent) : undefined;
      if (definition.parent && !parent) throw new Error('Invalid Three reference hierarchy');
      const inverseParent = parent
        ? parent.restWorldQuaternion.clone().invert()
        : new Quaternion();
      const bone: ThreeReferenceBone = {
        definition,
        name: definition.name,
        parent: definition.parent,
        index,
        length: head.distanceTo(tail),
        restHead: head,
        restTail: tail,
        restWorldQuaternion,
        offset: parent
          ? head.clone().sub(parent.restHead).applyQuaternion(inverseParent)
          : head.clone(),
        restLocalQuaternion: inverseParent.clone().multiply(restWorldQuaternion),
      };
      this.bones.push(bone);
      this.byName.set(bone.name, bone);
    });
  }

  bone(name: BoneName): ThreeReferenceBone {
    const bone = this.byName.get(name);
    if (!bone) throw new Error(`Unknown reference bone "${name}"`);
    return bone;
  }
}

class ThreeReferenceEvaluation {
  private readonly matrices: Matrix4[];
  private readonly quaternions: Quaternion[];
  private readonly scratchEuler = new Euler(0, 0, 0, EULER_ORDER);
  private readonly scratchQuaternion = new Quaternion();
  private readonly scratchMatrix = new Matrix4();
  private readonly scratchVector = new Vector3();

  constructor(readonly skeleton: ThreeReferenceSkeleton) {
    this.matrices = skeleton.bones.map(() => new Matrix4());
    this.quaternions = skeleton.bones.map(() => new Quaternion());
  }

  apply(pose: Pose): this {
    for (const bone of this.skeleton.bones) {
      const rotation = pose.rotations[bone.name];
      this.scratchEuler.set(
        rotation?.x ?? 0,
        rotation?.y ?? 0,
        rotation?.z ?? 0,
        EULER_ORDER,
      );
      this.scratchQuaternion.setFromEuler(this.scratchEuler);

      const local = this.matrices[bone.index];
      local.compose(
        this.scratchVector.copy(bone.offset),
        this.quaternions[bone.index]
          .copy(bone.restLocalQuaternion)
          .multiply(this.scratchQuaternion),
        UNIT_SCALE,
      );

      if (bone.parent === null) {
        this.scratchEuler.set(
          pose.rootRotation.x,
          pose.rootRotation.y,
          pose.rootRotation.z,
          EULER_ORDER,
        );
        this.scratchMatrix.compose(
          this.scratchVector.set(
            pose.rootPosition.x,
            pose.rootPosition.y,
            pose.rootPosition.z,
          ),
          this.scratchQuaternion.setFromEuler(this.scratchEuler),
          UNIT_SCALE,
        );
        local.premultiply(this.scratchMatrix);
      } else {
        local.premultiply(this.matrices[this.skeleton.bone(bone.parent).index]);
      }

      this.quaternions[bone.index].setFromRotationMatrix(local);
    }
    return this;
  }

  matrix(name: BoneName): Matrix4 {
    return this.matrices[this.skeleton.bone(name).index];
  }

  quaternion(name: BoneName): Quaternion {
    return this.quaternions[this.skeleton.bone(name).index];
  }

  head(name: BoneName, target = new Vector3()): Vector3 {
    return target.setFromMatrixPosition(this.matrix(name));
  }

  tail(name: BoneName, target = new Vector3()): Vector3 {
    const bone = this.skeleton.bone(name);
    return target.set(0, bone.length, 0).applyMatrix4(this.matrix(name));
  }
}

const referenceSkeleton = new ThreeReferenceSkeleton();

describe('first-party skeleton production parity', () => {
  it('reproduces the Three reference canonical rest skeleton', () => {
    expect(canonicalSkeleton.names).toEqual(referenceSkeleton.bones.map((bone) => bone.name));
    expect(hgCanonicalSkeleton.names).toEqual(referenceSkeleton.bones.map((bone) => bone.name));

    for (const reference of referenceSkeleton.bones) {
      const current = canonicalSkeleton.bone(reference.name);
      const hg = hgCanonicalSkeleton.bone(reference.name);

      for (const candidate of [current, hg]) {
        expect(candidate.parent).toBe(reference.parent);
        expect(Math.abs(candidate.length - reference.length), reference.name).toBeLessThan(EPS);
      }

      expect(current.restHead.distanceTo(reference.restHead), `${reference.name}/current-head`).toBeLessThan(EPS);
      expect(current.restTail.distanceTo(reference.restTail), `${reference.name}/current-tail`).toBeLessThan(EPS);
      expect(
        hg.restHead.distanceTo(new HgVec3(reference.restHead.x, reference.restHead.y, reference.restHead.z)),
        `${reference.name}/hg-head`,
      ).toBeLessThan(EPS);
      expect(
        hg.restTail.distanceTo(new HgVec3(reference.restTail.x, reference.restTail.y, reference.restTail.z)),
        `${reference.name}/hg-tail`,
      ).toBeLessThan(EPS);

      const currentDot = Math.abs(current.restWorldQuaternion.dot(reference.restWorldQuaternion));
      const hgDot = Math.abs(
        hg.restWorldQuaternion.x * reference.restWorldQuaternion.x +
        hg.restWorldQuaternion.y * reference.restWorldQuaternion.y +
        hg.restWorldQuaternion.z * reference.restWorldQuaternion.z +
        hg.restWorldQuaternion.w * reference.restWorldQuaternion.w
      );
      expect(Math.abs(1-currentDot), `${reference.name}/current-quaternion`).toBeLessThan(EPS);
      expect(Math.abs(1-hgDot), `${reference.name}/hg-quaternion`).toBeLessThan(EPS);
    }
  });

  it('reproduces Three pose matrices across the whole exercise library', () => {
    const reference = new ThreeReferenceEvaluation(referenceSkeleton);
    const current = new PoseEvaluation(canonicalSkeleton);
    const hg = new HgPoseEvaluation(hgCanonicalSkeleton);
    let worst = 0;
    let label = '';

    for (const exercise of EXERCISES) {
      const clip = generateClip(canonicalSkeleton, exercise);
      for (const fraction of [0, 0.17, 0.33, 0.5, 0.71, 1]) {
        const pose = sampleClip(clip, clip.duration * fraction).pose;
        reference.apply(pose);
        current.apply(pose);
        hg.apply(pose);

        for (const bone of referenceSkeleton.bones) {
          const expected = reference.matrix(bone.name).elements;
          const candidates = [
            ['current', current.matrix(bone.name).elements],
            ['hg', hg.matrix(bone.name).elements],
          ] as const;
          for (const [kind, matrix] of candidates) {
            for (let index = 0; index < 16; index += 1) {
              const delta = Math.abs(expected[index] - matrix[index]);
              if (delta > worst) {
                worst = delta;
                label = `${kind}/${exercise.id}/${fraction}/${bone.name}/m${index}`;
              }
            }
          }
        }
      }
    }

    expect(worst, label).toBeLessThan(EPS);
  }, 60_000);

  it('reproduces Three head, tail and quaternion queries', () => {
    const exercise = EXERCISES[0];
    const clip = generateClip(canonicalSkeleton, exercise);
    const pose = sampleClip(clip, clip.duration * 0.43).pose;
    const reference = new ThreeReferenceEvaluation(referenceSkeleton).apply(pose);
    const current = new PoseEvaluation(canonicalSkeleton).apply(pose);
    const hg = new HgPoseEvaluation(hgCanonicalSkeleton).apply(pose);

    for (const bone of referenceSkeleton.bones) {
      const expectedHead = reference.head(bone.name);
      const expectedTail = reference.tail(bone.name);
      const currentHead = current.head(bone.name);
      const currentTail = current.tail(bone.name);
      const hgHead = hg.head(bone.name);
      const hgTail = hg.tail(bone.name);

      expect(currentHead.distanceTo(expectedHead), `${bone.name}/current-head`).toBeLessThan(EPS);
      expect(currentTail.distanceTo(expectedTail), `${bone.name}/current-tail`).toBeLessThan(EPS);
      expect(Math.hypot(
        hgHead.x-expectedHead.x,
        hgHead.y-expectedHead.y,
        hgHead.z-expectedHead.z,
      ), `${bone.name}/hg-head`).toBeLessThan(EPS);
      expect(Math.hypot(
        hgTail.x-expectedTail.x,
        hgTail.y-expectedTail.y,
        hgTail.z-expectedTail.z,
      ), `${bone.name}/hg-tail`).toBeLessThan(EPS);

      const expectedQ = reference.quaternion(bone.name);
      const currentQ = current.quaternion(bone.name);
      const hgQ = hg.quaternion(bone.name);
      expect(Math.abs(1-Math.abs(currentQ.dot(expectedQ))), `${bone.name}/current-quaternion`).toBeLessThan(EPS);
      const hgDot = Math.abs(
        hgQ.x*expectedQ.x + hgQ.y*expectedQ.y + hgQ.z*expectedQ.z + hgQ.w*expectedQ.w
      );
      expect(Math.abs(1-hgDot), `${bone.name}/hg-quaternion`).toBeLessThan(EPS);
    }
  });
});
