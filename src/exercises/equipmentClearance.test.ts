import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import {
  bodyMeshOf,
  EQUIPMENT_MARGIN as MARGIN,
  measureEquipmentClearance,
  SUPPORT_LIMITS as SUPPORT,
} from '../constraints/bodyClearance';
import { canonicalSkeleton } from '../rig/skeleton';
import { retargetedCharacterSource } from '../character/retargetSource';
import { EXERCISES } from './library';

/**
 * Does any equipment go through the body?
 *
 * Nothing in the technique-rule vocabulary can ask this, and the gap is not
 * hypothetical: the hammer curl drove a dumbbell 16.92 mm into the thigh, 82
 * vertices inside, while technique rules, IK reachability, loop closure and
 * contact drift all reported it clean.
 *
 * The envelope is derived from `EQUIPMENT_PARTS` by `constraints/collision.ts`,
 * the same description the viewport and the GLB exporter build from, so the
 * shape being measured is the shape being drawn. That is what lets this cover
 * every item rather than only the dumbbell it started with — a rack is measured
 * from its own parts with no new code.
 *
 * ## What is measured, and what is deliberately not
 *
 * Only the legs and trunk are measured. Hands, fingers, forearms and upper arms
 * are excluded on purpose: a gripped handle is *supposed* to sink into the palm,
 * and a hanging body is supposed to touch the bar it hangs from. Treating either
 * as a collision reports the grip working as a fault — measured, including them
 * produces an identical, pose-independent "penetration" for every exercise,
 * which is how the exclusion was arrived at rather than assumed.
 *
 * So this answers one question well: does the implement pass through the torso
 * or the legs. Body-against-body — an arm crossing a chest — is a different
 * measurement with a different notion of acceptable, since real bodies touch,
 * and it is not claimed here.
 *
 * It runs against the production imported character, and skips rather than fails
 * when that asset is absent so a checkout without `review-assets/` still runs
 * the rest of the suite.
 */
const ASSET =
  process.env.REAL_CHARACTER_GLB ??
  'review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb';

const rig = canonicalSkeleton;
const mm = (metres: number) => `${(metres * 1000).toFixed(2)} mm`;

/*
 * The limits — a 2 mm margin off the body for anything that is not a support,
 * and for a pad the body rests on, reached within 3 mm and pressed no more than
 * 15 mm in — and the measurement itself live in `constraints/bodyClearance.ts`,
 * with their reasons, so the generator's validation holds a candidate to exactly
 * what this test holds the library to. The measured surface is the legs and
 * trunk (`CLEARANCE_BODY`).
 */

const armed = EXERCISES.filter((exercise) =>
  exercise.equipment.instances.some((instance) => instance.visible),
);

describe.skipIf(!existsSync(ASSET))('equipment clears the body', () => {
  it.each(armed.map((exercise) => [exercise.name, exercise] as const))(
    '%s',
    async (_name, exercise) => {
      const bytes = readFileSync(ASSET);
      const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
      const character = await retargetedCharacterSource({ id: ASSET, label: ASSET, data }).build(rig);
      expect(bodyMeshOf(character), 'the imported body mesh').toBeDefined();

      const items = measureEquipmentClearance(character, rig, generateClip(rig, exercise));
      character.dispose?.();

      expect(items.length, 'equipment measured').toBeGreaterThan(0);
      // Printed whichever way it goes, in the plan's report shape: a number that
      // is only seen when it fails is a number nobody knows the value of.
      for (const { id, sample, support, pass } of items) {
        console.log(
          `  ${pass ? 'PASS' : 'FAIL'}  ` +
            `${exercise.id.padEnd(24)} ${id.padEnd(12)} ${support ? 'deepest' : 'closest'} ` +
            `${mm(sample.closest).padStart(10)}  inside ${sample.inside}  (${sample.where})`,
        );
      }
      for (const { id, sample, support, parts } of items) {
        const report = `${exercise.id} / ${id}: closest ${mm(sample.closest)} at ${sample.where}`;
        if (support) {
          parts.forEach((part, index) => {
            const at = `${exercise.id} / ${id} part ${index}: ${mm(part.deepest)} at ${part.where}`;
            console.log(`        ${part.material.padEnd(6)} ${at}`);
            if (part.material === 'pad') {
              expect(part.deepest, `${at} — the body does not reach this pad`).toBeLessThanOrEqual(SUPPORT.resting);
              expect(part.deepest, `${at} — the body sinks into this pad`).toBeGreaterThanOrEqual(-SUPPORT.compression);
            } else {
              expect(part.deepest, `${at} — the body touches the frame`).toBeGreaterThan(MARGIN);
            }
          });
          continue;
        }
        expect(sample.inside, `${report} — ${sample.inside} body vertices inside`).toBe(0);
        expect(sample.closest, report).toBeGreaterThan(MARGIN);
      }
    },
    180_000,
  );
});
