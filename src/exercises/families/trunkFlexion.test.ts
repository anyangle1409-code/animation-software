import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { applyCharacterPose } from '../../character/pose';
import { retargetedCharacterSource } from '../../character/retargetSource';
import { dominantBone, posedVertex } from '../../character/posedMesh';
import { EXERCISES } from '../library';
import { crunch } from '../definitions/crunch';
import { sitUp } from '../definitions/sitUp';
import type { ExerciseDefinition } from '../types';

/**
 * The trunk-flexion family: lying on the floor and curling up — the crunch
 * part of the way, the sit-up all the way to sitting.
 */
const rig = canonicalSkeleton;

function frames(exercise: ExerciseDefinition, steps = 40) {
  const evaluation = new PoseEvaluation(rig);
  const clip = generateClip(rig, exercise);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  return Array.from({ length: steps + 1 }, (_, step) => {
    const frame = resolveFrame(rig, evaluation, clip, (step / steps) * clip.duration, { anchors });
    evaluation.apply(frame.pose);
    const head = (bone: 'spine_01' | 'spine_02') => evaluation.head(bone, new Vector3());
    const angle = (bone: 'spine_01' | 'spine_02') =>
      (Math.acos(evaluation.tail(bone, new Vector3()).sub(head(bone)).normalize().y) * 180) / Math.PI;
    return {
      frame,
      pose: frame.pose,
      pelvis: evaluation.head('pelvis', new Vector3()),
      shoulder: evaluation.head('upperarm_l', new Vector3()),
      lowerBack: angle('spine_01'),
      midBack: angle('spine_02'),
    };
  });
}

describe('the trunk-flexion family', () => {
  it('has two registered variants', () => {
    const flexing = EXERCISES.filter((exercise) => exercise.technique.some((rule) => rule.id === 'neck_neutral'));
    expect(flexing.map((exercise) => exercise.id)).toEqual(['crunch', 'sit_up']);
  });

  it('keeps both feet reached on every frame', () => {
    for (const exercise of [crunch, sitUp]) {
      for (const { frame } of frames(exercise)) {
        for (const result of frame.ikResults) expect(result.error, exercise.id).toBeLessThan(0.002);
      }
    }
  });
});

describe('crunch', () => {
  const all = frames(crunch);
  const top = all.find(({ frame }) => frame.phaseId === 'top')!;

  it('lifts the shoulders 12 cm and more while the hips and lower back stay down', () => {
    expect(top.shoulder.y - all[0].shoulder.y).toBeGreaterThan(0.12);
    for (const { pelvis, lowerBack } of all) {
      expect(pelvis.distanceTo(all[0].pelvis)).toBeLessThan(1e-9);
      expect(lowerBack).toBeGreaterThan(75);
    }
  });
});

describe('sit-up', () => {
  const all = frames(sitUp);
  const top = all.find(({ frame }) => frame.phaseId === 'top')!;

  it('comes up to sitting, the mid back within 20° of upright', () => {
    expect(top.midBack).toBeLessThan(20);
    expect(all[0].midBack).toBeGreaterThan(80);
  });

  it('rolls onto the seat: the hip joint rises 1.4 cm and never leaves its line', () => {
    expect(top.pelvis.y - all[0].pelvis.y).toBeCloseTo(0.014, 6);
    for (const { pelvis } of all) expect(Math.abs(pelvis.z)).toBeLessThan(1e-9);
  });
});

const ASSET =
  process.env.REAL_CHARACTER_GLB ?? 'review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb';

/**
 * The floor held to a bench pad's bounds: what rests on it within 3 mm of it,
 * and pressed into it no further than flesh would flatten (15 mm).
 */
const PAD = { resting: 0.003, compression: 0.015 };

describe.skipIf(!existsSync(ASSET))('lying and sitting on the production character', () => {
  it.each([crunch, sitUp].map((exercise) => [exercise.id, exercise] as const))(
    '%s: back, seat and head rest on the floor at the start; nothing sinks through it',
    async (_id, exercise) => {
      const bytes = readFileSync(ASSET);
      const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
      const character = await retargetedCharacterSource({ id: ASSET, label: ASSET, data }).build(rig);
      const body = (character.meshes as SkinnedMesh[]).find((mesh) => /freeman/i.test(mesh.name))!;
      const count = body.geometry.getAttribute('position').count;
      // The trunk and head by the production skeleton's names: its spine chain
      // runs from the pelvis (`spine`) to the head (`spine.006`).
      const trunk = Array.from({ length: count }, (_, index) => /^(spine|pelvis|breast)/.test(dominantBone(body, index)));
      const head = Array.from({ length: count }, (_, index) => /^spine006/.test(dominantBone(body, index)));
      const evaluation = new PoseEvaluation(rig);
      const vertex = new Vector3();
      const sampled = frames(exercise, 16);
      let deepest = Infinity;
      sampled.forEach(({ pose, frame }, index) => {
        evaluation.apply(pose);
        applyCharacterPose(character, rig, pose, evaluation, { contacts: frame.contacts });
        body.skeleton.update();
        body.updateWorldMatrix(true, false);
        let lowest = Infinity;
        let lowestHead = Infinity;
        for (let vertexIndex = 0; vertexIndex < count; vertexIndex += 1) {
          if (!trunk[vertexIndex]) continue;
          const y = posedVertex(body, vertexIndex, vertex).y;
          lowest = Math.min(lowest, y);
          if (head[vertexIndex]) lowestHead = Math.min(lowestHead, y);
        }
        deepest = Math.min(deepest, lowest);
        if (index === 0) {
          expect(lowest, 'the back rests on the floor').toBeLessThanOrEqual(PAD.resting);
          expect(lowestHead, 'the head rests on the floor').toBeLessThanOrEqual(PAD.resting);
          expect(lowestHead, 'the head does not sink').toBeGreaterThanOrEqual(-PAD.compression);
        }
      });
      // Measured: the upper back 6.5 mm and the chest's sides 8.6 mm into the
      // floor lying; the sit-up's seat 11.4 mm mid-rise.
      expect(deepest).toBeGreaterThanOrEqual(-PAD.compression);
      character.dispose?.();
    },
    120_000,
  );
});
