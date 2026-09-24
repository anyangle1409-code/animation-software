import type { BoneName } from './boneNames';
import { mirrorBoneName } from './boneNames';
import { Euler, Quaternion, Vector3 } from 'three';
import type { Axis, Pose, Vec3 } from './types';
import { AXES, EULER_ORDER, vec3 } from './types';
import type { RigBone, Skeleton } from './skeleton';
import { clamp, lerpAngle, toRad, round } from '../core/math';

export const ZERO: Vec3 = Object.freeze(vec3(0, 0, 0));

export function restPose(): Pose {
  return { rotations: {}, rootPosition: vec3(0, 0, 0), rootRotation: vec3(0, 0, 0) };
}

export function clonePose(pose: Pose): Pose {
  const rotations: Pose['rotations'] = {};
  for (const [name, rotation] of Object.entries(pose.rotations)) {
    if (rotation) rotations[name as BoneName] = { ...rotation };
  }
  return {
    rotations,
    rootPosition: { ...pose.rootPosition },
    rootRotation: { ...pose.rootRotation },
  };
}

export const boneRotation = (pose: Pose, bone: BoneName): Vec3 => pose.rotations[bone] ?? ZERO;

/** Immutably set one bone's rotation, clamped to its anatomical limits. */
export function withBoneRotation(
  skeleton: Skeleton,
  pose: Pose,
  bone: BoneName,
  rotation: Vec3,
): Pose {
  const next = clonePose(pose);
  next.rotations[bone] = clampRotation(skeleton.bone(bone), rotation);
  return next;
}

/** Immutably set one axis of one bone. */
export function withAxis(
  skeleton: Skeleton,
  pose: Pose,
  bone: BoneName,
  axis: Axis,
  radians: number,
): Pose {
  const current = boneRotation(pose, bone);
  return withBoneRotation(skeleton, pose, bone, { ...current, [axis]: radians });
}

/**
 * Clamp a rotation into the joint's anatomical range. Axes the joint does not
 * have (a hinge's twist and abduction, say) are pinned to zero, which is what
 * stops the editor and the IK solver producing impossible poses.
 */
export function clampRotation(bone: RigBone, rotation: Vec3): Vec3 {
  const out = vec3();
  for (const axis of AXES) {
    const limit = bone.definition.limits[axis];
    if (!limit) {
      out[axis] = 0;
      continue;
    }
    out[axis] = clamp(rotation[axis], toRad(limit.min), toRad(limit.max));
  }
  return out;
}

/** How far outside its limits an axis currently sits, in radians (0 if legal). */
export function limitViolation(bone: RigBone, rotation: Vec3, axis: Axis): number {
  const limit = bone.definition.limits[axis];
  if (!limit) return rotation[axis];
  const value = rotation[axis];
  if (value < toRad(limit.min)) return value - toRad(limit.min);
  if (value > toRad(limit.max)) return value - toRad(limit.max);
  return 0;
}

/** Clamp every bone in a pose. */
export function clampPose(skeleton: Skeleton, pose: Pose): Pose {
  const next = restPose();
  next.rootPosition = { ...pose.rootPosition };
  next.rootRotation = { ...pose.rootRotation };
  for (const bone of skeleton.bones) {
    const rotation = pose.rotations[bone.name];
    if (!rotation) continue;
    if (bone.parent === null) {
      next.rotations[bone.name] = { ...rotation };
      continue;
    }
    next.rotations[bone.name] = clampRotation(bone, rotation);
  }
  return next;
}

/**
 * Mirror a pose across the body's centre line. Flexion (x) is unchanged;
 * axial rotation (y) and abduction (z) flip, because those axes are handed.
 */
export function mirrorPose(skeleton: Skeleton, pose: Pose): Pose {
  const next = restPose();
  next.rootPosition = vec3(-pose.rootPosition.x, pose.rootPosition.y, pose.rootPosition.z);
  next.rootRotation = vec3(pose.rootRotation.x, -pose.rootRotation.y, -pose.rootRotation.z);
  for (const bone of skeleton.bones) {
    if (bone.parent === null) continue;
    const source = pose.rotations[mirrorBoneName(bone.name)];
    if (!source) continue;
    next.rotations[bone.name] = clampRotation(bone, vec3(source.x, -source.y, -source.z));
  }
  return next;
}

/** Copy one side of the body onto the other. */
export function mirrorSideInPlace(skeleton: Skeleton, pose: Pose, from: 'l' | 'r'): Pose {
  const next = clonePose(pose);
  for (const bone of skeleton.bones) {
    if (!bone.name.endsWith(`_${from}`)) continue;
    const target = mirrorBoneName(bone.name);
    const source = pose.rotations[bone.name] ?? ZERO;
    next.rotations[target] = clampRotation(
      skeleton.bone(target),
      vec3(source.x, -source.y, -source.z),
    );
  }
  return next;
}

