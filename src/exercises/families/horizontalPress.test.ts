import { describe, expect, it } from 'vitest';
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
