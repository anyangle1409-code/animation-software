import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { canonicalSkeleton } from '../rig/skeleton';
import { retargetedCharacterSource } from '../character/retargetSource';
import {
  ARM_TRUNK_SEARCH,
  ARM_TRUNK_SLACK as SLACK,
  bodyMeshOf,
  measureArmTrunkSeparation,
} from '../constraints/bodyClearance';
import { EXERCISES } from './library';

/**
 * How close does an arm come to the trunk it swings beside?
 *
 * ## What this can and cannot tell you — read before trusting a number
 *
 * It measures the **separation** between two sets of surface points. It cannot
 * tell contact from penetration: an arm resting on a chest and an arm buried in
 * one both approach zero from the outside, and a point cloud carries no notion
 * of inside.
 *
 * ## Why this is a regression guard and not a floor
 *
 * A fixed floor was the obvious design and the measurements killed it. An arm
 * hanging at the side genuinely rests against the chest: the squat measures
 * 1.36 mm, the press 1.95 mm and the pull-up 2.02 mm, all upper arm to breast,
 * with the curl at 4.66 mm, the hammer curl at 5.03 mm and the push-up at
 * 7.90 mm. Normal anatomy already sits inside any floor that would also catch a
 * real interpenetration, so a floor here does not separate good from bad — it
 * separates "arms by the sides" from "arms not by the sides".
 *
 * So each exercise is held against what it measures now. That catches the thing
 * worth catching — a change that pushes an arm into the chest it used to clear —
 * without inventing an absolute safe distance that the body itself does not
 * respect. It is the same shape as the shoulder-strain guard: record what the
 * library does, fail if a later change gives it back.
 *
 * Left and right agree to within 0.01 mm throughout, which is an independent
 * check on the mirroring: two separately measured point clouds landing on the
 * same number is not something a broken mirror would produce.
 */
const ASSET =
  process.env.REAL_CHARACTER_GLB ??
  'review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb';

const rig = canonicalSkeleton;
const mm = (metres: number) => `${(metres * 1000).toFixed(2)} mm`;

/**
 * What each exercise measures now, in metres, as the minimum over both sides.
 * Recorded from the production character; see the header for why these are
 * baselines rather than a shared floor.
 */
const BASELINE: Record<string, number> = {
  dumbbell_bicep_curl: 0.00466,
  dumbbell_hammer_curl: 0.00502,
  dumbbell_reverse_curl: 0.00259,
  push_up: 0.00789,
  air_squat: 0.00136,
  dumbbell_shoulder_press: 0.00195,
  pull_up: 0.00202,
  // Hanging arms resting on the sides of the chest mid-descent, like the squat.
  dumbbell_romanian_deadlift: 0.00117,
  // At the stretch, arms hanging beside the chest.
  dumbbell_bent_over_row: 0.00152,
  // The standing press's arms, sat down: the same 1.95 mm.
  seated_dumbbell_shoulder_press: 0.00195,
  // Arms hanging behind the body, near the chest at the top of the curl.
  incline_dumbbell_curl: 0.00179,
  // Arms overhead, the upper arm beside the top of the chest at lockout.
  dumbbell_overhead_triceps_extension: 0.0029,
  // Arms hanging at the sides through the split squat.
  split_squat: 0.00422,
  // Elbows tucked at the ribs, nearest the chest at lockout.
  cable_triceps_pushdown: 0.00464,
  // Arms hanging beside the chest at the bottom of the lateral raise.
  dumbbell_lateral_raise: 0.00414,
  // Arms passing the chest on the way down in the front raise.
  dumbbell_front_raise: 0.00112,
  // Arms hanging at the sides while the body rises onto the toes.
  standing_calf_raise: 0.0051,
  dumbbell_calf_raise: 0.00559,
  // The upper (left) arm crossing the chest to the clasped handle.
  cable_pallof_press: 0.00185,
  // Lying on the bench: the upper arm passing the side of the chest as the
  // press begins to lower, and beside the armpit with the fly's arms open.
  dumbbell_bench_press: 0.00863,
  dumbbell_fly: 0.01028,
  // Upper arms drawn in to clasp the hands, passing the side of the trunk as
  // it turns.
  russian_twist: 0.00184,
  // The tightest in the library: the right forearm passing the trunk as the
  // long arms swing the handle down across the body. Grazing, not inside.
  cable_woodchop: 0.00098,
  // The split squat's arms, hanging, through a step.
  forward_lunge: 0.00422,
  reverse_lunge: 0.00422,
  // Arms reaching towards the knees past the sides of the chest as the trunk
  // curls up.
  crunch: 0.00194,
  sit_up: 0.00159,
  // Arms hanging long at the sides, a dumbbell in each hand, through the walk.
  farmers_walk: 0.0057,
};
/**
 * The measurement and the 1 mm slack live in `constraints/bodyClearance.ts`,
 * so the generator's validation holds a candidate to exactly what this test
 * holds the library to.
 * The imported deform bones' side is captured explicitly there: the first
 * version of this check matched it with `endsWith('L')`, silently dropped every
 * numbered arm segment and measured 74 vertices of proximal forearm as "the
 * arm". The vertex-count assertions below are what made that visible.
 */
describe.skipIf(!existsSync(ASSET))('the arm clears the trunk', () => {
  it.each(EXERCISES.map((exercise) => [exercise.name, exercise] as const))(
    '%s',
    async (_name, exercise) => {
      const bytes = readFileSync(ASSET);
      const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
      const character = await retargetedCharacterSource({ id: ASSET, label: ASSET, data }).build(rig);
      expect(bodyMeshOf(character), 'the imported body mesh').toBeDefined();

      const measured = measureArmTrunkSeparation(character, rig, generateClip(rig, exercise));
      character.dispose?.();
      expect(measured.trunkVertices, 'trunk vertices').toBeGreaterThan(100);

      const reach = `beyond the ${mm(ARM_TRUNK_SEARCH)} search`;
      for (const side of measured.sides) {
        expect(side.armVertices, `${side.side} arm vertices`).toBeGreaterThan(100);
        console.log(
          `  ${exercise.id.padEnd(24)} ${side.side}  closest ` +
            `${(Number.isFinite(side.closest) ? mm(side.closest) : reach).padStart(10)}  (${side.where || reach})`,
        );
      }
      const overall = measured.closest;
      const overallWhere = measured.where;

      // Never coincident, whatever the baseline says. Two surfaces at exactly
      // zero are not touching, they are the same point.
      expect(overall, `${exercise.id}: ${overallWhere}`).toBeGreaterThan(0);

      const baseline = BASELINE[exercise.id];
      expect(baseline, `${exercise.id} has no recorded baseline — add one`).toBeDefined();
      expect(
        overall,
        `${exercise.id}: closest ${mm(overall)} against a ${mm(baseline)} baseline — ${overallWhere}`,
      ).toBeGreaterThan(baseline - SLACK);
    },
    180_000,
  );
});
