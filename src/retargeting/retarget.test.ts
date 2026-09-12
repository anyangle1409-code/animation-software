import { describe, expect, it } from 'vitest';
import { Bone, Group, Quaternion, Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { poseFromDegrees, restPose } from '../rig/pose';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { createMapping, guessMapping, isMappingUsable, reportMapping } from './boneMap';
import { applyRetarget, bindRetarget, readCharacter, resetCharacter } from './retarget';

const skeleton = canonicalSkeleton;

/**
 * A stand-in imported character: the canonical rig rebuilt under a different
 * naming convention, optionally with a deliberately different authored rest
 * pose. Real characters often arrive A/T-posed with open, spread fingers.
 */
function buildCharacter(options: {
  names: (name: string) => string;
  tPose?: boolean;
  openHand?: boolean;
}) {
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
    if (
      options.openHand &&
      /^(thumb|index|middle|ring|pinky)_01_[lr]$/.test(rigBone.name)
    ) {
      // Fan the proximal finger bones away from the canonical hand pose. The
      // exact axis is unimportant; the point is that a canonical grip must not
      // be treated as a delta on top of this authored spread.
      const side = rigBone.name.endsWith('_l') ? 1 : -1;
      bone.quaternion.multiply(
        new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), side * 0.38),
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

  it('uses the canonical pose absolutely instead of preserving a T-pose rest', () => {
    const character = buildCharacter({ names: mixamoNames, tPose: true });
    const mapping = createMapping('T-pose', 'mixamo');
    mapping.bones = guessMapping(character.boneNames);
    const bone = (canonical: 'upperarm_l' | 'forearm_l' | 'hand_l') =>
      character.bones.get(mapping.bones[canonical]!)!;
    const worldOf = (canonical: 'upperarm_l' | 'forearm_l' | 'hand_l') =>
      new Vector3().setFromMatrixPosition(bone(canonical).matrixWorld);

    const binding = bindRetarget(character, mapping);
    const rest = restPose();
    applyRetarget(binding, rest);
    evaluation.apply(rest);

    // The source was authored with horizontal arms, but canonical zero means
    // canonical rest: the target arm must come down rather than staying in its
    // source T pose.
    const targetUpper = bone('upperarm_l').getWorldQuaternion(new Quaternion());
    expect(targetUpper.angleTo(evaluation.quaternion('upperarm_l'))).toBeLessThan(1e-5);
    expect(worldOf('forearm_l').y).toBeCloseTo(evaluation.head('forearm_l').y, 5);

    // Curling the source elbow still bends the target by the canonical amount.
    resetCharacter(character);
    const flexedPose = poseFromDegrees({ forearm_l: { x: 120 } });
    applyRetarget(binding, flexedPose);
    evaluation.apply(flexedPose);
    const shoulder = worldOf('upperarm_l');
    const elbow = worldOf('forearm_l');
    const hand = worldOf('hand_l');
    const upper = elbow.clone().sub(shoulder).normalize();
    const lower = hand.clone().sub(elbow).normalize();
    const bend = (Math.acos(Math.min(1, Math.max(-1, upper.dot(lower)))) * 180) / Math.PI;
    expect(bend).toBeCloseTo(120, 0);
  });

  it('closes an authored-open hand to the canonical grip pose', () => {
    const character = buildCharacter({ names: identityNames, openHand: true });
    const mapping = createMapping('Open hand', 'identity');
    mapping.bones = guessMapping(character.boneNames);
    const binding = bindRetarget(character, mapping);

    const pose = sampleClip(clip, 0).pose; // bicep curl includes its dumbbell grip
    applyRetarget(binding, pose);
    evaluation.apply(pose);

    // A source bone may have a different authored roll even when its anatomical
    // segment is in exactly the right place. Judge the segment direction rather
    // than comparing raw bone quaternions.
    const segments = [
      ['thumb_01_l', 'thumb_02_l'],
      ['thumb_02_l', 'thumb_03_l'],
      ['index_01_l', 'index_02_l'],
      ['middle_02_l', 'middle_03_l'],
      ['ring_02_r', 'ring_03_r'],
      ['pinky_02_r', 'pinky_03_r'],
    ] as const;
    for (const [name, child] of segments) {
      const targetHead = new Vector3().setFromMatrixPosition(character.bones.get(name)!.matrixWorld);
      const targetTail = new Vector3().setFromMatrixPosition(character.bones.get(child)!.matrixWorld);
      const targetDirection = targetTail.sub(targetHead).normalize();
      const expectedHead = evaluation.head(name, new Vector3());
      const expectedTail = evaluation.head(child, new Vector3());
      const expectedDirection = expectedTail.sub(expectedHead).normalize();
      expect(targetDirection.angleTo(expectedDirection), `${name}->${child}`).toBeLessThan(1e-5);
    }
  });

  it('puts the character back in its authored rest pose on reset', () => {
    const character = buildCharacter({ names: identityNames, tPose: true, openHand: true });
    const mapping = createMapping('Same', 'identity');
    mapping.bones = guessMapping(character.boneNames);
    const beforeArm = character.bones.get('upperarm_l')!.quaternion.clone();
    const beforeFinger = character.bones.get('index_01_l')!.quaternion.clone();

    applyRetarget(bindRetarget(character, mapping), sampleClip(clip, 2).pose);
    expect(character.bones.get('upperarm_l')!.quaternion.angleTo(beforeArm)).toBeGreaterThan(0.5);
    expect(character.bones.get('index_01_l')!.quaternion.angleTo(beforeFinger)).toBeGreaterThan(0.1);

    resetCharacter(character);
    expect(character.bones.get('upperarm_l')!.quaternion.angleTo(beforeArm)).toBeLessThan(1e-6);
    expect(character.bones.get('index_01_l')!.quaternion.angleTo(beforeFinger)).toBeLessThan(1e-6);
  });
});
