import { describe, expect, it } from 'vitest';
import { Bone, Group, Quaternion, Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { poseFromDegrees, restPose } from '../rig/pose';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { createMapping, guessMapping, isMappingUsable, reportMapping } from './boneMap';
import { applyRetarget, bindRetarget, readCharacter, resetCharacter, retargetedBoneMatrix } from './retarget';
import { resolveRetargetedEquipment } from '../equipment/attach';

const skeleton = canonicalSkeleton;

/**
 * A stand-in imported character: the canonical rig rebuilt under a different
 * naming convention, optionally with its arms in a T-pose so the rest poses of
 * the two rigs genuinely differ.
 */
function buildCharacter(options: { names: (name: string) => string; tPose?: boolean }) {
  const group = new Group();
  const bones = new Map<string, Bone>();

  for (const rigBone of skeleton.bones) {
    const bone = new Bone();
    bone.name = options.names(rigBone.name);
    bone.position.copy(rigBone.offset);
    bone.quaternion.copy(rigBone.restLocalQuaternion);
    if (options.tPose && (rigBone.name === 'upperarm_l' || rigBone.name === 'upperarm_r')) {
      // Raise the arms to horizontal: a genuinely different rest pose.
      const side = rigBone.name.endsWith('_l') ? -1 : 1;
      bone.quaternion.multiply(
        new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), (side * Math.PI) / 2),
      );
    }
    bones.set(rigBone.name, bone);
    if (rigBone.parent) bones.get(rigBone.parent)!.add(bone);
    else group.add(bone);
  }
  group.updateMatrixWorld(true);
  return readCharacter(group);
}

const identityNames = (name: string) => name;
const mixamoNames = (name: string): string => {
  const map: Record<string, string> = {
    pelvis: 'mixamorig:Hips',
    spine_01: 'mixamorig:Spine',
    spine_02: 'mixamorig:Spine1',
    spine_03: 'mixamorig:Spine2',
    neck: 'mixamorig:Neck',
    head: 'mixamorig:Head',
    clavicle_l: 'mixamorig:LeftShoulder',
    upperarm_l: 'mixamorig:LeftArm',
    forearm_l: 'mixamorig:LeftForeArm',
    hand_l: 'mixamorig:LeftHand',
    clavicle_r: 'mixamorig:RightShoulder',
    upperarm_r: 'mixamorig:RightArm',
    forearm_r: 'mixamorig:RightForeArm',
    hand_r: 'mixamorig:RightHand',
    thigh_l: 'mixamorig:LeftUpLeg',
    shin_l: 'mixamorig:LeftLeg',
    foot_l: 'mixamorig:LeftFoot',
    toe_l: 'mixamorig:LeftToeBase',
    thigh_r: 'mixamorig:RightUpLeg',
    shin_r: 'mixamorig:RightLeg',
    foot_r: 'mixamorig:RightFoot',
    toe_r: 'mixamorig:RightToeBase',
  };
  return map[name] ?? `bone_${name}`;
};

describe('bone mapping', () => {
  it('recognises a Mixamo naming convention', () => {
    const character = buildCharacter({ names: mixamoNames });
    const mapping = createMapping('Test', 'mixamo');
    mapping.bones = guessMapping(character.boneNames);

    expect(mapping.bones.pelvis).toBe('mixamorig:Hips');
    expect(mapping.bones.upperarm_l).toBe('mixamorig:LeftArm');
    expect(mapping.bones.forearm_r).toBe('mixamorig:RightForeArm');
    expect(mapping.bones.foot_l).toBe('mixamorig:LeftFoot');
    expect(isMappingUsable(mapping)).toBe(true);
  });

  it('leaves bones it cannot identify blank rather than guessing', () => {
    const mapping = createMapping('Sparse', 'unknown');
    mapping.bones = guessMapping(['Hips', 'Spine', 'Blob_A', 'Blob_B']);
    expect(mapping.bones.pelvis).toBe('Hips');
    expect(mapping.bones.hand_l).toBeUndefined();
    expect(isMappingUsable(mapping)).toBe(false);
    expect(reportMapping(mapping).missingRequired).toContain('hand_l');
  });

  it('never maps two canonical bones onto the same character bone', () => {
    const character = buildCharacter({ names: mixamoNames });
    const bones = guessMapping(character.boneNames);
    const used = Object.values(bones);
    expect(new Set(used).size).toBe(used.length);
  });
});

