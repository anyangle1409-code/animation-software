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
import type { BoneMapping } from './boneMap';
import { createMapping, guessMapping } from './boneMap';
import type { TargetCharacter } from './retarget';
import { applyRetarget, bindRetarget, readCharacter } from './retarget';
import { describe, expect, it } from 'vitest';

const rig = canonicalSkeleton;
const MAX_DIRECTION_ERROR = 0.01; // radians, about 0.57 degrees
const MAX_PALM_DIRECTION_ERROR = 0.015; // radians, about 0.86 degrees

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

function palmRoots(side: 'l' | 'r'): BoneName[] {
  return [`index_01_${side}`, `middle_01_${side}`, `ring_01_${side}`, `pinky_01_${side}`] as BoneName[];
}

/**
 * Return an anatomical segment direction on the imported character.  Most
 * bones end at the next canonical joint.  Hands are different: their bone tail
 * sits through the centre of the palm while the hierarchy fans directly into
 * five digits, so we use the four finger knuckles rather than the thumb child.
 */
function targetDirection(
  character: TargetCharacter,
  mapping: BoneMapping,
  name: BoneName,
): Vector3 {
  const targetName = mapping.bones[name]!;
  const head = new Vector3().setFromMatrixPosition(character.bones.get(targetName)!.matrixWorld);

  if (name === 'hand_l' || name === 'hand_r') {
    const side = name.endsWith('_l') ? 'l' : 'r';
    const palm = new Vector3();
    for (const root of palmRoots(side)) {
      const mapped = mapping.bones[root]!;
      palm.add(new Vector3().setFromMatrixPosition(character.bones.get(mapped)!.matrixWorld));
    }
    palm.multiplyScalar(0.25);
    return palm.sub(head).normalize();
  }

  const child = rig.bone(name).children[0];
  expect(child, `${name} must have a child for direction certification`).toBeDefined();
  const mappedChild = mapping.bones[child]!;
  const tail = new Vector3().setFromMatrixPosition(character.bones.get(mappedChild)!.matrixWorld);
  return tail.sub(head).normalize();
}

function expectedDirection(evaluation: PoseEvaluation, name: BoneName): Vector3 {
  const head = evaluation.head(name, new Vector3());

  if (name === 'hand_l' || name === 'hand_r') {
    const side = name.endsWith('_l') ? 'l' : 'r';
    const palm = new Vector3();
    for (const root of palmRoots(side)) palm.add(evaluation.head(root, new Vector3()));
    palm.multiplyScalar(0.25);
    return palm.sub(head).normalize();
  }

  const child = rig.bone(name).children[0];
  expect(child, `${name} must have a child for direction certification`).toBeDefined();
  return evaluation.head(child, new Vector3()).sub(head).normalize();
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
      // We certify the anatomical segment direction, not source-bone roll.
      // The hand has no explicit tail node on common rigs, so its centreline is
      // reconstructed from the four finger knuckles; allow that approximation
      // slightly under one degree. Other segments stay under ~0.57 degrees.
      const tolerance = name === 'hand_l' || name === 'hand_r'
        ? MAX_PALM_DIRECTION_ERROR
        : MAX_DIRECTION_ERROR;
      expect(
        targetDirection(character, mapping, name).angleTo(expectedDirection(evaluation, name)),
        `${definition.id} ${name} at ${fraction}`,
      ).toBeLessThan(tolerance);
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
