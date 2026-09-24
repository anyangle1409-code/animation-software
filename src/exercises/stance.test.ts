import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton } from '../rig/skeleton';
import { ANKLE_HEIGHT, flatFootAim } from './stance';

/**
 * The flat foot a lock can pin is the rig's own resting foot, turned out.
 * Movements that open seated or bent over cannot take it from their first
 * frame, so it is written down; this holds it to the skeleton it came from.
 */
describe('a flat foot', () => {
  const rest = canonicalSkeleton.bone('foot_l');
  const vector = (value: { x: number; y: number; z: number }) => new Vector3(value.x, value.y, value.z);

  it('is the resting foot when not turned out', () => {
    const aim = flatFootAim(0);
    const direction = new Vector3(0, 1, 0).applyQuaternion(rest.restWorldQuaternion);
    const forward = new Vector3(0, 0, 1).applyQuaternion(rest.restWorldQuaternion);
    expect(vector(aim.direction).angleTo(direction)).toBeLessThan(1e-6);
    expect(vector(aim.forward).angleTo(forward)).toBeLessThan(1e-6);
    expect(rest.restHead.y).toBe(ANKLE_HEIGHT);
  });

  it('turns out about the vertical, towards the outside of the left foot', () => {
    const aim = flatFootAim(10);
    const flat = vector(aim.direction).setY(0);
    expect((Math.atan2(-flat.x, flat.z) * 180) / Math.PI).toBeCloseTo(10, 9);
    expect(aim.direction.y).toBeCloseTo(flatFootAim(0).direction.y, 12);
  });
});