describe('retargeting', () => {
  const evaluation = new PoseEvaluation(skeleton);
  const clip = generateClip(skeleton, bicepCurl);

  it('reproduces the pose exactly on a rig with the same rest pose', () => {
    const character = buildCharacter({ names: identityNames });
    const mapping = createMapping('Same', 'identity');
    mapping.bones = guessMapping(character.boneNames);

    const pose = sampleClip(clip, 2).pose;
    applyRetarget(bindRetarget(character, mapping), pose);
    evaluation.apply(pose);

    for (const name of ['hand_l', 'forearm_r', 'foot_l', 'head'] as const) {
      const target = new Vector3().setFromMatrixPosition(character.bones.get(name)!.matrixWorld);
      expect(target.distanceTo(evaluation.head(name, new Vector3())), name).toBeLessThan(1e-6);
    }
  });

  it('carries the movement onto a T-posed rig rather than copying raw angles', () => {
    const character = buildCharacter({ names: mixamoNames, tPose: true });
    const mapping = createMapping('T-pose', 'mixamo');
    mapping.bones = guessMapping(character.boneNames);
    const bone = (canonical: 'upperarm_l' | 'forearm_l' | 'hand_l') =>
      character.bones.get(mapping.bones[canonical]!)!;
    const worldOf = (canonical: 'upperarm_l' | 'forearm_l' | 'hand_l') =>
      new Vector3().setFromMatrixPosition(bone(canonical).matrixWorld);

    // Applying the source rest pose must leave the character in its own rest
    // pose — arms horizontal — not drag it into the source's arms-down pose.
    const binding = bindRetarget(character, mapping);
    applyRetarget(binding, restPose());
    const elbowAtRest = worldOf('forearm_l');
    expect(elbowAtRest.y).toBeGreaterThan(1.35);
    expect(elbowAtRest.x).toBeLessThan(-0.4);

    // Curling the source elbow bends the target's elbow by the same angle,
    // even though the two arms start from completely different orientations.
    resetCharacter(character);
    applyRetarget(binding, poseFromDegrees({ forearm_l: { x: 120 } }));
    const shoulder = worldOf('upperarm_l');
    const elbow = worldOf('forearm_l');
    const hand = worldOf('hand_l');
    const upper = elbow.clone().sub(shoulder).normalize();
    const lower = hand.clone().sub(elbow).normalize();
    const bend = (Math.acos(Math.min(1, Math.max(-1, upper.dot(lower)))) * 180) / Math.PI;
    expect(bend).toBeCloseTo(120, 0);
  });

  it('puts the character back in its rest pose on reset', () => {
    const character = buildCharacter({ names: identityNames });
    const mapping = createMapping('Same', 'identity');
    mapping.bones = guessMapping(character.boneNames);
    const before = character.bones.get('forearm_l')!.quaternion.clone();

    applyRetarget(bindRetarget(character, mapping), sampleClip(clip, 2).pose);
    expect(character.bones.get('forearm_l')!.quaternion.angleTo(before)).toBeGreaterThan(0.5);

    resetCharacter(character);
    expect(character.bones.get('forearm_l')!.quaternion.angleTo(before)).toBeLessThan(1e-6);
  });

  it('applies and resets root translation and rotation on the character root', () => {
    const character = buildCharacter({ names: identityNames });
    character.root.position.set(2, 3, 4);
    character.root.rotation.set(0, 0.2, 0);
    character.root.updateMatrixWorld(true);
    character.rootRestPosition.copy(character.root.position);
    character.rootRestQuaternion.copy(character.root.quaternion);
    const mapping = createMapping('Root motion', 'identity');
    mapping.bones = guessMapping(character.boneNames);
    const binding = bindRetarget(character, mapping);
    const pose = restPose();
    pose.rootPosition = { x: 0.1, y: -0.2, z: 0.3 };
    pose.rootRotation = { x: 0, y: 0.4, z: 0 };

    applyRetarget(binding, pose);
    expect(character.root.position.x).toBeCloseTo(2 + 0.1 * binding.scale, 6);
    expect(character.root.position.y).toBeCloseTo(3 - 0.2 * binding.scale, 6);
    expect(character.root.quaternion.angleTo(binding.rootRestQuaternion)).toBeGreaterThan(0.35);

    resetCharacter(character);
    expect(character.root.position.distanceTo(binding.rootRestPosition)).toBeLessThan(1e-8);
    expect(character.root.quaternion.angleTo(binding.rootRestQuaternion)).toBeLessThan(1e-7);
  });

  it('places hand-held equipment from the retargeted hand frame', () => {
    const character = buildCharacter({ names: mixamoNames, tPose: true });
    const mapping = createMapping('Equipment', 'mixamo');
    mapping.bones = guessMapping(character.boneNames);
    const binding = bindRetarget(character, mapping);
    applyRetarget(binding, sampleClip(clip, 2).pose);

    const transforms = resolveRetargetedEquipment(binding, clip.equipment);
    const expected = new Vector3(0, 0.045, 0).applyMatrix4(
      retargetedBoneMatrix(binding, 'hand_l')!,
    );
    expect(transforms.get('dumbbell_l')!.position.distanceTo(expected)).toBeLessThan(1e-6);
  });
});
