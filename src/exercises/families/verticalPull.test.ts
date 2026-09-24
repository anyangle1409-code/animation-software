import { describe, expect, it } from 'vitest';
import { verticalPullFamily } from './verticalPull';
import { pullUp } from '../definitions/pullUp';

/**
 * The vertical-pull family holds the accepted pull-up exactly. (That the whole
 * clip is byte-identical to the accepted one is proved by the definition-and-
 * frame comparison recorded in `docs/CHANGE_LOG_REVERT_POINTS.md`.)
 */
const identity = { id: 'x', name: 'X', clipName: 'x', description: 'x' };
const strip = ({ id: _id, name: _name, clipName: _clip, description: _description, ...rest }: typeof pullUp) => rest;

describe('the vertical-pull family', () => {
  it('carries the accepted pull-up: hands on the rack, the body hanging from them', () => {
    expect(pullUp.locks.map((lock) => [lock.mode, lock.equipmentId, lock.socket])).toEqual([
      ['equipment', 'rack', 'pullup_l'],
      ['equipment', 'rack', 'pullup_r'],
    ]);
  });

  it('builds the pull-up from nothing but its name', () => {
    expect(strip(verticalPullFamily(identity))).toEqual(strip(pullUp));
  });

  it('lets a variant change its tempo and nothing else', () => {
    const slow = verticalPullFamily({ ...identity, tempo: { eccentric: 4, pauseStretched: 1, concentric: 2, pauseContracted: 1 } });
    expect(slow.tempo.eccentric).toBe(4);
    expect({ ...strip(slow), tempo: null }).toEqual({ ...strip(pullUp), tempo: null });
  });
});
