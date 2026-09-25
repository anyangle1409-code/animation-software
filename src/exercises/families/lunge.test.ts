import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { EXERCISES } from '../library';
import { splitSquat } from '../definitions/splitSquat';
import { forwardLunge } from '../definitions/forwardLunge';
import { reverseLunge } from '../definitions/reverseLunge';
import { existsSync, readFileSync } from 'node:fs';
import type { SkinnedMesh } from 'three';
import { applyCharacterPose } from '../../character/pose';
import { retargetedCharacterSource } from '../../character/retargetSource';
import { dominantBone, posedVertex } from '../../character/posedMesh';

/**
 * The lunge family: a split stance, the two legs doing different things. The
 * front foot is flat; the back foot stands on its ball with the heel rising and
 * falling as the back knee drops, which is the new contact this family needed.
 */
const rig = canonicalSkeleton;
const deg = (radians: number | undefined) => ((radians ?? 0) * 180) / Math.PI;
const evaluation = new PoseEvaluation(rig);
const clip = generateClip(rig, splitSquat);
const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);

function at(time: number) {
  const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
  evaluation.apply(frame.pose);
  const heel = evaluation.head('foot_r', new Vector3());
  const ball = evaluation.tail('foot_r', new Vector3());
  return {
    pose: frame.pose,
    ball,
    toeTip: evaluation.tail('toe_r', new Vector3()),
    toe: new Vector3(0, 1, 0).applyQuaternion(evaluation.quaternion('toe_r')),
    /** How far the back foot is pitched up off the floor, degrees. */
    heel: (Math.asin((heel.y - ball.y) / heel.distanceTo(ball)) * 180) / Math.PI,
    backKnee: evaluation.head('shin_r', new Vector3()),
    frontKnee: evaluation.head('shin_l', new Vector3()),
    frontAnkle: evaluation.head('foot_l', new Vector3()),
  };
}
const bottom = splitSquat.tempo.eccentric + splitSquat.tempo.pauseStretched / 2;

describe('the lunge family', () => {
  it('pivots the back foot on its ball: the ball and toes stay put while the heel rises', () => {
    const first = at(0);
    const heels: number[] = [];
    for (let step = 0; step <= 40; step += 1) {
      const frame = at((step / 40) * clip.duration);
      expect(frame.ball.distanceTo(first.ball), `ball at step ${step}`).toBeLessThan(0.001);
      expect(Math.abs(frame.toeTip.y - first.toeTip.y), `toe tip at step ${step}`).toBeLessThan(0.001);
      expect((frame.toe.angleTo(first.toe) * 180) / Math.PI, `toes at step ${step}`).toBeLessThan(0.25);
      // The ankle holds its 25°.
      expect(Math.abs(deg(frame.pose.rotations.foot_r?.x) - 25), `ankle at step ${step}`).toBeLessThan(0.5);
      heels.push(frame.heel);
    }
    // And the heel does move: that is what the ball contact is for.
    expect(Math.max(...heels) - Math.min(...heels)).toBeGreaterThan(15);
  });

  it('reaches depth with the front knee over the front foot', () => {
    const frame = at(bottom);
    expect(frame.backKnee.y).toBeLessThan(0.12);
    expect(Math.abs(frame.frontKnee.x - frame.frontAnkle.x)).toBeLessThan(0.02);
    expect(frame.frontKnee.z - frame.frontAnkle.z).toBeLessThan(0.05);
  });

  it('authors leg angles that agree with what the solver produces', () => {
    for (const [time, key] of [[0, 'start'], [bottom, 'peak']] as const) {
      const rotations = at(time).pose.rotations;
      for (const target of splitSquat.jointTargets) {
        const solved = deg(rotations[target.bone]?.[target.axis]);
        expect(Math.abs(solved - target[key]), `${target.bone} ${key}: solved ${solved.toFixed(1)}`).toBeLessThan(1.5);
      }
    }
  });

  it('has three registered variants', () => {
    // A foot held on its ball at a fixed ankle is a lunge's back foot, by a lock
    // or, where it steps, by its keyframe; the calf raise's feet are on their
    // balls too, but hold the knee instead.
    const backFoot = (exercise: (typeof EXERCISES)[number]) =>
      exercise.locks.some((lock) => lock.onBall?.ankle !== undefined) ||
      [exercise.startPose, exercise.peakPose].some((pose) => pose.ik?.leg_r?.onBall);
    expect(EXERCISES.filter(backFoot).map((exercise) => exercise.id)).toEqual(['split_squat', 'forward_lunge', 'reverse_lunge']);
  });
});

