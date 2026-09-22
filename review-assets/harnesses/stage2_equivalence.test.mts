import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { shoulderPress } from '../../src/exercises/definitions/shoulderPress';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';
import type { BoneName } from '../../src/rig/boneNames';

/**
 * Retarget equivalence between the Stage 1 and Stage 2 candidates.
 *
 * Stage 2 is meant to be Stage 1 with the shoulder moved outward and NOTHING
 * else. That is a checkable claim: drive both characters from the same
 * canonical poses and compare every mapped bone's world position. Bones off the
 * arm must not move at all, and bones on the arm must move by exactly the
 * intended lateral shift — no rotation, no droop, no change along the bone.
 *
 * The first attempt failed exactly here: translating the upper arm moved the
 * clavicle's tail while leaving its stored bind orientation behind, so the
 * retarget correction absorbed the difference and the arm swung out by
 * hundreds of millimetres. This is the test that would have caught it.
 */
const rig = canonicalSkeleton;
const SHIFT = 0.01924 * 1.75; // metres per side, studio scale

const load = async (path: string, id: string) => {
  const bytes = readFileSync(path);
  const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  return retargetedCharacterSource({ id, label: id, data }).build(rig);
};

const ARM = /^(clavicle|upperarm|forearm|hand|thumb|index|middle|ring|pinky)_(l|r)$|^(thumb|index|middle|ring|pinky)_0[123]_(l|r)$/;

describe('stage 2 retarget equivalence', () => {
  it('poses identically to stage 1 apart from the intended shoulder shift', async () => {
    const one = await load('scratchpad/reference-fit/HomeGymPT_Male_STAGE1_CANDIDATE.glb', 'one');
    const two = await load('scratchpad/reference-fit/HomeGymPT_Male_STAGE2_CANDIDATE.glb', 'two');

    let worstOff = { bone: '', value: 0, at: '' };
    let worstArm = { bone: '', value: 0, at: '' };
    const scratch = new Vector3();

    for (const [exercise, label, times] of [
      [bicepCurl, 'curl', [0, 1, 2, 5.5]],
      [shoulderPress, 'press', [0, 2.35]],
    ] as [typeof bicepCurl, string, number[]][]) {
      const clip = generateClip(rig, exercise);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      for (const time of times) {
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        evaluation.apply(frame.pose);
        const context = {
          contacts: frame.contacts,
          grip: { kind: exercise.hands.grip, closure: exercise.hands.closure },
        };
        applyCharacterPose(one, rig, frame.pose, evaluation, context);
        applyCharacterPose(two, rig, frame.pose, evaluation, context);

        for (const rigBone of rig.bones) {
          const a = one.boneByName.get(rigBone.name as BoneName);
          const b = two.boneByName.get(rigBone.name as BoneName);
          if (!a || !b) continue;
          const pa = new Vector3().setFromMatrixPosition(a.matrixWorld);
          const pb = new Vector3().setFromMatrixPosition(b.matrixWorld);
          const arm = ARM.test(rigBone.name);
          if (arm && rigBone.name !== 'clavicle_l' && rigBone.name !== 'clavicle_r') {
            // Expected: a pure lateral shift, outboard on each side.
            const sign = rigBone.name.endsWith('_l') ? 1 : -1;
            const expected = scratch.set(sign * SHIFT, 0, 0);
            const error = pb.clone().sub(pa).sub(expected).length();
            if (error > worstArm.value) worstArm = { bone: rigBone.name, value: error, at: `${label} ${time}s` };
          } else if (!arm) {
            const moved = pa.distanceTo(pb);
            if (moved > worstOff.value) worstOff = { bone: rigBone.name, value: moved, at: `${label} ${time}s` };
          }
        }
      }
    }

    console.log(`EQUIV off-arm worst ${(worstOff.value * 1000).toFixed(4)} mm (${worstOff.bone} @ ${worstOff.at})`);
    console.log(`EQUIV arm deviation from a pure ${(SHIFT * 1000).toFixed(2)} mm shift: ` +
      `worst ${(worstArm.value * 1000).toFixed(4)} mm (${worstArm.bone} @ ${worstArm.at})`);

    expect(worstOff.value, 'a bone off the arm moved').toBeLessThan(1e-5);
    expect(worstArm.value, 'an arm bone did more than translate').toBeLessThan(5e-4);
  }, 300000);
});
