import { describe, expect, it } from 'vitest';
import { HgVec3 } from '../core/linearMath';
import { HgOrbitModel } from './orbitModel';

function expectVec(actual: HgVec3, expected: HgVec3, epsilon = 1e-10) {
  expect(Math.abs(actual.x - expected.x)).toBeLessThan(epsilon);
  expect(Math.abs(actual.y - expected.y)).toBeLessThan(epsilon);
  expect(Math.abs(actual.z - expected.z)).toBeLessThan(epsilon);
}

describe('first-party orbit model', () => {
  it('round-trips the initial camera placement', () => {
    const position = new HgVec3(2.3, 1.35, 2.7);
    const target = new HgVec3(0, 1.02, 0);
    const orbit = new HgOrbitModel(position, target);
    expectVec(orbit.snapshot().position, position);
    expectVec(orbit.snapshot().target, target);
  });

  it('clamps zoom to the configured distance envelope', () => {
    const orbit = new HgOrbitModel(
      new HgVec3(0, 1, 3),
      new HgVec3(0, 1, 0),
      { minDistance: 0.6, maxDistance: 12, damping: 1 },
    );
    orbit.zoomByFactor(100).step(1 / 60);
    expect(orbit.snapshot().distance).toBe(12);
    orbit.zoomByFactor(0.0001).step(1 / 60);
    expect(orbit.snapshot().distance).toBeCloseTo(0.6, 12);
  });

  it('clamps vertical rotation away from the singular poles', () => {
    const orbit = new HgOrbitModel(
      new HgVec3(0, 1, 3),
      new HgVec3(0, 1, 0),
      { minPolarAngle: 0.1, maxPolarAngle: Math.PI - 0.1, damping: 1 },
    );
    orbit.rotatePixels(0, 100000, 1000).step(1 / 60);
    expect(orbit.snapshot().polar).toBeCloseTo(0.1, 12);
    orbit.rotatePixels(0, -100000, 1000).step(1 / 60);
    expect(orbit.snapshot().polar).toBeCloseTo(Math.PI - 0.1, 12);
  });

  it('uses frame-rate-independent damping with the current 0.12 feel at 60 Hz', () => {
    const orbit = new HgOrbitModel(
      new HgVec3(0, 1, 3),
      new HgVec3(0, 1, 0),
      { damping: 0.12 },
    );
    orbit.zoomByFactor(2);
    const before = orbit.snapshot().distance;
    const goal = orbit.goal().distance;
    const after = orbit.step(1 / 60).distance;
    expect(after).toBeCloseTo(before + (goal - before) * 0.12, 12);
  });

  it('moves the orbit centre without inventing camera drift', () => {
    const orbit = new HgOrbitModel(
      new HgVec3(0, 1, 3),
      new HgVec3(0, 1, 0),
      { damping: 1 },
    );
    orbit.setTarget(new HgVec3(1, 2, 3));
    expectVec(orbit.snapshot().position, new HgVec3(1, 2, 6));
  });
});