describe('forward lunge', () => {
  const evaluation = new PoseEvaluation(rig);
  const clip = generateClip(rig, forwardLunge);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  const step = clip.keyframes[1].time;
  const drive = { start: clip.keyframes[2].time, end: clip.keyframes[3].time };
  const all = Array.from({ length: 201 }, (_, index) => {
    const time = (index / 200) * clip.duration;
    const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
    evaluation.apply(frame.pose);
    return {
      time,
      frame,
      ankle: evaluation.head('foot_l', new Vector3()),
      frontToe: evaluation.tail('toe_l', new Vector3()),
      backBall: evaluation.tail('foot_r', new Vector3()),
      backHeel: evaluation.head('foot_r', new Vector3()),
      backKnee: evaluation.head('shin_r', new Vector3()),
    };
  });

  it('solves every frame: both legs reach', () => {
    for (const { frame, time } of all) {
      for (const result of frame.ikResults) expect(result.error, `${result.chain} at ${time.toFixed(2)}s`).toBeLessThan(0.002);
    }
  });

  it('steps the front foot forward 94 cm through the air and lands it flat', () => {
    const start = all[0].ankle;
    const bottom = all.find((entry) => entry.frame.phaseId === 'bottom')!.ankle;
    expect(bottom.z - start.z).toBeCloseTo(0.94, 4);
    // Up to 7 cm off the floor on the way, never through it.
    const highest = Math.max(...all.map((entry) => entry.ankle.y));
    expect(highest).toBeGreaterThan(0.08 + 0.065);
    expect(highest).toBeLessThan(0.08 + 0.071);
    for (const { ankle, frontToe } of all) {
      expect(ankle.y).toBeGreaterThan(0.08 - 1e-9);
      // Flat the whole way: the toe tip as far below the ankle as standing puts it.
      expect(ankle.y - frontToe.y).toBeCloseTo(0.06, 3);
    }
  });

  it('plants the front foot for the last 35% of the step and the first 35% of the push', () => {
    const landed = all.find((entry) => entry.frame.phaseId === 'bottom')!.ankle;
    const planted = all.filter(
      ({ time }) =>
        (time >= step * 0.66 && time <= step) ||
        (time >= drive.start && time <= drive.start + (drive.end - drive.start) * 0.34),
    );
    expect(planted.length).toBeGreaterThan(20);
    for (const { ankle } of planted) expect(ankle.distanceTo(landed)).toBeLessThan(0.0005);
  });

  it('keeps the back foot on its ball, flat at standing and heel up at the bottom', () => {
    for (const { backBall } of all) expect(backBall.distanceTo(all[0].backBall)).toBeLessThan(0.0005);
    expect(all[0].backHeel.y).toBeCloseTo(0.08, 3);
    const bottom = all.find((entry) => entry.frame.phaseId === 'bottom')!;
    expect(bottom.backHeel.y).toBeGreaterThan(0.16);
    // The back knee 9 cm off the floor, as the split squat's is.
    expect(bottom.backKnee.y).toBeLessThan(0.1);
  });

  it('reports the stepping foot to a character as a floor contact, lifted while it swings', () => {
    const swinging = all.find(({ ankle }) => ankle.y > 0.14)!;
    const contact = swinging.frame.contacts.find((entry) => entry.chain === 'leg_l')!;
    expect(contact.mode).toBe('floor');
    expect(contact.lift).toBeCloseTo(swinging.ankle.y - 0.08, 6);
    const planted = all[0].frame.contacts.find((entry) => entry.chain === 'leg_l')!;
    expect(planted.lift).toBe(0);
    // The back foot's contact names its ankle, not the ball it pivots on.
    const bottom = all.find((entry) => entry.frame.phaseId === 'bottom')!;
    const back = bottom.frame.contacts.find((entry) => entry.chain === 'leg_r')!;
    expect(new Vector3(back.target.x, back.target.y, back.target.z).distanceTo(bottom.backHeel)).toBeLessThan(1e-9);
  });
});

