import { Bone, Group, Quaternion, Vector3 } from 'three';
import type { ExerciseDefinition } from '../exercises/types';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { airSquat } from '../exercises/definitions/airSquat';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { pullUp } from '../exercises/definitions/pullUp';
import { pushUp } from '../exercises/definitions/pushUp';
import { shoulderPress } from '../exercises/definitions/shoulderPress';
import type { BoneName } from '../rig/boneNames';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { createMapping, guessMapping } from './boneMap';
import { applyRetarget, bindRetarget, readCharacter } from './retarget';
import { describe, expect, it } from 'vitest';

const rig = canonicalSkeleton;
const MAX_DIRECTION_ERROR = 0.01; // radians, about 0.57 degrees

/**
 * Build a deliberately non-canonical imported rest pose.  This is not meant to
 * look pretty: it makes the arms, legs, torso, wrists and fingers start from
 * different authored rotations so a delta-based retargeter cannot accidentally
 * pass.  The absolute retargeter must still reproduce every exercise pose.
 */
function biasedCharacter() {
  const root = new Group();
  const bones = new Map<BoneName, Bone>();

  const rotate = (bone: Bone, axis: Vector3, degrees: number) => {
    bone.quaternion.multiply(
      new Quaternion().setFromAxisAngle(axis, (degrees * Math.PI) / 180),
    );
  };

  for (const definition of rig.bones) {
    const bone = new Bone();
    bone.name = definition.name;
    bone.position.copy(definition.offset);
    bone.quaternion.copy(definition.restLocalQuaternion);

    const side = definition.name.endsWith('_l') ? 1 : definition.name.endsWith('_r') ? -1 : 0;
    if (definition.name === 'spine_01') rotate(bone, new Vector3(1, 0, 0), 9);
    if (definition.name === 'spine_02') rotate(bone, new Vector3(0, 0, 1), -7);
    if (/^upperarm_[lr]$/.test(definition.name)) rotate(bone, new Vector3(0, 0, 1), side * 48);
    if (/^forearm_[lr]$/.test(definition.name)) rotate(bone, new Vector3(1, 0, 0), 17);
    if (/^hand_[lr]$/.test(definition.name)) rotate(bone, new Vector3(0, 0, 1), side * 14);
    if (/^thigh_[lr]$/.test(definition.name)) rotate(bone, new Vector3(1, 0, 0), side * 18);
    if (/^shin_[lr]$/.test(definition.name)) rotate(bone, new Vector3(1, 0, 0), -11);
    if (/^foot_[lr]$/.test(definition.name)) rotate(bone, new Vector3(1, 0, 0), 8);
    if (/^(thumb|index|middle|ring|pinky)_01_[lr]$/.test(definition.name)) {
      rotate(bone, new Vector3(1, 0, 0), side * 18);
    }

    bones.set(definition.name, bone);
    if (definition.parent) bones.get(definition.parent)!.add(bone);
    else root.add(bone);
  }

  root.updateMatrixWorld(true);
  return readCharacter(root);
}

function certifyExercise(definition: ExerciseDefinition, names: BoneName[]) {
  const character = biasedCharacter();
  const mapping = createMapping(`Certification: ${definition.name}`, 'identity');
  mapping.bones = guessMapping(character.boneNames);
  const binding = bindRetarget(character, mapping);
  const clip = generateClip(rig, definition);
  const evaluation = new PoseEvaluation(rig);

  for (const fraction of [0, 0.2, 0.45, 0.7, 0.95]) {
    const pose = sampleClip(clip, clip.duration * fraction).pose;
    applyRetarget(binding, pose);
    evaluation.apply(pose);

    for (const name of names) {
      const child = rig.bone(name).children[0];
      expect(child, `${name} must have a child for direction certification`).toBeDefined();
      const targetName = mapping.bones[name]!;
      const targetChild = mapping.bones[child]!;
      const targetHead = new Vector3().setFromMatrixPosition(
        character.bones.get(targetName)!.matrixWorld,
      );
      const targetTail = new Vector3().setFromMatrixPosition(
        character.bones.get(targetChild)!.matrixWorld,
      );
      const targetDirection = targetTail.sub(targetHead).normalize();
      const expectedHead = evaluation.head(name, new Vector3());
      const expectedTail = evaluation.head(child, new Vector3());
      const expectedDirection = expectedTail.sub(expectedHead).normalize();

      // We certify the anatomical segment direction, not source-bone roll.
      // A sub-degree allowance covers floating point and authored frame
      // differences while still failing the old delta-based A/T-pose error by
      // a very large margin.
      expect(
        targetDirection.angleTo(expectedDirection),
        `${definition.id} ${name} at ${fraction}`,
      ).toBeLessThan(MAX_DIRECTION_ERROR);
    }
  }
}

describe('whole-body imported-character movement certification', () => {
  it('certifies the squat chain: torso, hips, knees and ankles', () => {
    certifyExercise(airSquat, [
      'spine_01',
      'spine_02',
      'thigh_l',
      'shin_l',
      'foot_l',
      'thigh_r',
      'shin_r',
      'foot_r',
    ]);
  });

  it('certifies the bicep curl chain: upper arm, elbow, wrist and fingers', () => {
    certifyExercise(bicepCurl, [
      'upperarm_l',
      'forearm_l',
      'hand_l',
      'index_01_l',
      'upperarm_r',
      'forearm_r',
      'hand_r',
      'index_01_r',
    ]);
  });

  it('certifies overhead pressing through the shoulder, elbow and wrist', () => {
    certifyExercise(shoulderPress, [
      'spine_02',
      'upperarm_l',
      'forearm_l',
      'hand_l',
      'upperarm_r',
      'forearm_r',
      'hand_r',
    ]);
  });

  it('certifies pushing through the torso, shoulders, elbows and wrists', () => {
    certifyExercise(pushUp, [
      'spine_02',
      'spine_03',
      'upperarm_l',
      'forearm_l',
      'hand_l',
      'upperarm_r',
      'forearm_r',
      'hand_r',
    ]);
  });

  it('certifies overhead pulling through the torso, shoulders and elbows', () => {
    certifyExercise(pullUp, [
      'spine_02',
      'spine_03',
      'upperarm_l',
      'forearm_l',
      'upperarm_r',
      'forearm_r',
    ]);
  });
});
