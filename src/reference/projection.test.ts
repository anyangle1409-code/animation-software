import { describe, expect, it } from 'vitest';
import { evaluateProjectedEnvelope, projectWorldPoint, projectedDistance } from './projection';

const camera = {
  position: { x: 0, y: 0, z: 5 },
  target: { x: 0, y: 0, z: 0 },
  fov: 50,
  aspect: 1,
};

describe('projected landmark QA', () => {
  it('projects the camera target to image centre', () => {
    const point = projectWorldPoint({ x: 0, y: 0, z: 0 }, camera);
    expect(point.x).toBeCloseTo(0.5, 8);
    expect(point.y).toBeCloseTo(0.5, 8);
    expect(point.inFrame).toBe(true);
  });

  it('keeps projected coordinates resolution-independent', () => {
    const left = projectWorldPoint({ x: -0.5, y: 0.3, z: 0 }, camera);
    const right = projectWorldPoint({ x: 0.5, y: 0.3, z: 0 }, camera);
    expect(left.x).toBeLessThan(0.5);
    expect(right.x).toBeGreaterThan(0.5);
    expect(left.y).toBeCloseTo(right.y, 8);
  });

  it('reports explainable corridor failures', () => {
    const pass = evaluateProjectedEnvelope(
      { x: 0, y: 0, z: 0 },
      camera,
      { x: { min: 0.45, max: 0.55 }, y: { min: 0.45, max: 0.55 } },
    );
    expect(pass.passed).toBe(true);

    const fail = evaluateProjectedEnvelope(
      { x: 1, y: 0, z: 0 },
      camera,
      { x: { min: 0.45, max: 0.55 } },
    );
    expect(fail.passed).toBe(false);
    expect(fail.excess).toBeGreaterThan(0);
    expect(fail.detail).toMatch(/outside the allowed corridor/);
  });

  it('compares candidate and reference landmarks in normalized image units', () => {
    const a = projectWorldPoint({ x: 0, y: 0, z: 0 }, camera);
    const b = projectWorldPoint({ x: 0.2, y: 0, z: 0 }, camera);
    expect(projectedDistance(a, a)).toBe(0);
    expect(projectedDistance(a, b)).toBeGreaterThan(0);
  });
});
