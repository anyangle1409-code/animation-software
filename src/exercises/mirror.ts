import type { BoneName } from '../rig/boneNames';
import type { Vec3 } from '../rig/types';
import type { EffectorLock, PointRef, TechniqueRule } from '../constraints/types';
import type { IKChainId } from '../ik/types';
import type { JointTarget, PoseSpec } from './types';

/**
 * Authoring primitives for the left/right halves of an exercise.
 *
 * A body is symmetric and so is almost every rule written about it, but until
 * now both halves were typed out by hand: of the 87 technique rules across the
 * five exercises, 60 are one of 30 mirror pairs. That is 30 chances to get a
 * sign backwards, and the drift is already visible — the same rule is spelled
 * `feet_planted_l` in the curl and `foot_planted_l` in the squat and the press.
 *
 * So the left side is authored and the right side is derived. Nothing here
 * invents a convention: the rig already mirrors bones and joint limits in
 * `humanoid.ts`, and the muscle model already mirrors bone-local offsets in
 * `mirrorMuscle`. This applies the same rules to the three remaining shapes —
 * poses, joint targets and technique rules — and `mirror.test.ts` holds it to
 * reproducing every right-hand half that was authored by hand.
 *
 * ## The conventions, and why each axis behaves as it does
 *
 * **Bone-local values** follow the rig. The two sides' bone frames are
 * reflections of one another, so flexion (x) keeps its sign across the body
 * while axial rotation (y) and abduction (z) reverse. A bone-local *offset* is
 * a position rather than a rotation, and reflects in x alone.
 *
 * **World-space values** — lock positions, pole targets, aim directions —
 * reflect in x and keep y and z.
 *
 * **Rule bounds** depend on what the evaluator actually measures, which is not
 * uniform and is the reason this is a module rather than a one-line helper:
 *
 * | Rule | Measured as | Bounds under mirroring |
 * |---|---|---|
 * | `jointAngle` | signed bone-local Euler | reflected on y and z, kept on x |
 * | `relativePosition` | signed world-axis delta | reflected on x, kept on y and z |
 * | `segmentAngle` | `abs(dot)` with a world axis | unchanged |
 * | `distance` | `abs` delta, or true distance | unchanged |
 * | `stationary` | drift, a length | unchanged |
 * | `alignment` | perpendicular deviation, a length | unchanged |
 * | `symmetry` | compares the two sides already | not a pair; see `bilateralRule` |
 *
 * Reflecting a range is not negation: `[min, max]` becomes `[-max, -min]`, and
 * a one-sided range swaps which side it is open on. An absent bound stays
 * absent rather than becoming `undefined`, so a derived rule is the same shape
 * as a hand-written one.
 */

/** Swap a bone's side. Centre-line bones — spine, neck, head, root — are returned unchanged. */
export function mirrorBoneName(bone: BoneName): BoneName {
  if (bone.endsWith('_l')) return `${bone.slice(0, -2)}_r` as BoneName;
  if (bone.endsWith('_r')) return `${bone.slice(0, -2)}_l` as BoneName;
  return bone;
}

/** Swap an IK chain's side. */
export function mirrorChain(chain: IKChainId): IKChainId {
  return (chain.endsWith('_l') ? `${chain.slice(0, -2)}_r` : `${chain.slice(0, -2)}_l`) as IKChainId;
}

/** Swap a trailing `_l`/`_r` on an identifier, leaving anything else alone. */
export function mirrorId(id: string): string {
  if (id.endsWith('_l')) return `${id.slice(0, -2)}_r`;
  if (id.endsWith('_r')) return `${id.slice(0, -2)}_l`;
  return id;
}

/** Swap the side named in a human-readable label, both cases. */
export function mirrorLabel(label: string): string {
  return label.replace(/\b(Left|left|Right|right)\b/g, (word) =>
    word === 'Left' ? 'Right' : word === 'left' ? 'right' : word === 'Right' ? 'Left' : 'left',
  );
}

