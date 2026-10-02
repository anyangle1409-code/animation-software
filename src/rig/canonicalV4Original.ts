import type { BoneName, Finger, MetacarpalFinger } from './boneNames';
import { FINGERS, METACARPAL_FINGERS } from './boneNames';
import type { AxisLimit, BoneDefinition, JointLimits, Vec3 } from './types';
import { vec3 } from './types';

export const HGPT_CANONICAL_V4_ORIGINAL_ID = 'hgpt_canonical_v4_original' as const;

import { HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS } from './originalDimensions';
export { HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS } from './originalDimensions';

const limit = (min: number, max: number, positive: string, negative: string): AxisLimit => ({
  min, max, positive, negative,
});
const joint = (
  x: AxisLimit | null,
  y: AxisLimit | null,
  z: AxisLimit | null,
): JointLimits => ({ x, y, z });
const free = (): JointLimits => joint(
  limit(-180, 180, 'Pitch up', 'Pitch down'),
  limit(-180, 180, 'Yaw left', 'Yaw right'),
  limit(-180, 180, 'Roll right', 'Roll left'),
);

const mirrorLimit = (axis: AxisLimit | null): AxisLimit | null => axis && ({
  min: -axis.max,
  max: -axis.min,
  positive: axis.negative,
  negative: axis.positive,
});
const mirrorLimits = (limits: JointLimits): JointLimits => ({
  x: limits.x,
  y: mirrorLimit(limits.y),
  z: mirrorLimit(limits.z),
});
const mirrorVec = (value: Vec3): Vec3 => vec3(-value.x, value.y, value.z);
const mirrorBone = (bone: BoneDefinition): BoneDefinition => {
  const swap = (name: BoneName | null): BoneName | null =>
    name?.endsWith('_l') ? `${name.slice(0, -2)}_r` as BoneName : name;
  return {
    ...bone,
    name: swap(bone.name) as BoneName,
    parent: swap(bone.parent),
    head: mirrorVec(bone.head),
    tail: mirrorVec(bone.tail),
    limits: mirrorLimits(bone.limits),
  };
};

const CENTRE: BoneDefinition[] = [
  { name: 'root', parent: null, head: vec3(0, 0, 0), tail: vec3(0, 0.22, 0), limits: free(), radius: 0.052 },
  {
    name: 'pelvis', parent: 'root', head: vec3(0, 0.99, 0), tail: vec3(0, 1.07, 0), radius: 0.12,
    limits: joint(limit(-45, 45, 'Anterior tilt', 'Posterior tilt'), limit(-45, 45, 'Rotation right', 'Rotation left'), limit(-30, 30, 'Hike left', 'Hike right')),
  },
  {
    name: 'spine_01', parent: 'pelvis', head: vec3(0, 1.07, 0), tail: vec3(0, 1.19, 0), radius: 0.108,
    limits: joint(limit(-15, 30, 'Flexion', 'Extension'), limit(-12, 12, 'Rotation right', 'Rotation left'), limit(-22, 22, 'Side bend left', 'Side bend right')),
  },
  {
    name: 'spine_02', parent: 'spine_01', head: vec3(0, 1.19, 0), tail: vec3(0, 1.33, 0), radius: 0.115,
    limits: joint(limit(-12, 25, 'Flexion', 'Extension'), limit(-20, 20, 'Rotation right', 'Rotation left'), limit(-20, 20, 'Side bend left', 'Side bend right')),
  },
  {
    name: 'spine_03', parent: 'spine_02', head: vec3(0, 1.33, 0), tail: vec3(0, 1.5, 0), radius: 0.132,
    limits: joint(limit(-10, 20, 'Flexion', 'Extension'), limit(-25, 25, 'Rotation right', 'Rotation left'), limit(-18, 18, 'Side bend left', 'Side bend right')),
  },
  {
    name: 'neck', parent: 'spine_03', head: vec3(0, 1.5, 0), tail: vec3(0, 1.61, 0), radius: 0.058,
    limits: joint(limit(-45, 40, 'Flexion', 'Extension'), limit(-55, 55, 'Rotation right', 'Rotation left'), limit(-35, 35, 'Side bend left', 'Side bend right')),
  },
  {
    name: 'head', parent: 'neck', head: vec3(0, 1.61, 0), tail: vec3(0, 1.82, 0), radius: 0.098,
    limits: joint(limit(-20, 20, 'Flexion', 'Extension'), limit(-25, 25, 'Rotation right', 'Rotation left'), limit(-15, 15, 'Side bend left', 'Side bend right')),
  },
];

