import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from './skeleton';
import { ALL_BONES, mirrorBoneName } from './boneNames';
import { clampRotation, mirrorPose, poseFromDegrees, restPose } from './pose';
import { RIG_HEIGHT } from './humanoid';
import { toDeg, toRad } from '../core/math';

const skeleton = canonicalSkeleton;

describe('canonical skeleton', () => {
  it('defines every declared bone exactly once', () => {
    expect(skeleton.bones).toHaveLength(ALL_BONES.length);
    expect(new Set(skeleton.names).size).toBe(ALL_BONES.length);
    for (const name of ALL_BONES) expect(skeleton.has(name)).toBe(true);
  });

  it('has a single root and a connected hierarchy', () => {
    const roots = skeleton.bones.filter((bone) => bone.parent === null);
    expect(roots.map((bone) => bone.name)).toEqual(['root']);
    for (const bone of skeleton.bones) {
      expect(skeleton.chainToRoot(bone.name).at(-1)?.name).toBe('root');
    }
  });

  it('stands the mannequin on the floor at roughly human height', () => {
    const evaluation = new PoseEvaluation(skeleton).apply(restPose());
    expect(evaluation.tail('head').y).toBeCloseTo(RIG_HEIGHT, 2);
    expect(evaluation.head('foot_l').y).toBeGreaterThan(0);
    expect(evaluation.head('foot_l').y).toBeLessThan(0.12);
  });

  it('places the character’s left on -X, facing +Z', () => {
    const evaluation = new PoseEvaluation(skeleton).apply(restPose());
    expect(evaluation.head('hand_l').x).toBeLessThan(0);
    expect(evaluation.head('hand_r').x).toBeGreaterThan(0);
    expect(evaluation.tail('toe_l').z).toBeGreaterThan(evaluation.head('foot_l').z);
  });

  it('is left/right symmetric in the rest pose', () => {
    const evaluation = new PoseEvaluation(skeleton).apply(restPose());
    for (const bone of skeleton.bones) {
      if (!bone.name.endsWith('_l')) continue;
      const left = evaluation.head(bone.name, new Vector3());
      const right = evaluation.head(mirrorBoneName(bone.name), new Vector3());
      expect(right.x).toBeCloseTo(-left.x, 6);
      expect(right.y).toBeCloseTo(left.y, 6);
      expect(right.z).toBeCloseTo(left.z, 6);
    }
  });
});

describe('bone frame convention', () => {
  const evaluation = new PoseEvaluation(skeleton);

  it('bends the elbow forwards on positive x for both arms', () => {
    const rest = evaluation.apply(restPose());
    const restHand = rest.head('hand_l', new Vector3());
    const flexed = evaluation.apply(poseFromDegrees({ forearm_l: { x: 90 } }));
    const flexedHand = flexed.head('hand_l', new Vector3());
    expect(flexedHand.z).toBeGreaterThan(restHand.z + 0.15);

    const flexedRight = evaluation.apply(poseFromDegrees({ forearm_r: { x: 90 } }));
    expect(flexedRight.head('hand_r', new Vector3()).z).toBeGreaterThan(restHand.z + 0.15);
  });

  it('bends the knee backwards on negative x for both legs', () => {
    const flexed = evaluation.apply(poseFromDegrees({ shin_l: { x: -90 } }));
    expect(flexed.head('foot_l', new Vector3()).z).toBeLessThan(-0.2);
    const flexedRight = evaluation.apply(poseFromDegrees({ shin_r: { x: -90 } }));
    expect(flexedRight.head('foot_r', new Vector3()).z).toBeLessThan(-0.2);
  });

  it('raises each arm sideways on its own abduction sign', () => {
    const left = evaluation.apply(poseFromDegrees({ upperarm_l: { z: -90 } }));
    const leftHand = left.head('hand_l', new Vector3());
    expect(leftHand.y).toBeGreaterThan(1.3);
    expect(leftHand.x).toBeLessThan(-0.4);

    const right = evaluation.apply(poseFromDegrees({ upperarm_r: { z: 90 } }));
    const rightHand = right.head('hand_r', new Vector3());
    expect(rightHand.y).toBeGreaterThan(1.3);
    expect(rightHand.x).toBeGreaterThan(0.4);
  });

  it('flexes the hip forwards on positive x', () => {
    const flexed = evaluation.apply(poseFromDegrees({ thigh_l: { x: 90 } }));
    const knee = flexed.head('shin_l', new Vector3());
    expect(knee.z).toBeGreaterThan(0.35);
    expect(knee.y).toBeCloseTo(0.92, 1);
  });

  it('bends the spine forwards on positive x', () => {
    const flexed = evaluation.apply(
      poseFromDegrees({ spine_01: { x: 25 }, spine_02: { x: 25 }, spine_03: { x: 20 } }),
    );
    expect(flexed.head('neck', new Vector3()).z).toBeGreaterThan(0.15);
  });
});

describe('joint limits', () => {
  it('locks axes a joint does not have', () => {
    const elbow = skeleton.bone('forearm_l');
    const clamped = clampRotation(elbow, { x: toRad(60), y: 0, z: toRad(40) });
    expect(clamped.z).toBe(0);
    expect(toDeg(clamped.x)).toBeCloseTo(60);
  });

  it('prevents impossible joint angles', () => {
    const knee = skeleton.bone('shin_l');
    const hyperextended = clampRotation(knee, { x: toRad(80), y: 0, z: 0 });
    expect(toDeg(hyperextended.x)).toBeCloseTo(2);
    const overFlexed = clampRotation(knee, { x: toRad(-200), y: 0, z: 0 });
    expect(toDeg(overFlexed.x)).toBeCloseTo(-150);
  });

  it('mirrors handed limits between sides', () => {
    const left = skeleton.bone('upperarm_l').definition.limits;
    const right = skeleton.bone('upperarm_r').definition.limits;
    expect(right.x).toEqual(left.x);
    expect(right.z?.min).toBe(-(left.z?.max ?? 0));
    expect(right.z?.max).toBe(-(left.z?.min ?? 0));
    expect(right.z?.positive).toBe(left.z?.negative);
  });
});

describe('pose mirroring', () => {
  it('produces the geometric mirror of the original pose', () => {
    const pose = poseFromDegrees({
      upperarm_l: { x: 40, y: 20, z: 30 },
      forearm_l: { x: 95 },
      thigh_r: { x: 30, z: -10 },
    });
    const evaluation = new PoseEvaluation(skeleton);
    const original = evaluation.apply(pose).head('hand_l', new Vector3());
    const mirroredHand = evaluation.apply(mirrorPose(skeleton, pose)).head('hand_r', new Vector3());
    expect(mirroredHand.x).toBeCloseTo(-original.x, 6);
    expect(mirroredHand.y).toBeCloseTo(original.y, 6);
    expect(mirroredHand.z).toBeCloseTo(original.z, 6);
  });
});
