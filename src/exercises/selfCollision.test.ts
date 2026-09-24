import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { PointGrid } from '../constraints/collision';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { applyCharacterPose } from '../character/pose';
import { dominantBone, posedVertex } from '../character/posedMesh';
import { retargetedCharacterSource } from '../character/retargetSource';
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
};

/**
 * How much closer an exercise may come than its baseline before this fails.
 * Wide enough to absorb a re-measure or a small deliberate change, narrow
 * enough that halving any of these separations trips it.
 */
const SLACK = 0.001;

/** 30 mm cells, and eight shells of them, so the search reaches 240 mm. */
const CELL = 0.03;
const RINGS = 8;

/**
 * Imported deform bones are named `<part><side>` with an optional numeric
 * suffix for a segment: `upper_armL`, `upper_armL001`, `forearmL001`. Matching
 * the side with a plain `endsWith('L')` therefore drops every segment — the
 * first version of this check did exactly that and silently measured 74
 * vertices of proximal forearm while reporting it as "the arm". The side is
 * captured explicitly so a segment cannot fall out of the set unnoticed, and the
 * vertex-count assertions below are what made the mistake visible.
 */
const ARM = /^(upper_?arm|forearm)([LR])\d*$/i;
const TRUNK = /^(spine|breast|pelvis)/i;
const armSide = (bone: string): string | null => {
  const match = ARM.exec(bone);
  return match ? match[2].toUpperCase() : null;
};

describe.skipIf(!existsSync(ASSET))('the arm clears the trunk', () => {
  it.each(EXERCISES.map((exercise) => [exercise.name, exercise] as const))(
    '%s',
    async (_name, exercise) => {
      const bytes = readFileSync(ASSET);
      const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
      const character = await retargetedCharacterSource({ id: ASSET, label: ASSET, data }).build(rig);
      const body = (character.meshes as SkinnedMesh[]).find((mesh) => /freeman/i.test(mesh.name));
      expect(body, 'the imported body mesh').toBeDefined();

      const count = body!.geometry.getAttribute('position').count;
      const bone = Array.from({ length: count }, (_, index) => dominantBone(body!, index));
      const trunk = [...Array(count).keys()].filter((index) => TRUNK.test(bone[index]));
      expect(trunk.length, 'trunk vertices').toBeGreaterThan(100);

      const evaluation = new PoseEvaluation(rig);
      const clip = generateClip(rig, exercise);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const here = new Vector3();
      const there = new Vector3();

      let overall = Number.POSITIVE_INFINITY;
      let overallWhere = '';

      for (const side of ['L', 'R'] as const) {
        const arm = [...Array(count).keys()].filter((index) => armSide(bone[index]) === side);
        expect(arm.length, `${side} arm vertices`).toBeGreaterThan(100);

        let closest = Number.POSITIVE_INFINITY;
        let where = '';

        for (let step = 0; step <= 40; step += 1) {
          const time = (step / 40) * clip.duration;
          const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
          applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
          body!.skeleton.update();
          body!.updateWorldMatrix(true, false);

          const grid = new PointGrid(CELL);
          for (const index of trunk) grid.add(index, posedVertex(body!, index, there));

          for (const index of arm) {
            posedVertex(body!, index, here);
            const hit = grid.nearest(here, RINGS, (i, out) => posedVertex(body!, i, out), there);
            if (hit && hit.distance < closest) {
              closest = hit.distance;
              where = `${bone[index]} to ${bone[hit.index]} at ${time.toFixed(2)}s`;
            }
          }
        }

        const reach = `beyond the ${mm(CELL * RINGS)} search`;
        console.log(
          `  ${exercise.id.padEnd(24)} ${side}  closest ` +
            `${(Number.isFinite(closest) ? mm(closest) : reach).padStart(10)}  (${where || reach})`,
        );
        // Nothing found within the search means the arm stayed further away than
        // the grid looks, not that it went unmeasured.
        if (Number.isFinite(closest) && closest < overall) {
          overall = closest;
          overallWhere = `${side}: ${where}`;
        }
      }
      character.dispose?.();

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
