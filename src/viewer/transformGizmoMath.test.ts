import { describe, expect, it } from 'vitest';
import { HgVec3 } from '../core/linearMath';
import {
  closestHgAxisParameter,
  hgAxisTranslationDelta,
  hgSignedRotationAngle,
  intersectHgRayPlane,
} from './transformGizmoMath';

const ray = (origin: HgVec3, direction: HgVec3) => ({ origin, direction });

describe('first-party transform gizmo drag math', () => {
  it('finds the closest position along a translation axis', () => {
    const value = closestHgAxisParameter(
      ray(new HgVec3(2, 1, 0), new HgVec3(0, -1, 0)),
      new HgVec3(0, 0, 0),
      new HgVec3(1, 0, 0),
    );
    expect(value).toBeCloseTo(2, 12);
  });

  it('measures an axis drag delta', () => {
    const delta = hgAxisTranslationDelta(
      ray(new HgVec3(1, 1, 0), new HgVec3(0, -1, 0)),
      ray(new HgVec3(3, 1, 0), new HgVec3(0, -1, 0)),
      new HgVec3(0, 0, 0),
      new HgVec3(1, 0, 0),
    );
    expect(delta).toBeCloseTo(2, 12);
  });

  it('intersects a pointer ray with a rotation plane', () => {
    const point = intersectHgRayPlane(
      ray(new HgVec3(1, 2, 5), new HgVec3(0, 0, -1)),
      new HgVec3(0, 0, 0),
      new HgVec3(0, 0, 1),
    );
    expect(point).not.toBeNull();
    expect(point?.x).toBeCloseTo(1, 12);
    expect(point?.y).toBeCloseTo(2, 12);
    expect(point?.z).toBeCloseTo(0, 12);
  });

  it('measures signed rotation with the right-hand rule', () => {
    const angle = hgSignedRotationAngle(
      ray(new HgVec3(1, 0, 5), new HgVec3(0, 0, -1)),
      ray(new HgVec3(0, 1, 5), new HgVec3(0, 0, -1)),
      new HgVec3(0, 0, 0),
      new HgVec3(0, 0, 1),
    );
    expect(angle).toBeCloseTo(Math.PI / 2, 12);
  });

  it('rejects degenerate parallel drag geometry', () => {
    const parameter = closestHgAxisParameter(
      ray(new HgVec3(0, 1, 0), new HgVec3(1, 0, 0)),
      new HgVec3(0, 0, 0),
      new HgVec3(1, 0, 0),
    );
    expect(parameter).toBeNull();

    const intersection = intersectHgRayPlane(
      ray(new HgVec3(0, 1, 0), new HgVec3(1, 0, 0)),
      new HgVec3(0, 0, 0),
      new HgVec3(0, 1, 0),
    );
    expect(intersection).toBeNull();
  });
});
