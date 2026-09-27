import { describe, expect, it } from 'vitest';
import { HgQuat, HgVec3 } from '../core/linearMath';
import { HgTransformDrag } from './transformGizmoInteraction';

const ray = (origin: HgVec3, direction = new HgVec3(0, -1, 0)) => ({
  origin,
  direction,
});

describe('first-party transform gizmo interaction', () => {
  it('translates from the original position along the selected world axis', () => {
    const drag = new HgTransformDrag(
      'translate',
      new HgVec3(1, 0, 0),
      ray(new HgVec3(1, 2, 0)),
      new HgVec3(4, 5, 6),
      new HgQuat(),
    );
    const result = drag.update(ray(new HgVec3(3.5, 2, 0)));
    expect(result?.position).toEqual(new HgVec3(6.5, 5, 6));
    expect(result?.quaternion).toEqual(new HgQuat());
  });

  it('rotates from the original orientation around the selected world axis', () => {
    const drag = new HgTransformDrag(
      'rotate',
      new HgVec3(0, 0, 1),
      { origin: new HgVec3(1, 0, 5), direction: new HgVec3(0, 0, -1) },
      new HgVec3(),
      new HgQuat(),
    );
    const result = drag.update({
      origin: new HgVec3(0, 1, 5),
      direction: new HgVec3(0, 0, -1),
    });
    expect(result?.quaternion.z).toBeCloseTo(Math.SQRT1_2, 12);
    expect(result?.quaternion.w).toBeCloseTo(Math.SQRT1_2, 12);
    expect(result?.position).toEqual(new HgVec3());
  });

  it('returns null for a degenerate drag instead of corrupting the object', () => {
    const drag = new HgTransformDrag(
      'translate',
      new HgVec3(1, 0, 0),
      { origin: new HgVec3(), direction: new HgVec3(1, 0, 0) },
      new HgVec3(),
      new HgQuat(),
    );
    expect(drag.update({
      origin: new HgVec3(0, 1, 0),
      direction: new HgVec3(1, 0, 0),
    })).toBeNull();
  });
});