/**
 * Negate, but return `0` rather than `-0`.
 *
 * Not cosmetic. A mirrored value is compared against the hand-written one it
 * replaces, and `-0` is a different value from `0` under `Object.is`, which is
 * what `toEqual` and every structural diff use. Without this a derived rule
 * with a zero bound reads as changed for a difference nothing can observe.
 */
const negate = (value: number): number => (value === 0 ? 0 : -value);

/** Reflect a position across the body's midline: world or bone-local alike. */
export function mirrorPosition(vector: Vec3): Vec3 {
  return { x: negate(vector.x), y: vector.y, z: vector.z };
}

/**
 * Reflect a rotation authored in a bone's own frame. Flexion keeps its sign
 * because both limbs bend the same way; the handed axes reverse.
 */
export function mirrorRotation(rotation: Partial<Vec3>): Partial<Vec3> {
  const out: Partial<Vec3> = {};
  if (rotation.x !== undefined) out.x = rotation.x;
  if (rotation.y !== undefined) out.y = negate(rotation.y);
  if (rotation.z !== undefined) out.z = negate(rotation.z);
  return out;
}

export function mirrorPoint(point: PointRef): PointRef {
  return {
    ...point,
    bone: mirrorBoneName(point.bone),
    ...(point.offset ? { offset: mirrorPosition(point.offset) } : {}),
  };
}

/** `[min, max]` under reflection becomes `[-max, -min]`; absent bounds stay absent. */
function reflectRange<T extends { min?: number; max?: number }>(range: T): T {
  const out = { ...range };
  delete out.min;
  delete out.max;
  const reflected = out as T;
  if (range.max !== undefined) reflected.min = negate(range.max);
  if (range.min !== undefined) reflected.max = negate(range.min);
  return reflected;
}

export function mirrorJointTarget(target: JointTarget): JointTarget {
  const handed = target.axis !== 'x';
  return {
    ...target,
    bone: mirrorBoneName(target.bone),
    ...(handed ? { start: negate(target.start), peak: negate(target.peak) } : {}),
    ...(handed && target.range ? { range: reflectRange(target.range) } : {}),
  };
}

export function mirrorLock(lock: EffectorLock): EffectorLock {
  return {
    ...lock,
    id: mirrorId(lock.id),
    chain: mirrorChain(lock.chain),
    // Equipment sockets are sided too — the pull-up's grips are `pullup_l` and
    // `pullup_r` on the rack — and a lock that keeps its twin's socket points
    // both hands at the same place on the bar.
    ...(lock.equipmentId ? { equipmentId: mirrorId(lock.equipmentId) } : {}),
    ...(lock.socket ? { socket: mirrorId(lock.socket) } : {}),
    ...(lock.position ? { position: mirrorPosition(lock.position) } : {}),
    ...(lock.pole ? { pole: mirrorPosition(lock.pole) } : {}),
    ...(lock.aim
      ? {
          aim: {
            direction: mirrorPosition(lock.aim.direction),
            ...(lock.aim.forward ? { forward: mirrorPosition(lock.aim.forward) } : {}),
          },
        }
      : {}),
  };
}

/** Mirror the joint rotations of a pose. The root and centre bones pass through. */
export function mirrorPoseJoints(
  joints: PoseSpec['joints'],
): PoseSpec['joints'] {
  const out: PoseSpec['joints'] = {};
  for (const [bone, rotation] of Object.entries(joints)) {
    if (!rotation) continue;
    out[mirrorBoneName(bone as BoneName)] = mirrorRotation(rotation);
  }
  return out;
}

/**
 * A pose authored on the left, completed on the right.
 *
 * Centre-line bones pass through untouched. Naming a right-hand bone as well is
 * an error rather than an override: an exercise that really is asymmetric — an
 * alternating curl, a single-arm row — should author both halves plainly and not
 * reach for this at all, and silently discarding the authored value would hide
 * exactly that intent.
 */
