import { describe, expect, it } from 'vitest';
import { HgVec3 } from '../../core/linearMath';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { vec3 } from '../../rig/types';
import { horizontalPressFamily } from './horizontalPress';
import { pushUp } from '../definitions/pushUp';

/**
 * The horizontal-press family holds the accepted push-up exactly: its values
 * are the measured ones, and a variant changes only what it says it changes.
 * (That the whole clip is byte-identical to the accepted one is proved by the
 * definition-and-frame comparison recorded in `docs/CHANGE_LOG_REVERT_POINTS.md`.)
 */
const identity = { id: 'x', name: 'X', clipName: 'x', description: 'x' };
const strip = ({ id: _id, name: _name, clipName: _clip, description: _description, ...rest }: typeof pushUp) => rest;

describe('the horizontal-press family', () => {
  it('carries the accepted push-up values', () => {
    expect(pushUp.locks.map((lock) => lock.position)).toEqual([vec3(-0.3, 0.055, 1.295), vec3(0.3, 0.055, 1.295)]);
    expect(pushUp.startPose.root?.rotation?.x).toBe(75.59);
    expect(pushUp.peakPose.root?.rotation?.x).toBe(85.54);
  });

  it('keeps toe contact root-authored instead of adding a competing leg IK lock', () => {
    expect(pushUp.locks.map((lock) => lock.chain)).toEqual(['arm_l', 'arm_r']);
  });

  it('keeps the standard push-up palms explicitly flat to the floor', () => {
    for (const lock of pushUp.locks.filter((entry) => entry.id.startsWith('hand_'))) {
      expect(lock.aim).toEqual({
        direction: vec3(0, 0, 1),
        forward: vec3(lock.id.endsWith('_l') ? 1 : -1, 0, 0),
      });
    }
    expect(pushUp.hands).toMatchObject({
      grip: 'floor',
      orientation: 'pronated',
      closure: 0.05,
    });
  });

  it('keeps both resolved palms flat and every digit out of hyperextension through the repetition', () => {
    const clip = generateClip(canonicalSkeleton, pushUp);
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const worldUp = new HgVec3(0, 1, 0);

    for (const fraction of [0, 0.25, 0.5, 0.75, 1]) {
      const frame = resolveFrame(canonicalSkeleton, evaluation, clip, clip.duration * fraction);
      evaluation.apply(frame.pose);

      for (const side of ['l', 'r'] as const) {
        const turn = evaluation.firstPartyEvaluation.quaternion(`hand_${side}`);
        const handDirection = new HgVec3(0, 1, 0).applyQuaternion(turn).normalize();
        const handForward = new HgVec3(0, 0, 1).applyQuaternion(turn).normalize();
        const palmNormal = handDirection.clone().cross(handForward).normalize();

        // World Y is vertical. Both hand-plane axes must stay horizontal and
        // their normal must stay vertical, so the solved palm cannot roll onto
        // its side even if the wrist rotates within the floor plane.
        const degrees = (radians: number) => (radians * 180) / Math.PI;
        const forearm = frame.pose.rotations[`forearm_${side}`] ?? { x: 0, y: 0, z: 0 };
        const hand = frame.pose.rotations[`hand_${side}`] ?? { x: 0, y: 0, z: 0 };
        const diagnostic =
          `${fraction}/${side} ` +
          `dirY=${handDirection.dot(worldUp).toFixed(6)} ` +
          `fwdY=${handForward.dot(worldUp).toFixed(6)} ` +
          `normalY=${palmNormal.dot(worldUp).toFixed(6)} ` +
          `forearmY=${degrees(forearm.y).toFixed(2)}deg ` +
          `handX=${degrees(hand.x).toFixed(2)}deg handZ=${degrees(hand.z).toFixed(2)}deg`;

        expect(Math.abs(handDirection.dot(worldUp)), diagnostic).toBeLessThan(1e-3);
        expect(Math.abs(handForward.dot(worldUp)), diagnostic).toBeLessThan(1e-3);
        expect(Math.abs(palmNormal.dot(worldUp)), diagnostic).toBeGreaterThan(0.999);

        for (const finger of ['index', 'middle', 'ring', 'pinky'] as const) {
          for (const segment of ['01', '02', '03'] as const) {
            const raw = ((frame.pose.rotations[`${finger}_${segment}_${side}`]?.z ?? 0) * 180) / Math.PI;
            // Z is a handed local axis, so right-hand flexion has the opposite
            // sign. Convert it back to anatomical flexion before checking it.
            const flexion = side === 'l' ? raw : -raw;
            expect(flexion, `${fraction}/${finger}_${segment}_${side}`).toBeGreaterThanOrEqual(0);
            expect(flexion, `${fraction}/${finger}_${segment}_${side}`).toBeLessThan(1);
          }
        }

        for (const segment of ['01', '02', '03'] as const) {
          const angle = ((frame.pose.rotations[`thumb_${segment}_${side}`]?.z ?? 0) * 180) / Math.PI;
          expect(Math.abs(angle), `${fraction}/thumb_${segment}_${side}`).toBeLessThan(1);
        }
      }
    }
  });

  it('builds the push-up from nothing but its name', () => {
    expect(strip(horizontalPressFamily(identity))).toEqual(strip(pushUp));
  });

  it('lets a variant move only the hands', () => {
    const wide = horizontalPressFamily({ ...identity, hand: vec3(-0.4, 0.055, 1.295) });
    expect(wide.locks.map((lock) => lock.position)).toEqual([vec3(-0.4, 0.055, 1.295), vec3(0.4, 0.055, 1.295)]);
    const withoutHands = (definition: typeof pushUp) => ({
      ...strip(definition),
      locks: definition.locks.map(({ position: _position, ...lock }) => lock),
    });
    expect(withoutHands(wide)).toEqual(withoutHands(pushUp));
  });
});
