import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { equipmentPartDistances, measureClearance } from '../constraints/collision';
import { EQUIPMENT_PARTS } from '../equipment/geometry';
import type { ClearanceSample } from '../constraints/collision';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { applyCharacterPose } from '../character/pose';
import { retargetedCharacterSource } from '../character/retargetSource';
import { anatomicalGripOffset } from '../equipment/attach';
import { equipmentSocketForInstance } from '../equipment/library';
import { handAttachmentMatrix } from '../export/clipBuilder';
import { dominantBone, posedVertex } from '../character/posedMesh';
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

/**
 * A margin rather than a floor at zero, because zero passes a plate that grazes
 * the shorts, which reads as a collision even when it technically is not. The
 * tightest items in the library are the curls' dumbbells at 11.46 mm and
 * 11.68 mm, so 2 mm sits well clear of both while still failing anything that
 * actually touches. (Those read 9.75 and 11.41 before the envelope was derived
 * from EQUIPMENT_PARTS; the measurement got more accurate at plate rim corners,
 * the exercises did not move.)
 */
const MARGIN = 0.002;

/**
 * Equipment the body rests on — a bench it sits or lies on — is asked the
 * opposite question, pad by pad. Each padded part must be *reached*: a seat the
 * body hovers above is not being sat on, and a backrest the back hangs off is
 * not being leant on, so each pad's deepest point may be no more than 3 mm
 * clear. And each may be pressed into, because the flesh of a seated thigh and
 * buttock flattens under the whole upper body, but only by as much as that
 * flesh would: a skinned mesh does not flatten, so its surface passes into the
 * pad where the real one would spread, and 15 mm is held as the most that can
 * pass for compression rather than sinking. The frame is not padding, and keeps
 * the same 2 mm margin as any other equipment.
 */
const SUPPORT = { resting: 0.003, compression: 0.015 };

/** The surface equipment must not reach: legs and trunk. */
const BODY = /^(thigh|pelvis|shin|spine|breast|neck)/i;


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
      const body = (character.meshes as SkinnedMesh[]).find((mesh) => /freeman/i.test(mesh.name));
      expect(body, 'the imported body mesh').toBeDefined();

      const count = body!.geometry.getAttribute('position').count;
      const measured = Array.from({ length: count }, (_, index) => BODY.test(dominantBone(body!, index)));

      const evaluation = new PoseEvaluation(rig);
      const clip = generateClip(rig, exercise);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);

      const worst = new Map<string, ClearanceSample>();
      const placement = new Matrix4();
      /** Per support, per part: deepest point, and where. */
      const parts = new Map<string, { deepest: number; where: string }[]>();
      const local = new Vector3();

      for (let step = 0; step <= 40; step += 1) {
        const time = (step / 40) * clip.duration;
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        body!.skeleton.update();
        body!.updateWorldMatrix(true, false);

        for (const instance of clip.equipment) {
          if (!instance.visible) continue;

          if (instance.attachment.mode === 'hand') {
            // Rigid in the hand: the item's frame follows the character's own
            // grip, not the canonical rig's.
            const side = instance.attachment.side;
            const hand = character.handMatrix?.(side, new Matrix4());
            if (!hand) continue;
            const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
            const offset =
              instance.attachment.gripOffset ?? character.gripOffset?.(side) ?? anatomicalGripOffset(side);
            placement
              .multiplyMatrices(hand, handAttachmentMatrix(offset, socket?.position ?? { x: 0, y: 0, z: 0 }))
              .invert();
          } else {
            const transform = frame.equipment.get(instance.id);
            if (!transform) continue;
            placement
              .compose(
                new Vector3(transform.position.x, transform.position.y, transform.position.z),
                transform.quaternion,
                new Vector3(1, 1, 1),
              )
              .invert();
          }

          if (instance.supportsBody) {
            const record =
              parts.get(instance.id) ??
              EQUIPMENT_PARTS[instance.kind].map(() => ({ deepest: Number.POSITIVE_INFINITY, where: '' }));
            for (let index = 0; index < count; index += 1) {
              if (!measured[index]) continue;
              posedVertex(body!, index, local).applyMatrix4(placement);
              equipmentPartDistances(instance.kind, local).forEach((distance, part) => {
                if (distance < record[part].deepest) {
                  record[part] = { deepest: distance, where: `${time.toFixed(2)}s, ${dominantBone(body!, index)}` };
                }
              });
            }
            parts.set(instance.id, record);
          }

          const sample =
            worst.get(instance.id) ?? { closest: Number.POSITIVE_INFINITY, inside: 0, where: '' };
          measureClearance(
            instance.kind,
            placement,
            count,
            (index, out) => (measured[index] ? posedVertex(body!, index, out) : null),
            (index) => `${instance.id} at ${time.toFixed(2)}s, against ${dominantBone(body!, index)}`,
            sample,
          );
          worst.set(instance.id, sample);
        }
      }
      character.dispose?.();

      expect(worst.size, 'equipment measured').toBeGreaterThan(0);
      // Printed whichever way it goes, in the plan's report shape: a number that
      // is only seen when it fails is a number nobody knows the value of.
      const supports = new Set(clip.equipment.filter((instance) => instance.supportsBody).map((instance) => instance.id));
      for (const [id, sample] of worst) {
        const pass = supports.has(id)
          ? sample.closest <= SUPPORT.resting && sample.closest >= -SUPPORT.compression
          : sample.inside === 0 && sample.closest > MARGIN;
        console.log(
          `  ${pass ? 'PASS' : 'FAIL'}  ` +
            `${exercise.id.padEnd(24)} ${id.padEnd(12)} ${supports.has(id) ? 'deepest' : 'closest'} ` +
            `${mm(sample.closest).padStart(10)}  inside ${sample.inside}  (${sample.where})`,
        );
      }
      for (const [id, sample] of worst) {
        const report = `${exercise.id} / ${id}: closest ${mm(sample.closest)} at ${sample.where}`;
        if (supports.has(id)) {
          const kind = clip.equipment.find((instance) => instance.id === id)!.kind;
          parts.get(id)!.forEach((part, index) => {
            const at = `${exercise.id} / ${id} part ${index}: ${mm(part.deepest)} at ${part.where}`;
            console.log(`        ${EQUIPMENT_PARTS[kind][index].material.padEnd(6)} ${at}`);
            if (EQUIPMENT_PARTS[kind][index].material === 'pad') {
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