export function bilateralJoints(joints: PoseSpec['joints']): PoseSpec['joints'] {
  const out: PoseSpec['joints'] = { ...joints };
  for (const [bone, rotation] of Object.entries(joints)) {
    if (!rotation) continue;
    const name = bone as BoneName;
    const twin = mirrorBoneName(name);
    if (twin === name) continue;
    if (joints[twin] !== undefined) {
      throw new Error(`bilateralJoints: '${name}' and its mirror '${twin}' are both authored`);
    }
    out[twin] = mirrorRotation(rotation);
  }
  return out;
}

export function mirrorRule(rule: TechniqueRule): TechniqueRule {
  const shared = { id: mirrorId(rule.id), label: mirrorLabel(rule.label) };
  switch (rule.kind) {
    case 'jointAngle':
      // Handed axes reflect; flexion does not.
      return {
        ...(rule.axis === 'x' ? rule : reflectRange(rule)),
        ...shared,
        bone: mirrorBoneName(rule.bone),
      };
    case 'relativePosition':
      // A signed world-axis delta, so only x reflects.
      return {
        ...(rule.axis === 'x' ? reflectRange(rule) : rule),
        ...shared,
        point: mirrorPoint(rule.point),
        relativeTo: mirrorPoint(rule.relativeTo),
      };
    case 'segmentAngle':
      return { ...rule, ...shared, bone: mirrorBoneName(rule.bone) };
    case 'stationary':
      return { ...rule, ...shared, point: mirrorPoint(rule.point) };
    case 'distance':
      return { ...rule, ...shared, from: mirrorPoint(rule.from), to: mirrorPoint(rule.to) };
    case 'symmetry':
      // Already bilateral: mirroring swaps which half is which.
      return { ...rule, ...shared, left: mirrorPoint(rule.right), right: mirrorPoint(rule.left) };
    case 'alignment':
      return {
        ...rule,
        ...shared,
        points: rule.points.map(mirrorPoint) as typeof rule.points,
      };
  }
}

/**
 * The authored rule and its mirror, as a pair to spread into a `technique` list.
 *
 * The left-hand rule is written exactly as it would have been by hand, `_l`
 * suffix and "Left …" label included, so migrating an exercise is deleting the
 * right-hand half rather than rewriting the left.
 *
 * A rule that names no sided bone would produce a pointless twin, so that is an
 * authoring error rather than something to emit quietly. `symmetry` rules are
 * bilateral in themselves and are excluded for the same reason.
 */
export function bilateralRule(left: TechniqueRule): [TechniqueRule, TechniqueRule] {
  const right = mirrorRule(left);
  if (left.kind === 'symmetry') {
    throw new Error(`bilateralRule: '${left.id}' is a symmetry rule, which already spans both sides`);
  }
  if (JSON.stringify({ ...left, id: '', label: '' }) === JSON.stringify({ ...right, id: '', label: '' })) {
    throw new Error(`bilateralRule: '${left.id}' names no sided bone, so its mirror would be a duplicate`);
  }
  return [left, right];
}

/** The authored joint target and its mirror. */
export function bilateralJointTarget(left: JointTarget): [JointTarget, JointTarget] {
  return [left, mirrorJointTarget(left)];
}

/** The authored lock and its mirror. */
export function bilateralLock(left: EffectorLock): [EffectorLock, EffectorLock] {
  return [left, mirrorLock(left)];
}

/**
 * Per-bone phase timing, authored on the left and completed on the right.
 *
 * Timing carries no handedness — a delay, a finish point and an easing curve
 * mean the same thing on either arm — so only the bone name moves. An exercise
 * that deliberately staggers the two sides, an alternating curl, authors both
 * halves plainly instead, and the same both-authored guard applies.
 */
export function bilateralTiming<T>(
  timing: Partial<Record<BoneName, T>>,
): Partial<Record<BoneName, T>> {
  const out: Partial<Record<BoneName, T>> = { ...timing };
  for (const [bone, value] of Object.entries(timing) as [BoneName, T][]) {
    const twin = mirrorBoneName(bone);
    if (twin === bone) continue;
    if (timing[twin] !== undefined) {
      throw new Error(`bilateralTiming: '${bone}' and its mirror '${twin}' are both authored`);
    }
    out[twin] = value;
  }
  return out;
}
