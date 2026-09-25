import { Vector3 } from 'three';
import type { StudioClip } from '../animation/clip';
import { sampleClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import {
  ARM_TRUNK_SLACK,
  measureArmTrunkSeparation,
  measureEquipmentClearance,
} from '../constraints/bodyClearance';
import type { CharacterBuild } from '../character';
import { toDeg } from '../core/math';
import { reviewExercise } from '../editor/review';
import type { ExerciseDefinition } from '../exercises/types';
import { repetitionDuration } from '../exercises/types';
import type { BoneName } from '../rig/boneNames';
import { PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';

/**
 * Every automatic check a generated exercise must pass, in one report.
 *
 * Nothing here is new policy. Each check is one the library is already held
 * to, at the library's own limits, called rather than copied:
 *
 * - technique rules, loop closure, IK reachability, locked contacts and the
 *   dumbbell grip envelope come from `editor/review.ts`'s `reviewExercise`;
 * - joint limits, lock stillness, duration and rule references are the checks
 *   `exercises/exercises.test.ts` runs, and flat feet the one in
 *   `exercises/feet.test.ts`, at the same tolerances;
 * - equipment clearance and arm–trunk separation are measured on the character
 *   by `constraints/bodyClearance.ts`, which the library's tests also call.
 *
 * The arm–trunk check is the one that needs a reference. The library holds each
 * exercise to its own recorded separation, because real arms rest against real
 * chests and no shared floor separates good from bad. A candidate has no record,
 * so it is held to the library exercise it is closest to — measured live, on
 * the same character, so the comparison is like for like whichever character
 * is loaded — with the same 1 mm slack.
 *
 * The correction loop reads this report and cannot change any limit in it.
 */

export type CheckId =
  | 'technique'
  | 'loop'
  | 'ik'
  | 'contacts'
  | 'grip'
  | 'twoHandGrip'
  | 'jointLimits'
  | 'lockDrift'
  | 'feetFlat'
  | 'duration'
  | 'references'
  | 'equipmentClearance'
  | 'armTrunk';

/** How each check reads in a report or a correction message. */
export const CHECK_LABELS: Record<CheckId, string> = {
  technique: 'Technique rules',
  loop: 'Loop closure',
  ik: 'IK reachability',
  contacts: 'Locked contacts',
  grip: 'Dumbbell grip envelope',
  twoHandGrip: 'Two-hand equipment fit',
  jointLimits: 'Joint limits',
  lockDrift: 'Locked contacts stay put',
  feetFlat: 'Feet flat and square',
  duration: 'Clip matches its tempo',
  references: 'Rules, errors and muscles consistent',
  equipmentClearance: 'Equipment clears the body',
  armTrunk: 'Arms clear the trunk',
};

export interface CandidateCheck {
  id: CheckId;
  label: string;
  status: 'pass' | 'fail' | 'skipped';
  detail: string;
  /** The deciding measurement, in the check's own unit, for comparing attempts. */
  measured?: number;
}

export interface CandidateReport {
  checks: CandidateCheck[];
  /** Every check ran and passed. */
  passed: boolean;
  failed: CheckId[];
  /** Checks that could not run — the body checks without a character. */
  skipped: CheckId[];
  character: string | null;
}

export interface ValidationContext {
  rig: Skeleton;
  /** The character the body checks measure. Without one they are skipped, and the candidate cannot be certified. */
  character?: { build: CharacterBuild; label: string };
  /** The library exercise a candidate is compared with. */
  reference?: ExerciseDefinition;
  /** Only these checks, for a correction loop re-testing what it changed. */
  only?: CheckId[];
}

const mm = (metres: number) => `${(metres * 1000).toFixed(2)} mm`;

/** Every rotation inside its bone's limit, locked axes still, at 21 samples. */
function jointLimits(rig: Skeleton, clip: StudioClip): CandidateCheck {
  const evaluation = new PoseEvaluation(rig);
  let worst = 0;
  let where = '';
  for (let index = 0; index <= 20; index += 1) {
    const time = (index / 20) * clip.duration;
    const frame = resolveFrame(rig, evaluation, clip, time);
    for (const [name, rotation] of Object.entries(frame.pose.rotations)) {
      if (!rotation) continue;
      const bone = rig.bone(name as BoneName);
      for (const axis of ['x', 'y', 'z'] as const) {
        const limit = bone.definition.limits[axis];
        const degrees = toDeg(rotation[axis]);
        const over = limit ? Math.max(limit.min - degrees, degrees - limit.max, 0) : Math.abs(degrees);
        if (over > 1e-6 && over > worst) {
          worst = over;
          where = `${name}.${axis} ${degrees.toFixed(2)}° at ${time.toFixed(2)}s (${limit ? `${limit.min}° to ${limit.max}°` : 'locked axis'})`;
        }
      }
    }
  }
  return {
    id: 'jointLimits',
    label: 'Joint limits',
    status: worst === 0 ? 'pass' : 'fail',
    detail: worst === 0 ? 'Every sampled rotation is inside its joint limit.' : `${worst.toFixed(2)}° past the limit: ${where}.`,
    measured: worst,
  };
}

/** Each locked contact within 5 mm of where it started, at 41 samples. */
function lockDrift(rig: Skeleton, clip: StudioClip): CandidateCheck {
  if (clip.locks.length === 0) {
    return { id: 'lockDrift', label: 'Locked contacts stay put', status: 'pass', detail: 'No locks.', measured: 0 };
  }
  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  const start = new Map<string, Vector3>();
  let worst = 0;
  let where = '';
  for (let index = 0; index <= 40; index += 1) {
    const time = (index / 40) * clip.duration;
    evaluation.apply(resolveFrame(rig, evaluation, clip, time, { anchors }).pose);
    for (const lock of clip.locks) {
      const side = lock.chain.endsWith('_l') ? 'l' : 'r';
      const bone: BoneName = lock.chain.startsWith('arm') ? `hand_${side}` : `foot_${side}`;
      // A foot standing on its ball is held at the ball; its ankle rises.
      const position = lock.onBall ? evaluation.tail(bone, new Vector3()) : evaluation.head(bone, new Vector3());
      const first = start.get(lock.id);
      if (!first) start.set(lock.id, position.clone());
      else if (position.distanceTo(first) > worst) {
        worst = position.distanceTo(first);
        where = `${lock.id} at ${time.toFixed(2)}s`;
      }
    }
  }
  return {
    id: 'lockDrift',
    label: 'Locked contacts stay put',
    status: worst < 0.005 ? 'pass' : 'fail',
    detail: `Worst drift ${mm(worst)}${where ? ` (${where})` : ''}; limit 5 mm.`,
    measured: worst,
  };
}

/** Floor-locked feet flat and pointing where they started, at 81 samples. */
function feetFlat(rig: Skeleton, exercise: ExerciseDefinition, clip: StudioClip): CandidateCheck {
  const sides = (['l', 'r'] as const).filter((side) =>
    exercise.locks.some((lock) => lock.chain === `leg_${side}` && lock.mode === 'floor'),
  );
  if (sides.length === 0) {
    return { id: 'feetFlat', label: 'Feet flat and square', status: 'pass', detail: 'No floor-locked feet.', measured: 0 };
  }
  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  const first = new Map<string, { toe: number; direction: Vector3 }>();
  let toeTravel = 0;
  let swing = 0;
  for (let step = 0; step <= 80; step += 1) {
    const time = (step / 80) * clip.duration;
    evaluation.apply(resolveFrame(rig, evaluation, clip, time, { anchors }).pose);
    for (const side of sides) {
      const toe = evaluation.tail(`toe_${side}`, new Vector3()).y;
      const onBall = exercise.locks.some((lock) => lock.chain === `leg_${side}` && lock.onBall);
      const direction = new Vector3(0, 1, 0).applyQuaternion(evaluation.quaternion(onBall ? `toe_${side}` : `foot_${side}`));
      const start = first.get(side);
      if (!start) {
        first.set(side, { toe, direction });
        continue;
      }
      toeTravel = Math.max(toeTravel, Math.abs(toe - start.toe));
      swing = Math.max(swing, toDeg(direction.angleTo(start.direction)));
    }
  }
  const pass = toeTravel < 0.001 && swing < 0.25;
  return {
    id: 'feetFlat',
    label: 'Feet flat and square',
    status: pass ? 'pass' : 'fail',
    detail: `Toe height moves ${mm(toeTravel)} (limit 1 mm); feet turn ${swing.toFixed(2)}° (limit 0.25°).`,
    measured: toeTravel,
  };
}

function duration(exercise: ExerciseDefinition, clip: StudioClip): CandidateCheck {
  const expected = repetitionDuration(exercise);
  const pass = Math.abs(clip.duration - expected) < 1e-6;
  return {
    id: 'duration',
    label: 'Clip matches its tempo',
    status: pass ? 'pass' : 'fail',
    detail: `${clip.duration.toFixed(2)} s against ${expected.toFixed(2)} s from the tempo.`,
  };
}

function references(exercise: ExerciseDefinition): CandidateCheck {
  const ids = new Set(exercise.technique.map((rule) => rule.id));
  const dangling = exercise.commonErrors.filter((error) => error.ruleId && !ids.has(error.ruleId)).map((error) => error.id);
  const duplicate = ids.size !== exercise.technique.length;
  const pass = dangling.length === 0 && !duplicate && exercise.muscles.primary.length > 0;
  return {
    id: 'references',
    label: 'Rules, errors and muscles consistent',
    status: pass ? 'pass' : 'fail',
    detail: pass
      ? `${exercise.technique.length} rules, ${exercise.commonErrors.length} common errors, all references resolve.`
      : `${dangling.length ? `Errors name missing rules: ${dangling.join(', ')}. ` : ''}${duplicate ? 'Duplicate rule ids. ' : ''}`,
  };
}

/** The character-free checks, cheapest first. */
function rigChecks(ctx: ValidationContext, exercise: ExerciseDefinition, clip: StudioClip, want: (id: CheckId) => boolean) {
  const checks: CandidateCheck[] = [];
  if (['technique', 'loop', 'ik', 'contacts', 'grip', 'twoHandGrip'].some((id) => want(id as CheckId))) {
    // At the 20 samples a second the library's own technique test uses.
    const review = reviewExercise(ctx.rig, exercise, clip, 20);
    for (const gate of review.gates) {
      if (!want(gate.id)) continue;
      checks.push({
        id: gate.id,
        label: gate.label,
        status: gate.applicable === false ? 'pass' : gate.passed ? 'pass' : 'fail',
        detail: gate.detail,
      });
    }
  }
  if (want('jointLimits')) checks.push(jointLimits(ctx.rig, clip));
  if (want('lockDrift')) checks.push(lockDrift(ctx.rig, clip));
  if (want('feetFlat')) checks.push(feetFlat(ctx.rig, exercise, clip));
  if (want('duration')) checks.push(duration(exercise, clip));
  if (want('references')) checks.push(references(exercise));
  return checks;
}

/** Cached per character and reference: the library does not move during a session. */
const referenceSeparation = new WeakMap<CharacterBuild, Map<string, number>>();

function* bodyChecks(
  ctx: ValidationContext,
  clip: StudioClip,
  generateReference: (exercise: ExerciseDefinition) => StudioClip,
  want: (id: CheckId) => boolean,
): Generator<string, CandidateCheck[]> {
  const checks: CandidateCheck[] = [];
  const character = ctx.character;
  if (want('equipmentClearance')) {
    if (!character) {
      checks.push({
        id: 'equipmentClearance',
        label: 'Equipment clears the body',
        status: 'skipped',
        detail: 'No character loaded to measure against.',
      });
    } else {
      yield 'Measuring equipment against the body';
      const items = measureEquipmentClearance(character.build, ctx.rig, clip);
      const failing = items.filter((item) => !item.pass);
      const free = items.filter((item) => !item.support);
      const tightest = free.reduce((worst, item) => Math.min(worst, item.sample.closest), Number.POSITIVE_INFINITY);
      const describe = (item: (typeof items)[number]) =>
        item.support
          ? `${item.id}: ${item.parts
              .map((part) => `${part.material} ${mm(part.deepest)}${part.pass ? '' : ' ✗'}`)
              .join(', ')}`
          : `${item.id} ${mm(item.sample.closest)}${item.sample.inside ? `, ${item.sample.inside} inside` : ''} (${item.sample.where})`;
      checks.push({
        id: 'equipmentClearance',
        label: 'Equipment clears the body',
        status: items.length === 0 || failing.length === 0 ? 'pass' : 'fail',
        detail:
          items.length === 0
            ? 'No visible equipment.'
            : `${(failing.length ? failing : items).map(describe).join('; ')}. Limits: 2 mm off the legs and trunk; a pad reached within 3 mm and pressed no more than 15 mm.`,
        measured: Number.isFinite(tightest) ? tightest : undefined,
      });
    }
  }

  if (want('armTrunk')) {
    if (!character) {
      checks.push({ id: 'armTrunk', label: 'Arms clear the trunk', status: 'skipped', detail: 'No character loaded to measure against.' });
    } else if (!ctx.reference) {
      checks.push({ id: 'armTrunk', label: 'Arms clear the trunk', status: 'skipped', detail: 'No reference exercise to compare with.' });
    } else {
      const cache = referenceSeparation.get(character.build) ?? new Map<string, number>();
      referenceSeparation.set(character.build, cache);
      let reference = cache.get(ctx.reference.id);
      if (reference === undefined) {
        yield `Measuring the reference ${ctx.reference.id}`;
        reference = measureArmTrunkSeparation(character.build, ctx.rig, generateReference(ctx.reference)).closest;
        cache.set(ctx.reference.id, reference);
      }
      yield 'Measuring the arms against the trunk';
      const measured = measureArmTrunkSeparation(character.build, ctx.rig, clip);
      const pass = measured.closest > 0 && measured.closest > reference - ARM_TRUNK_SLACK;
      checks.push({
        id: 'armTrunk',
        label: 'Arms clear the trunk',
        status: pass ? 'pass' : 'fail',
        detail:
          `Closest ${Number.isFinite(measured.closest) ? mm(measured.closest) : 'beyond the search'} (${measured.where || 'none within 240 mm'}) ` +
          `against ${mm(reference)} for the reference ${ctx.reference.id}, which it may come within 1 mm of.`,
        measured: measured.closest,
      });
    }
  }
  return checks;
}

/**
 * The validation as a sequence of steps, each yielding what it is about to
 * measure, so a caller can hand control back between the slow ones.
 */
export function* validationSteps(
  ctx: ValidationContext,
  exercise: ExerciseDefinition,
  clip: StudioClip,
  generateReference: (exercise: ExerciseDefinition) => StudioClip,
): Generator<string, CandidateReport> {
  const want = (id: CheckId) => !ctx.only || ctx.only.includes(id);
  yield 'Checking technique, joints, contacts and feet';
  const rig = rigChecks(ctx, exercise, clip, want);
  const body = yield* bodyChecks(ctx, clip, generateReference, want);
  const checks = [...rig, ...body];
  const failed = checks.filter((check) => check.status === 'fail').map((check) => check.id);
  const skipped = checks.filter((check) => check.status === 'skipped').map((check) => check.id);
  return {
    checks,
    passed: failed.length === 0 && skipped.length === 0,
    failed,
    skipped,
    character: ctx.character?.label ?? null,
  };
}

export function validateCandidate(
  ctx: ValidationContext,
  exercise: ExerciseDefinition,
  clip: StudioClip,
  generateReference: (exercise: ExerciseDefinition) => StudioClip,
): CandidateReport {
  const steps = validationSteps(ctx, exercise, clip, generateReference);
  for (;;) {
    const step = steps.next();
    if (step.done) return step.value;
  }
}