const shoulderX = -HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS.shoulderBreadth / 2;
const hipX = -HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS.hipJointBreadth / 2;
const shoulderY = 1.515;
const elbowY = shoulderY - HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS.upperArmLength;
const wristY = elbowY - HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS.forearmLength;
const palmAxisEndY = wristY - HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS.wristToPalmAxisEnd;
const armZ = -0.03;

const LEFT_CORE: BoneDefinition[] = [
  {
    name: 'clavicle_l', parent: 'spine_03', head: vec3(-0.02, 1.5, 0.012), tail: vec3(shoulderX, shoulderY, armZ), radius: 0.037,
    limits: joint(limit(-18, 18, 'Protraction', 'Retraction'), null, limit(-25, 10, 'Depression', 'Elevation')),
  },
  {
    name: 'scapula_l', parent: 'clavicle_l', head: vec3(shoulderX, shoulderY, armZ), tail: vec3(-0.105, 1.3, -0.145), radius: 0.032,
    limits: joint(limit(-10, 30, 'Posterior tilt', 'Anterior tilt'), limit(-25, 25, 'External rotation', 'Internal rotation'), limit(-45, 10, 'Downward rotation', 'Upward rotation')),
  },
  {
    name: 'upperarm_l', parent: 'scapula_l', head: vec3(shoulderX, shoulderY, armZ), tail: vec3(shoulderX, elbowY, armZ), radius: 0.054,
    limits: joint(limit(-60, 180, 'Flexion', 'Extension'), limit(-90, 90, 'External rotation', 'Internal rotation'), limit(-180, 40, 'Adduction', 'Abduction')),
  },
  {
    name: 'forearm_l', parent: 'upperarm_l', head: vec3(shoulderX, elbowY, armZ), tail: vec3(shoulderX, wristY, armZ), radius: 0.043,
    limits: joint(limit(-5, 150, 'Flexion', 'Extension'), limit(-85, 85, 'Supination', 'Pronation'), null),
  },
  {
    name: 'hand_l', parent: 'forearm_l', head: vec3(shoulderX, wristY, armZ), tail: vec3(shoulderX, palmAxisEndY, armZ), radius: 0.037,
    // Same anatomical ranges as before, aligned to the shared XZY convention:
    // X flexes/extends the hand; Z carries radial/ulnar deviation.
    limits: joint(limit(-70, 80, 'Flexion', 'Extension'), null, limit(-30, 20, 'Radial deviation', 'Ulnar deviation')),
  },
  {
    name: 'thigh_l', parent: 'pelvis', head: vec3(hipX, 0.96, 0), tail: vec3(hipX, 0.515, 0), radius: 0.084,
    limits: joint(limit(-25, 125, 'Flexion', 'Extension'), limit(-40, 50, 'External rotation', 'Internal rotation'), limit(-45, 25, 'Adduction', 'Abduction')),
  },
  {
    name: 'shin_l', parent: 'thigh_l', head: vec3(hipX, 0.515, 0), tail: vec3(hipX, 0.085, 0), radius: 0.058,
    limits: joint(limit(-150, 2, 'Extension', 'Flexion'), limit(-15, 15, 'External rotation', 'Internal rotation'), null),
  },
  {
    name: 'foot_l', parent: 'shin_l', head: vec3(hipX, 0.085, 0), tail: vec3(hipX, 0.028, 0.18), radius: 0.042,
    limits: joint(limit(-45, 35, 'Dorsiflexion', 'Plantarflexion'), limit(-15, 25, 'Inversion', 'Eversion'), limit(-10, 10, 'Adduction', 'Abduction')),
  },
  {
    name: 'toe_l', parent: 'foot_l', head: vec3(hipX, 0.028, 0.18), tail: vec3(hipX, 0.02, 0.265), radius: 0.03,
    limits: joint(limit(-35, 80, 'Extension', 'Flexion'), null, null),
  },
];

interface FingerDesign {
  knuckle: Vec3;
  direction: Vec3;
  radius: number;
}

