import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { EXERCISES } from './library';

/**
 * Feet that stand on the floor stay flat on it.
 *
 * Every technique rule about a planted foot measures a point — the ankle, or a
 * spot just behind it — and a foot can rotate about that point without moving
 * it. So the squat passed all of them while, as played, its toes dipped 41 mm
 * into the floor mid-descent and its feet swivelled 32°. This measures the foot
 * as a body instead: the toe tip's height and the foot's direction, through the
 * whole repetition, as the studio shows it (with the clip's contact anchors).
 *
 * It covers every exercise that stands on its feet: floor-locked legs, and at
 * the first frame the ankle at standing height with the toe tip on the floor.
 * That takes in a row that starts bent over and a press that sits, and leaves
 * out the push-up, which is up on its toes and pivots on them. The pull-up
 * hangs.
 *
 * ## The squat is a known defect, held to what it does now
 *
 * The squat's feet ride with its shins: the toes dip 41 mm below the floor and
 * the feet swivel 32°. Holding them flat (`plantedStance({ flat })`) is not a
 * fix on its own. The stance turns the feet out at the ankle, and the ankle's
 * "toe-out" actually turns them *in* (10° asked, 10.7° in); the leg solver
 * twists near-straight legs outward by far more, which is what the studio shows.
 * With the feet held, every knee pole tried — 60 of them, and toe-out from the
 * hip as well — left the knees 74-128 mm inside the line of the foot at the
 * bottom, against 46 mm now. That is knee cave, the fault a squat must not
 * show, so the fix waits for a stance model that turns the leg out from the hip
 * and sets the thigh's twist from the foot. Until then the squat is held to its
 * current numbers so it cannot get worse, and it leaves this list when fixed.
 */
const rig = canonicalSkeleton;

/**
 * Measured now: toe-tip height travel (metres), and the largest angle the foot
 * bone turns through from where it started (degrees). The 32° swivel above is
 * the same motion read off the footprint on the floor; the bone points 23°
 * downward, so its turn in 3D reads smaller.
 */
const KNOWN_DEFECTS: Record<string, { toe: number; direction: number }> = {
  air_squat: { toe: 0.0666, direction: 29.3 },
};

/** Flat on the floor at the first frame: ankle at standing height, toe tip down. */
function startsFlat(exercise: (typeof EXERCISES)[number]): boolean {
  const evaluation = new PoseEvaluation(rig);
  const clip = generateClip(rig, exercise);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  evaluation.apply(resolveFrame(rig, evaluation, clip, 0, { anchors }).pose);
  const ankle = evaluation.head('foot_l', new Vector3()).y;
  const toe = evaluation.tail('toe_l', new Vector3()).y;
  return Math.abs(ankle - 0.082) < 0.01 && toe < 0.03;
}

const standing = EXERCISES.filter(
  (exercise) =>
    exercise.locks.some((lock) => lock.mode === 'floor' && lock.chain.startsWith('leg')) && startsFlat(exercise),
);

describe('standing feet', () => {
  it('cover every exercise that stands', () => {
    expect(standing.map((exercise) => exercise.id).sort()).toEqual([
      'air_squat',
      'dumbbell_bent_over_row',
      'dumbbell_bicep_curl',
      'dumbbell_hammer_curl',
      'dumbbell_overhead_triceps_extension',
      'dumbbell_reverse_curl',
      'dumbbell_romanian_deadlift',
      'dumbbell_shoulder_press',
      'incline_dumbbell_curl',
      'seated_dumbbell_shoulder_press',
    ]);
  });

  it.each(standing.map((exercise) => [exercise.id, exercise] as const))(
    '%s keeps both feet flat and pointing where they started',
    (_id, exercise) => {
      const evaluation = new PoseEvaluation(rig);
      const clip = generateClip(rig, exercise);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const first = new Map<string, { toe: number; direction: Vector3 }>();
      const known = KNOWN_DEFECTS[exercise.id];
      let lowest = Infinity;
      let highest = -Infinity;
      let swing = 0;

      for (let step = 0; step <= 80; step += 1) {
        const time = (step / 80) * clip.duration;
        evaluation.apply(resolveFrame(rig, evaluation, clip, time, { anchors }).pose);
        for (const side of ['l', 'r'] as const) {
          const toe = evaluation.tail(`toe_${side}`, new Vector3()).y;
          const direction = new Vector3(0, 1, 0).applyQuaternion(evaluation.quaternion(`foot_${side}`));
          const start = first.get(side);
          if (!start) {
            first.set(side, { toe, direction });
            continue;
          }
          lowest = Math.min(lowest, toe - start.toe);
          highest = Math.max(highest, toe - start.toe);
          swing = Math.max(swing, (direction.angleTo(start.direction) * 180) / Math.PI);
          if (known) continue;
          const at = `${side} at ${time.toFixed(2)}s`;
          // Measured: 0.2 mm and 0.0° at worst across the library.
          expect(Math.abs(toe - start.toe), `toe height, ${at}`).toBeLessThan(0.001);
          expect((direction.angleTo(start.direction) * 180) / Math.PI, `foot direction, ${at}`).toBeLessThan(0.25);
        }
      }
      if (known) {
        expect(highest - Math.min(lowest, 0), 'toe travel against the known baseline').toBeLessThan(known.toe + 0.002);
        expect(swing, 'foot swing against the known baseline').toBeLessThan(known.direction + 1);
      }
    },
  );

  it('lists only defects that are still there', () => {
    for (const id of Object.keys(KNOWN_DEFECTS)) expect(standing.map((exercise) => exercise.id)).toContain(id);
  });
});
