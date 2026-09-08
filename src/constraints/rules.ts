import { Vector3 } from 'three';
import type { PoseEvaluation } from '../rig/skeleton';
import type { Pose } from '../rig/types';
import { toDeg } from '../core/math';
import { boneLabel } from '../rig/boneNames';
import { resolvePoint } from './points';
import type { ReferenceDirection, RuleViolation, TechniqueRule } from './types';

const REFERENCE_VECTORS: Record<ReferenceDirection, Vector3> = {
  vertical: new Vector3(0, 1, 0),
  forward: new Vector3(0, 0, 1),
  lateral: new Vector3(1, 0, 0),
};

export interface RuleContext {
  /** Clip time this frame sits at, for reporting. */
  time: number;
  /** Phase the frame belongs to, so phase-scoped rules can opt out. */
  phase?: string;
  /** The pose at the start of the clip, used by `stationary` rules. */
  reference?: PoseEvaluation;
}

const scratchA = new Vector3();
const scratchB = new Vector3();
const scratchC = new Vector3();

/**
 * Check one frame against a set of technique rules.
 *
 * Rules describe the exercise's own standards — "elbows stay below the
 * shoulders", "feet stay planted", "torso stays upright" — and come from the
 * exercise definition, so the same data drives both the checker and the UI.
 */
export function evaluateRules(
  evaluation: PoseEvaluation,
  pose: Pose,
  rules: TechniqueRule[],
  context: RuleContext,
): RuleViolation[] {
  const violations: RuleViolation[] = [];
  for (const rule of rules) {
    if (rule.phases && context.phase && !rule.phases.includes(context.phase)) continue;
    const violation = evaluateRule(evaluation, pose, rule, context);
    if (violation) violations.push(violation);
  }
  return violations;
}

