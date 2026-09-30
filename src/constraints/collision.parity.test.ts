import { describe, expect, it } from 'vitest';
import { HgMat4, HgQuat, HgVec3 } from '../core/linearMath';
import { equipmentParts } from '../equipment/geometry';
import type { Part } from '../equipment/geometry';
import type { EquipmentKind } from '../equipment/types';
import { equipmentDistance, equipmentPartDistances, measureClearance, PointGrid } from './collision';

function referencePartMatrix(part: Part): HgMat4 {
  const [px, py, pz] = part.position ?? [0, 0, 0];
  const rotation = 'rotation' in part && part.rotation
    ? new HgQuat().setFromEulerXYZ(...part.rotation)
    : new HgQuat();
  return new HgMat4()
    .compose(new HgVec3(px, py, pz), rotation, new HgVec3(1, 1, 1))
    .invert();
}

function referenceDistanceToPart(part: Part, point: HgVec3): number {
  switch (part.shape) {
    case 'cylinder': {
      const radius = Math.max(part.radius, part.radiusTop ?? part.radius);
      const radial = Math.hypot(point.x, point.z) - radius;
      const axial = Math.abs(point.y) - part.length / 2;
      return radial > 0 && axial > 0 ? Math.hypot(radial, axial) : Math.max(radial, axial);
    }
    case 'box': {
      const [sx, sy, sz] = part.size;
      const dx = Math.abs(point.x) - sx / 2;
      const dy = Math.abs(point.y) - sy / 2;
      const dz = Math.abs(point.z) - sz / 2;
      const outside = Math.hypot(Math.max(dx, 0), Math.max(dy, 0), Math.max(dz, 0));
      return outside > 0 ? outside : Math.max(dx, dy, dz);
    }
    case 'sphere':
      return point.length() - part.radius;
    case 'torus': {
      const ring = Math.hypot(point.x, point.z) - part.radius;
      return Math.hypot(ring, point.y) - part.tube;
    }
    default:
      return Number.POSITIVE_INFINITY;
  }
}

function referencePartDistances(kind: EquipmentKind, point: HgVec3, backAngle?: number): number[] {
  return equipmentParts(kind, backAngle).map((part) =>
    referenceDistanceToPart(part, point.clone().applyMatrix4(referencePartMatrix(part))),
  );
}

const POINTS = [
  new HgVec3(0, 0, 0),
  new HgVec3(0.04, 0.08, -0.11),
  new HgVec3(-0.23, 0.41, 0.37),
  new HgVec3(0.71, 1.13, -0.52),
];

const CASES: Array<{ kind: EquipmentKind; backAngle?: number }> = [
  { kind: 'dumbbell' },
  { kind: 'ez_curl_bar' },
  { kind: 'cable_handle' },
  { kind: 'incline_bench', backAngle: 45 },
  { kind: 'incline_bench', backAngle: 67 },
];

describe('first-party collision math', () => {
  it('matches an independent part-transform and signed-distance reference', () => {
    for (const { kind, backAngle } of CASES) {
      for (const point of POINTS) {
        const expected = referencePartDistances(kind, point, backAngle);
        const actual = equipmentPartDistances(kind, point, backAngle);
        expect(actual).toHaveLength(expected.length);
        for (let index = 0; index < expected.length; index += 1) {
          expect(Math.abs(actual[index] - expected[index]), `${kind} part ${index}`).toBeLessThan(1e-12);
        }
        expect(Math.abs(equipmentDistance(kind, point, backAngle) - Math.min(...expected))).toBeLessThan(1e-12);
      }
    }
  });

  it('keeps PointGrid compatible with caller-owned first-party vectors', () => {
    const points = [
      new HgVec3(0.01, 0.02, 0.03),
      new HgVec3(0.22, 0.01, -0.04),
      new HgVec3(-0.18, 0.07, 0.09),
    ];
    const grid = new PointGrid(0.1);
    points.forEach((point, index) => grid.add(index, point));
    const scratch = new HgVec3();
    const query = new HgVec3(0.19, 0.01, -0.03);
    const hit = grid.nearest(
      query,
      3,
      (index, out) => out.copy(points[index]),
      scratch,
    );
    expect(hit?.index).toBe(1);
    expect(hit?.distance).toBeCloseTo(query.distanceTo(points[1]), 12);
  });

  it('measures clearance with first-party placement and scratch vectors', () => {
    const toItem = new HgMat4()
      .compose(
        new HgVec3(0.2, -0.1, 0.3),
        new HgQuat().setFromEulerXYZ(0.2, -0.3, 0.15),
        new HgVec3(1, 1, 1),
      )
      .invert();
    const points = [
      new HgVec3(0.2, -0.1, 0.3),
      new HgVec3(0.27, -0.02, 0.18),
      new HgVec3(-0.1, 0.4, 0.6),
    ];
    const expected = points.map((point) => {
      const local = point.clone().applyMatrix4(toItem);
      return Math.min(...referencePartDistances('dumbbell', local));
    });
    const result = measureClearance(
      'dumbbell',
      toItem,
      points.length,
      (index, out) => out.copy(points[index]),
      (index) => String(index),
      undefined,
      undefined,
      new HgVec3(),
    );
    expect(result.closest).toBeCloseTo(Math.min(...expected), 12);
    expect(result.inside).toBe(expected.filter((distance) => distance < 0).length);
  });
});
