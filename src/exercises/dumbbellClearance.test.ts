import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { applyCharacterPose } from '../character/pose';
import { retargetedCharacterSource } from '../character/retargetSource';
import { anatomicalGripOffset } from '../equipment/attach';
import { equipmentSocketForInstance } from '../equipment/library';
import { handAttachmentMatrix } from '../export/clipBuilder';
import { EXERCISES } from './library';

/**
 * Does the equipment go through the body?
 *
 * Nothing else in the suite asks. Technique rules, IK reachability, loop closure
 * and contact drift are all satisfiable by a repetition that drives a dumbbell
 * clean through the thigh, and that is not hypothetical — the hammer curl did
 * exactly that when it was first written, 16.92 mm deep with 82 vertices inside,
 * while reporting a clean bill of health on every existing gate.
 *
 * This is a narrow first instalment of the plan's Phase 5, not the whole of it:
 * one implement, one body, hand-held dumbbells only. The general contact and
 * collision framework is still to come. What it does cover is the case that
 * actually bit.
 *
 * ## What is measured, and what is deliberately not
 *
 * The dumbbell is an analytic envelope — a 15 mm handle 120 mm long, and two
 * 48 mm plates 35 mm thick at ±75 mm — rather than its render mesh, so the
 * measurement is a signed distance and reads the same at any sample rate.
 *
 * Only the legs and trunk are measured against it. The hand, fingers, forearm
 * and upper arm are excluded on purpose: a gripped handle is *supposed* to sink
 * into the palm, and treating that as a collision reports the grip working as a
 * fault. Including them produces exactly that — an identical, pose-independent
 * "penetration" for every exercise, which is how the exclusion was arrived at.
 *
 * The measurement runs against the production imported character, because that
 * is the body that ships. It skips rather than fails when the asset is absent,
 * so a checkout without `review-assets/` still runs the rest of the suite.
 */
const ASSET =
  process.env.REAL_CHARACTER_GLB ??
  'review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb';

const rig = canonicalSkeleton;
const mm = (metres: number) => `${(metres * 1000).toFixed(2)} mm`;

/** The dumbbell's own geometry, from `EQUIPMENT_PARTS.dumbbell`. */
const HANDLE_RADIUS = 0.015;
const HANDLE_HALF = 0.06;
const PLATE_RADIUS = 0.048;
const PLATE_HALF = 0.0175;
const PLATE_CENTRE = 0.075;

/** Signed distance from a point in the dumbbell's frame to its surface. */
const envelope = (point: Vector3): number => {
  const radial = Math.hypot(point.x, point.y);
  const along = Math.abs(point.z);
  return Math.min(
    Math.max(radial - HANDLE_RADIUS, along - HANDLE_HALF),
    Math.max(radial - PLATE_RADIUS, PLATE_CENTRE - PLATE_HALF - along, along - PLATE_CENTRE - PLATE_HALF),
  );
};

/**
 * A margin rather than a floor at zero. Zero would pass a repetition whose plate
 * grazes the shorts, which reads as a collision even when it technically is not;
 * the two curls measure 9.75 mm and 11.41 mm, so 2 mm sits well clear of both
 * while still failing anything that actually touches.
 */
const MARGIN = 0.002;

/** The surface the equipment must not reach: legs and trunk. */
const BODY = /^(thigh|pelvis|shin|spine|breast|neck)/i;

function posedPoint(mesh: SkinnedMesh, index: number, out: Vector3): Vector3 {
  const position = mesh.geometry.getAttribute('position');
  out.fromBufferAttribute(position, index);
  const morphs = mesh.geometry.morphAttributes.position ?? [];
  const influences = mesh.morphTargetInfluences ?? [];
  const relative = mesh.geometry.morphTargetsRelative === true;
  for (let slot = 0; slot < morphs.length; slot += 1) {
    const weight = influences[slot] ?? 0;
    if (!weight) continue;
    const morph = morphs[slot];
    out.x += (relative ? morph.getX(index) : morph.getX(index) - position.getX(index)) * weight;
    out.y += (relative ? morph.getY(index) : morph.getY(index) - position.getY(index)) * weight;
    out.z += (relative ? morph.getZ(index) : morph.getZ(index) - position.getZ(index)) * weight;
  }
  mesh.applyBoneTransform(index, out);
  return mesh.localToWorld(out);
}

function dominantBone(mesh: SkinnedMesh, index: number): string {
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  let best = -1;
  let bone = '';
  for (let lane = 0; lane < 4; lane += 1) {
    const weight = skinWeight.getComponent(index, lane);
    if (weight > best) {
      best = weight;
      bone = mesh.skeleton.bones[skinIndex.getComponent(index, lane)]?.name ?? '';
    }
  }
  return bone.replace(/^DEF-?/, '');
}

const held = EXERCISES.filter((exercise) =>
  exercise.equipment.instances.some(
    (instance) => instance.kind === 'dumbbell' && instance.attachment.mode === 'hand',
  ),
);

describe.skipIf(!existsSync(ASSET))('dumbbells clear the body', () => {
  it.each(held.map((exercise) => [exercise.name, exercise] as const))(
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
      const point = new Vector3();
      const local = new Vector3();

      let worst = Number.POSITIVE_INFINITY;
      let worstAt = '';
      let inside = 0;

      for (let step = 0; step <= 40; step += 1) {
        const time = (step / 40) * clip.duration;
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        body!.skeleton.update();
        body!.updateWorldMatrix(true, false);

        for (const instance of clip.equipment) {
          if (instance.kind !== 'dumbbell' || instance.attachment.mode !== 'hand') continue;
          const side = instance.attachment.side;
          const hand = character.handMatrix?.(side, new Matrix4());
          if (!hand) continue;
          const socket = equipmentSocketForInstance(instance, instance.attachment.socket);
          const offset =
            instance.attachment.gripOffset ?? character.gripOffset?.(side) ?? anatomicalGripOffset(side);
          const toDumbbell = new Matrix4()
            .multiplyMatrices(hand, handAttachmentMatrix(offset, socket?.position ?? { x: 0, y: 0, z: 0 }))
            .invert();

          for (let index = 0; index < count; index += 1) {
            if (!measured[index]) continue;
            posedPoint(body!, index, point);
            local.copy(point).applyMatrix4(toDumbbell);
            const gap = envelope(local);
            if (gap < 0) inside += 1;
            if (gap < worst) {
              worst = gap;
              worstAt = `${side} dumbbell at ${time.toFixed(2)}s, against ${dominantBone(body!, index)}`;
            }
          }
        }
      }
      character.dispose?.();

      const report = `${exercise.id}: closest ${mm(worst)} at ${worstAt}`;
      expect(inside, `${report} — ${inside} vertices inside the implement`).toBe(0);
      expect(worst, report).toBeGreaterThan(MARGIN);
    },
    120_000,
  );
});