const FINGER_DESIGN: Record<Finger, FingerDesign> = {
  thumb: { knuckle: vec3(shoulderX + 0.008, wristY - 0.03, armZ + 0.025), direction: vec3(0.5, -0.58, 0.64), radius: 0.012 },
  index: { knuckle: vec3(shoulderX - 0.001, palmAxisEndY + 0.01, armZ + 0.037), direction: vec3(-0.012, -1, 0.025), radius: 0.01 },
  middle: { knuckle: vec3(shoulderX - 0.0015, palmAxisEndY + 0.008, armZ + 0.014), direction: vec3(0, -1, 0), radius: 0.0102 },
  ring: { knuckle: vec3(shoulderX - 0.001, palmAxisEndY + 0.01, armZ - 0.009), direction: vec3(0.008, -1, -0.018), radius: 0.0096 },
  pinky: { knuckle: vec3(shoulderX + 0.002, palmAxisEndY + 0.014, armZ - 0.031), direction: vec3(0.018, -1, -0.035), radius: 0.0086 },
};

const thumbBaseLimits = (): JointLimits => joint(
  limit(-85, 20, 'Extension', 'Flexion across the palm'),
  limit(-20, 20, 'Supination', 'Pronation'),
  limit(-25, 60, 'Palmar abduction', 'Retroposition'),
);
const fingerLimits = (finger: Finger, segment: number): JointLimits => {
  if (finger === 'thumb' && segment === 0) return thumbBaseLimits();
  const flexion = finger === 'thumb' ? [-25, 60] : segment === 0 ? [-30, 90] : segment === 1 ? [-5, 110] : [-5, 80];
  return joint(
    segment === 0 ? limit(-14, 14, 'Spread towards thumb', 'Spread towards little finger') : null,
    null,
    limit(flexion[0], flexion[1], 'Flexion', 'Extension'),
  );
};
const metacarpalLimits = (finger: MetacarpalFinger): JointLimits => {
  const values = {
    index: [3, 3, -3, 3],
    middle: [3, 3, -3, 3],
    ring: [5, 10, -5, 15],
    pinky: [8, 15, -5, 30],
  }[finger];
  return joint(
    limit(-values[0], values[0], 'Spread towards thumb', 'Spread towards little finger'),
    limit(-values[1], values[1], 'Rotation towards thumb', 'Rotation away from thumb'),
    limit(values[2], values[3], 'Flexion', 'Extension'),
  );
};

function buildLeftHand(): BoneDefinition[] {
  const bones: BoneDefinition[] = [];
  const centreZ = METACARPAL_FINGERS.reduce((sum, finger) => sum + FINGER_DESIGN[finger].knuckle.z, 0) / METACARPAL_FINGERS.length;
  for (const finger of FINGERS) {
    const design = FINGER_DESIGN[finger];
    if (finger !== 'thumb') {
      const metacarpal = finger as MetacarpalFinger;
      const length = HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS.metacarpals[metacarpal];
      const baseZ = centreZ + (design.knuckle.z - centreZ) * 0.48;
      const across = design.knuckle.z - baseZ;
      bones.push({
        name: `metacarpal_${finger}_l` as BoneName,
        parent: 'hand_l',
        head: vec3(design.knuckle.x, design.knuckle.y + Math.sqrt(length * length - across * across), baseZ),
        tail: design.knuckle,
        limits: metacarpalLimits(metacarpal),
        radius: design.radius * 0.9,
        minor: true,
      });
    }

    const magnitude = Math.hypot(design.direction.x, design.direction.y, design.direction.z);
    const direction = vec3(design.direction.x / magnitude, design.direction.y / magnitude, design.direction.z / magnitude);
    let head = design.knuckle;
    HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS.fingers[finger].forEach((length, segment) => {
      const tail = vec3(head.x + direction.x * length, head.y + direction.y * length, head.z + direction.z * length);
      bones.push({
        name: `${finger}_0${segment + 1}_l` as BoneName,
        parent: segment === 0
          ? finger === 'thumb' ? 'hand_l' : `metacarpal_${finger}_l` as BoneName
          : `${finger}_0${segment}_l` as BoneName,
        head,
        tail,
        limits: fingerLimits(finger, segment),
        radius: design.radius * (1 - segment * 0.13),
        minor: true,
      });
      head = tail;
    });
  }
  return bones;
}

const LEFT = [...LEFT_CORE, ...buildLeftHand()];

/** New clean-room rest geometry. It is intentionally not the active v3 rig. */
export const HGPT_CANONICAL_V4_ORIGINAL_BONES: BoneDefinition[] = [
  ...CENTRE,
  ...LEFT,
  ...LEFT.map(mirrorBone),
];
