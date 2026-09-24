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
import { russianTwist } from '../definitions/russianTwist';

/**
 * The rotation family: the trunk turning over hips that stay put.
 */
const rig = canonicalSkeleton;
const R = Math.PI / 180;

function frames(steps = 40) {
  const evaluation = new PoseEvaluation(rig);
  const clip = generateClip(rig, russianTwist);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  return Array.from({ length: steps + 1 }, (_, step) => {
    const time = (step / steps) * clip.duration;
    const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
    evaluation.apply(frame.pose);
    return {
      time,
      pose: frame.pose,
      phase: frame.phaseId,
      pelvis: evaluation.head('pelvis', new Vector3()),
      hands: {
        l: evaluation.head('hand_l', new Vector3()).lerp(evaluation.tail('hand_l', new Vector3()), 0.5),
        r: evaluation.head('hand_r', new Vector3()).lerp(evaluation.tail('hand_r', new Vector3()), 0.5),
      },
      twist: (['spine_01', 'spine_02', 'spine_03'] as const).reduce(
        (total, bone) => total + (frame.pose.rotations[bone]?.y ?? 0) / R,
        0,
      ),
    };
  });
}

describe('the rotation family', () => {
  it('has one registered variant', () => {
    const turning = EXERCISES.filter(
      (exercise) => exercise.category === 'core' && exercise.technique.some((rule) => rule.id.startsWith('full_turn_')),
    );
    expect(turning.map((exercise) => exercise.id)).toEqual(['russian_twist']);
  });
});

describe('Russian twist', () => {
  const all = frames();

  it('turns the trunk 50° each way, and the hips not at all', () => {
    const twists = all.map((frame) => frame.twist);
    expect(Math.min(...twists)).toBeCloseTo(-50, 6);
    expect(Math.max(...twists)).toBeCloseTo(50, 6);
    for (const frame of all) {
      expect(frame.pose.rotations.pelvis?.y ?? 0).toBe(0);
      expect(frame.pelvis.distanceTo(all[0].pelvis)).toBeLessThan(1e-9);
    }
  });

  it('takes the hands to the left, then the right, past the thighs', () => {
    const left = all.find((frame) => frame.phase === 'left')!;
    const right = all.find((frame) => frame.phase === 'right')!;
    // Mirror images of each other.
    expect(left.hands.l.x).toBeCloseTo(-right.hands.r.x, 9);
    expect(left.hands.l.y).toBeCloseTo(right.hands.r.y, 9);
    expect(left.hands.l.z).toBeCloseTo(right.hands.r.z, 9);
    // Beside the thigh, not in front of the knee (knees 14 cm out).
    expect(left.hands.l.x).toBeLessThan(-0.25);
  });

  it('keeps the hands clasped the whole way', () => {
    for (const frame of all) expect(frame.hands.l.distanceTo(frame.hands.r)).toBeLessThan(0.05);
  });
});

const ASSET =
  process.env.REAL_CHARACTER_GLB ?? 'review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb';

describe.skipIf(!existsSync(ASSET))('Russian twist on the production character', () => {
  it('sits on the floor: resting on it, not hovering or sinking', async () => {
    const bytes = readFileSync(ASSET);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: ASSET, label: ASSET, data }).build(rig);
    const body = (character.meshes as SkinnedMesh[]).find((mesh) => /freeman/i.test(mesh.name))!;
    const count = body.geometry.getAttribute('position').count;
    // The seat: buttocks and the backs of the thighs.
    const seat = Array.from({ length: count }, (_, index) => /^(spine|pelvis|thigh)[LR]?$/.test(dominantBone(body, index)));
    const evaluation = new PoseEvaluation(rig);
    let lowest = Infinity;
    const vertex = new Vector3();
    for (const frame of frames(8)) {
      evaluation.apply(frame.pose);
      applyCharacterPose(character, rig, frame.pose, evaluation);
      body.skeleton.update();
      body.updateWorldMatrix(true, false);
      for (let index = 0; index < count; index += 1) {
        if (seat[index]) lowest = Math.min(lowest, posedVertex(body, index, vertex).y);
      }
    }
    character.dispose?.();
    // The same bounds as a bench pad: within 3 mm of the floor, and pressed
    // into it no further than flesh would flatten (measured 8.0 mm).
    expect(lowest).toBeLessThanOrEqual(0.003);
    expect(lowest).toBeGreaterThanOrEqual(-0.015);
  }, 60_000);
});