describe('reverse lunge', () => {
  const evaluation = new PoseEvaluation(rig);
  const clip = generateClip(rig, reverseLunge);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  const step = clip.keyframes[1].time;
  const drive = { start: clip.keyframes[2].time, end: clip.keyframes[3].time };
  const all = Array.from({ length: 201 }, (_, index) => {
    const time = (index / 200) * clip.duration;
    const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
    evaluation.apply(frame.pose);
    return {
      time,
      frame,
      front: evaluation.head('foot_l', new Vector3()),
      backAnkle: evaluation.head('foot_r', new Vector3()),
      backBall: evaluation.tail('foot_r', new Vector3()),
      backToe: evaluation.tail('toe_r', new Vector3()),
      backKnee: evaluation.head('shin_r', new Vector3()),
    };
  });
  const bottom = all.find((entry) => entry.frame.phaseId === 'bottom')!;

  it('solves every frame: both legs reach', () => {
    for (const { frame, time } of all) {
      for (const result of frame.ikResults) expect(result.error, `${result.chain} at ${time.toFixed(2)}s`).toBeLessThan(0.002);
    }
  });

  it('keeps the front foot where it stands', () => {
    for (const { front } of all) expect(front.distanceTo(all[0].front)).toBeLessThan(0.0005);
  });

  it('steps the back foot 94 cm back onto its ball and holds it there, toes flat', () => {
    expect(all[0].backBall.z - bottom.backBall.z).toBeCloseTo(0.94, 4);
    const planted = all.filter(
      ({ time }) =>
        (time >= step * 0.76 && time <= step) ||
        (time >= drive.start && time <= drive.start + (drive.end - drive.start) * 0.24),
    );
    expect(planted.length).toBeGreaterThan(20);
    for (const { backBall, backToe } of planted) {
      expect(backBall.distanceTo(bottom.backBall)).toBeLessThan(0.0005);
      expect(backBall.y).toBeCloseTo(0.025, 4);
      expect(backToe.y).toBeCloseTo(0.02, 4);
    }
    // Heel up at the bottom, flat at standing; the back knee 9 cm off the floor.
    expect(bottom.backAnkle.y).toBeGreaterThan(0.16);
    expect(all[0].backAnkle.y).toBeCloseTo(0.08, 3);
    expect(bottom.backKnee.y).toBeLessThan(0.1);
  });

  it('lifts the stepping foot clear on the way and never through the floor', () => {
    for (const { backBall, backToe } of all) {
      expect(backBall.y).toBeGreaterThan(0.025 - 0.0005);
      expect(backToe.y).toBeGreaterThan(0.02 - 0.0005);
    }
    expect(Math.max(...all.map(({ backBall }) => backBall.y))).toBeGreaterThan(0.025 + 0.04);
  });

  it('reports the stepping foot to a character by its ankle, lifted by its ball', () => {
    const landed = bottom.frame.contacts.find((entry) => entry.chain === 'leg_r')!;
    expect(new Vector3(landed.target.x, landed.target.y, landed.target.z).distanceTo(bottom.backAnkle)).toBeLessThan(1e-9);
    expect(landed.lift).toBe(0);
    const swinging = all.find(({ backBall }) => backBall.y > 0.06)!;
    const contact = swinging.frame.contacts.find((entry) => entry.chain === 'leg_r')!;
    expect(contact.lift).toBeCloseTo(swinging.backBall.y - 0.025, 3);
  });
});

const ASSET =
  process.env.REAL_CHARACTER_GLB ?? 'review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb';

/**
 * How far a planted sole may sit off the floor: the character contact solve's
 * residual. Measured: 0.24 mm on the split squat, 1.62 mm on the forward lunge.
 */
const SOLE = 0.002;

describe.skipIf(!existsSync(ASSET))('feet on the production character', () => {
  it.each([splitSquat, forwardLunge, reverseLunge].map((exercise) => [exercise.id, exercise] as const))(
    '%s: each planted sole rests on the floor, and each ankle is where the rig puts it',
    async (_id, exercise) => {
      const bytes = readFileSync(ASSET);
      const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
      const character = await retargetedCharacterSource({ id: ASSET, label: ASSET, data }).build(rig);
      const body = (character.meshes as SkinnedMesh[]).find((mesh) => /freeman/i.test(mesh.name))!;
      const count = body.geometry.getAttribute('position').count;
      const sides = { l: [] as number[], r: [] as number[] };
      for (let index = 0; index < count; index += 1) {
        const bone = dominantBone(body, index);
        // The production skeleton's own names; its left is the rig's left.
        if (/^(foot|toe)L/.test(bone)) sides.l.push(index);
        if (/^(foot|toe)R/.test(bone)) sides.r.push(index);
      }
      const evaluation = new PoseEvaluation(rig);
      const clip = generateClip(rig, exercise);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const vertex = new Vector3();
      let worstSole = 0;
      const ankle = (side: 'L' | 'R') => {
        const position = body.skeleton.bones.find((bone) => bone.name === `DEF-foot${side}`)!.getWorldPosition(new Vector3());
        return position.setX(-position.x); // the character is the rig's mirror image
      };
      for (let index = 0; index <= 20; index += 1) {
        const time = (index / 20) * clip.duration;
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        evaluation.apply(frame.pose);
        applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
        body.skeleton.update();
        body.updateWorldMatrix(true, false);
        for (const contact of frame.contacts) {
          const side = contact.chain === 'leg_l' ? 'l' : 'r';
          let lowest = Infinity;
          for (const vertexIndex of sides[side]) lowest = Math.min(lowest, posedVertex(body, vertexIndex, vertex).y);
          const at = `${side} at ${time.toFixed(2)}s`;
          worstSole = Math.max(worstSole, Math.abs(lowest - (contact.lift ?? 0)));
          expect(Math.abs(lowest - (contact.lift ?? 0)), `sole, ${at}`).toBeLessThan(SOLE);
          const rigAnkle = evaluation.head(side === 'l' ? 'foot_l' : 'foot_r', new Vector3());
          const drawn = ankle(side === 'l' ? 'L' : 'R');
          expect(Math.hypot(drawn.x - rigAnkle.x, drawn.z - rigAnkle.z), `ankle, ${at}`).toBeLessThan(0.005);
        }
      }
      expect(worstSole).toBeLessThan(SOLE);
      character.dispose?.();
    },
    120_000,
  );
});