function evaluateRule(
  evaluation: PoseEvaluation,
  pose: Pose,
  rule: TechniqueRule,
  context: RuleContext,
): RuleViolation | null {
  const severity = rule.severity ?? 'warning';
  const fail = (message: string, amount: number): RuleViolation => ({
    ruleId: rule.id,
    label: rule.label,
    severity,
    message,
    amount,
    time: context.time,
  });

  switch (rule.kind) {
    case 'jointAngle': {
      const degrees = toDeg(pose.rotations[rule.bone]?.[rule.axis] ?? 0);
      const over = outside(degrees, rule.min, rule.max);
      if (over === 0) return null;
      return fail(
        `${boneLabel(rule.bone)} ${rule.axis} at ${degrees.toFixed(1)}°, ${describeRange(rule.min, rule.max, '°')}`,
        over,
      );
    }
    case 'segmentAngle': {
      const bone = evaluation.skeleton.bone(rule.bone);
      evaluation.head(rule.bone, scratchA);
      evaluation.tail(rule.bone, scratchB);
      scratchC.subVectors(scratchB, scratchA).normalize();
      const reference = REFERENCE_VECTORS[rule.reference];
      // The acute angle to the axis: a shin pointing down is 0° from vertical,
      // not 180°, which is what anyone reading the rule means by it.
      const degrees = toDeg(Math.acos(Math.min(1, Math.abs(scratchC.dot(reference)))));
      const over = outside(degrees, rule.min, rule.max);
      if (over === 0) return null;
      return fail(
        `${boneLabel(bone.name)} is ${degrees.toFixed(1)}° from ${rule.reference}, ${describeRange(rule.min, rule.max, '°')}`,
        over,
      );
    }
    case 'stationary': {
      if (!context.reference) return null;
      resolvePoint(evaluation, rule.point, scratchA);
      resolvePoint(context.reference, rule.point, scratchB);
      const drift = scratchA.distanceTo(scratchB);
      if (drift <= rule.tolerance) return null;
      return fail(
        `${boneLabel(rule.point.bone)} moved ${(drift * 100).toFixed(1)} cm (limit ${(rule.tolerance * 100).toFixed(1)} cm)`,
        drift - rule.tolerance,
      );
    }
    case 'distance': {
      resolvePoint(evaluation, rule.from, scratchA);
      resolvePoint(evaluation, rule.to, scratchB);
      const measured = rule.axis
        ? Math.abs(scratchA[rule.axis] - scratchB[rule.axis])
        : scratchA.distanceTo(scratchB);
      const over = outside(measured, rule.min, rule.max);
      if (over === 0) return null;
      return fail(
        `Distance ${(measured * 100).toFixed(1)} cm, ${describeRange(rule.min, rule.max, ' cm', 100)}`,
        over,
      );
    }
    case 'relativePosition': {
      resolvePoint(evaluation, rule.point, scratchA);
      resolvePoint(evaluation, rule.relativeTo, scratchB);
      const delta = scratchA[rule.axis] - scratchB[rule.axis];
      const over = outside(delta, rule.min, rule.max);
      if (over === 0) return null;
      return fail(
        `${boneLabel(rule.point.bone)} is ${(delta * 100).toFixed(1)} cm from ${boneLabel(rule.relativeTo.bone)} on ${rule.axis}, ${describeRange(rule.min, rule.max, ' cm', 100)}`,
        over,
      );
    }
    case 'symmetry': {
      resolvePoint(evaluation, rule.left, scratchA);
      resolvePoint(evaluation, rule.right, scratchB);
      // Mirror the right-hand point and compare: a symmetric pose puts them together.
      scratchB.x = -scratchB.x;
      const difference = scratchA.distanceTo(scratchB);
      if (difference <= rule.tolerance) return null;
      return fail(
        `Left and right differ by ${(difference * 100).toFixed(1)} cm (limit ${(rule.tolerance * 100).toFixed(1)} cm)`,
        difference - rule.tolerance,
      );
    }
    case 'alignment': {
      const [first, middle, last] = rule.points;
      resolvePoint(evaluation, first, scratchA);
      resolvePoint(evaluation, middle, scratchB);
      resolvePoint(evaluation, last, scratchC);
      const line = scratchC.clone().sub(scratchA);
      const length = line.length();
      if (length < 1e-6) return null;
      line.divideScalar(length);
      const offset = scratchB.clone().sub(scratchA);
      const deviation = offset.addScaledVector(line, -offset.dot(line)).length();
      if (deviation <= rule.tolerance) return null;
      return fail(
        `${boneLabel(middle.bone)} is ${(deviation * 100).toFixed(1)} cm out of line (limit ${(rule.tolerance * 100).toFixed(1)} cm)`,
        deviation - rule.tolerance,
      );
    }
    default:
      return null;
  }
}

/** Signed distance outside [min, max]; zero when inside. */
function outside(value: number, min?: number, max?: number): number {
  if (min !== undefined && value < min) return value - min;
  if (max !== undefined && value > max) return value - max;
  return 0;
}

function describeRange(min: number | undefined, max: number | undefined, unit: string, scale = 1): string {
  const format = (value: number) => `${(value * scale).toFixed(unit === '°' ? 0 : 1)}${unit}`;
  if (min !== undefined && max !== undefined) return `allowed ${format(min)} to ${format(max)}`;
  if (min !== undefined) return `minimum ${format(min)}`;
  if (max !== undefined) return `maximum ${format(max)}`;
  return 'unconstrained';
}

/** Collapse per-frame violations into one entry per rule, worst frame first. */
export function summariseViolations(violations: RuleViolation[]): RuleViolation[] {
  const worst = new Map<string, RuleViolation>();
  for (const violation of violations) {
    const existing = worst.get(violation.ruleId);
    if (!existing || Math.abs(violation.amount) > Math.abs(existing.amount)) {
      worst.set(violation.ruleId, violation);
    }
  }
  return [...worst.values()].sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount));
}