/**
 * Interpolate two poses. Used by the animation sampler and by pose blending.
 *
 * The root's rotation is interpolated by angle and its position in a straight
 * line — of the root's own origin, unless a `pivot` is given. A pivot is a
 * point in the root's frame that should travel in the straight line instead,
 * with the root turning about it: a body tipping forward from the hips keeps
 * its hips on a line, where tipping about the floor under it would swing them
 * up and out. The two agree at `t = 0` and `t = 1`; only the path between
 * differs, and without a pivot nothing changes at all.
 */
export function blendPoses(a: Pose, b: Pose, t: number, pivot?: Vec3): Pose {
  const out = restPose();
  const names = new Set<BoneName>([
    ...(Object.keys(a.rotations) as BoneName[]),
    ...(Object.keys(b.rotations) as BoneName[]),
  ]);
  for (const name of names) {
    const from = a.rotations[name] ?? ZERO;
    const to = b.rotations[name] ?? ZERO;
    out.rotations[name] = vec3(
      lerpAngle(from.x, to.x, t),
      lerpAngle(from.y, to.y, t),
      lerpAngle(from.z, to.z, t),
    );
  }
  out.rootPosition = vec3(
    a.rootPosition.x + (b.rootPosition.x - a.rootPosition.x) * t,
    a.rootPosition.y + (b.rootPosition.y - a.rootPosition.y) * t,
    a.rootPosition.z + (b.rootPosition.z - a.rootPosition.z) * t,
  );
  out.rootRotation = vec3(
    lerpAngle(a.rootRotation.x, b.rootRotation.x, t),
    lerpAngle(a.rootRotation.y, b.rootRotation.y, t),
    lerpAngle(a.rootRotation.z, b.rootRotation.z, t),
  );
  if (pivot) {
    // Where the pivot is in the world at each end, on a straight line between,
    // and the root placed so the blended rotation puts the pivot there.
    const turned = (rotation: Vec3) =>
      new Vector3(pivot.x, pivot.y, pivot.z).applyQuaternion(
        new Quaternion().setFromEuler(new Euler(rotation.x, rotation.y, rotation.z, EULER_ORDER)),
      );
    const from = turned(a.rootRotation).add(new Vector3(a.rootPosition.x, a.rootPosition.y, a.rootPosition.z));
    const to = turned(b.rootRotation).add(new Vector3(b.rootPosition.x, b.rootPosition.y, b.rootPosition.z));
    const position = from.lerp(to, t).sub(turned(out.rootRotation));
    out.rootPosition = vec3(position.x, position.y, position.z);
  }
  return out;
}

/** Build a pose from degrees, which is how exercise definitions are authored. */
export function poseFromDegrees(
  entries: Partial<Record<BoneName, Partial<Vec3>>>,
  root?: { position?: Partial<Vec3>; rotation?: Partial<Vec3> },
): Pose {
  const pose = restPose();
  for (const [name, rotation] of Object.entries(entries)) {
    if (!rotation) continue;
    pose.rotations[name as BoneName] = vec3(
      toRad(rotation.x ?? 0),
      toRad(rotation.y ?? 0),
      toRad(rotation.z ?? 0),
    );
  }
  if (root?.position) {
    pose.rootPosition = vec3(
      root.position.x ?? 0,
      root.position.y ?? 0,
      root.position.z ?? 0,
    );
  }
  if (root?.rotation) {
    pose.rootRotation = vec3(
      toRad(root.rotation.x ?? 0),
      toRad(root.rotation.y ?? 0),
      toRad(root.rotation.z ?? 0),
    );
  }
  return pose;
}

/** Drop rotations that are all but zero — keeps stored poses small and legible. */
export function compactPose(pose: Pose, epsilon = 1e-5): Pose {
  const out = restPose();
  out.rootPosition = { ...pose.rootPosition };
  out.rootRotation = { ...pose.rootRotation };
  for (const [name, rotation] of Object.entries(pose.rotations)) {
    if (!rotation) continue;
    if (
      Math.abs(rotation.x) < epsilon &&
      Math.abs(rotation.y) < epsilon &&
      Math.abs(rotation.z) < epsilon
    ) {
      continue;
    }
    out.rotations[name as BoneName] = {
      x: round(rotation.x, 6),
      y: round(rotation.y, 6),
      z: round(rotation.z, 6),
    };
  }
  return out;
}

export function posesEqual(a: Pose, b: Pose, epsilon = 1e-6): boolean {
  const names = new Set<BoneName>([
    ...(Object.keys(a.rotations) as BoneName[]),
    ...(Object.keys(b.rotations) as BoneName[]),
  ]);
  for (const name of names) {
    const left = a.rotations[name] ?? ZERO;
    const right = b.rotations[name] ?? ZERO;
    if (
      Math.abs(left.x - right.x) > epsilon ||
      Math.abs(left.y - right.y) > epsilon ||
      Math.abs(left.z - right.z) > epsilon
    ) {
      return false;
    }
  }
  const axes: (keyof Vec3)[] = ['x', 'y', 'z'];
  return axes.every(
    (axis) =>
      Math.abs(a.rootPosition[axis] - b.rootPosition[axis]) <= epsilon &&
      Math.abs(a.rootRotation[axis] - b.rootRotation[axis]) <= epsilon,
  );
}
